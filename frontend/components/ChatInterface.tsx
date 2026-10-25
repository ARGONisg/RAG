"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, PanelLeft, FileText, Sun, Moon, Square, ArrowDown } from "lucide-react";
import { Message, Citation } from "@/types";
import { ChatMessage } from "./ChatMessage";
import { EmptyState } from "./EmptyState";
import { FileUpload } from "./FileUpload";
import { CitationDrawer } from "./CitationDrawer";
import { Sidebar } from "./Sidebar";

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [currentDoc, setCurrentDoc] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [showScrollDown, setShowScrollDown] = useState(false);

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    if (scrollHeight - scrollTop - clientHeight > 100) {
      setShowScrollDown(true);
    } else {
      setShowScrollDown(false);
    }
  };

  useEffect(() => {
    if (!showScrollDown) {
      scrollToBottom();
    }
  }, [messages]);

  useEffect(() => {
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
    if (document.documentElement.classList.contains('dark')) {
      setTheme('dark');
    } else {
      setTheme('light');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleUploadSuccess = (filename: string, chunksIndexed: number) => {
    setCurrentDoc(filename);
    setShowUpload(false);
    // Optional: Add a system message about successful upload
  };

  const startNewChat = () => {
    stopGeneration();
    setMessages([]);
    setSessionId(crypto.randomUUID());
    setActiveCitation(null);
  };

  const handleRegenerate = (messageToRegenerate: Message) => {
    const index = messages.findIndex(m => m.id === messageToRegenerate.id);
    if (index > 0) {
      const prevMessage = messages[index - 1];
      if (prevMessage.role === 'user') {
        setMessages(prev => prev.slice(0, index));
        sendMessage(prevMessage.content);
      }
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input);
      }
    };

    useEffect(() => {
      const handleGlobalKeyDown = (e: KeyboardEvent) => {
        if (e.ctrlKey && e.key.toLowerCase() === 'b') {
          e.preventDefault();
          setIsSidebarOpen(prev => !prev);
        }
        if (e.key === 'Escape' && activeCitation) {
          e.preventDefault();
          setActiveCitation(null);
        }
      };
      window.addEventListener('keydown', handleGlobalKeyDown);
      return () => window.removeEventListener('keydown', handleGlobalKeyDown);
    }, [activeCitation]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setIsLoading(true);

    const assistantMessageId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: assistantMessageId, role: "assistant", content: "", citations: [] },
    ]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const history = messages.map(({ role, content }) => ({ role, content }));
      
      const response = await fetch("http://localhost:8000/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          query: text,
          session_id: sessionId,
          history,
        }),
      });

      if (!response.ok) throw new Error("Chat request failed");
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body stream");

      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n").filter((line) => line.trim() !== "");
          
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.substring(6);
              if (dataStr === "[DONE]") {
                setIsLoading(false);
                break;
              }
              
              try {
                const data = JSON.parse(dataStr);
                if (data.type === "token") {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, content: msg.content + data.content }
                        : msg
                    )
                  );
                } else if (data.type === "citations") {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, citations: data.sources }
                        : msg
                    )
                  );
                }
              } catch (e) {
                console.error("Error parsing SSE data", e, dataStr);
              }
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return;
      console.error(error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: "DOCrag couldn't connect to the server.\n\nPlease make sure the backend is running and try again." }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex h-screen bg-background text-text-primary overflow-hidden">
      {/* Mobile Sidebar Backdrop */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-20 md:hidden" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <Sidebar 
        onNewChat={() => {
          startNewChat();
          if (window.innerWidth < 768) setIsSidebarOpen(false);
        }} 
        isOpen={isSidebarOpen}
      />

      <div className="flex-1 flex flex-col min-w-0 relative">
        <header className="h-16 flex items-center justify-between px-6 border-b border-border-subtle shrink-0">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
              className="p-2 -ml-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-02 transition-colors"
              aria-label="Toggle sidebar"
            >
              <PanelLeft size={20} />
            </button>
            <button 
              onClick={toggleTheme} 
              className="p-2 -ml-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-02 transition-colors"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <h2 className="text-lg font-semibold md:hidden">DOCrag</h2>
            {currentDoc && (
              <div className="flex items-center gap-2 text-sm text-text-primary bg-surface-02 border border-border-subtle px-3 py-1.5 rounded-full max-w-[200px] md:max-w-[400px] transition-all">
                <FileText size={14} className="shrink-0 text-text-secondary" />
                <span className="truncate">{currentDoc}</span>
                <span className="text-green-500 text-xs font-medium shrink-0 flex items-center gap-1 border-l border-border-subtle pl-2 ml-1">✓ Ready</span>
              </div>
            )}
          </div>
        </header>

        <main 
          className="flex-1 overflow-y-auto relative bg-background" 
          onScroll={handleScroll}
          onDragOver={(e) => {
            e.preventDefault();
            if (!showUpload) setShowUpload(true);
          }}
        >
          {showUpload ? (
            <div className="absolute inset-0 z-10 bg-background/95 backdrop-blur-sm flex items-center justify-center p-4">
              <FileUpload 
                onUploadSuccess={handleUploadSuccess} 
                onCancel={() => setShowUpload(false)} 
              />
            </div>
          ) : messages.length === 0 ? (
            <EmptyState 
              hasDocument={!!currentDoc} 
              onUploadClick={() => setShowUpload(true)} 
              onExampleClick={(text) => sendMessage(text)} 
            />
          ) : (
            <div className="max-w-4xl mx-auto w-full px-4 py-6 md:px-8 pb-32">
              {messages.map((message, idx) => (
                <ChatMessage 
                  key={message.id} 
                  message={message} 
                  onCitationClick={setActiveCitation} 
                  onRegenerate={handleRegenerate}
                  isStreaming={isLoading && idx === messages.length - 1}
                />
              ))}
              {isLoading && messages[messages.length - 1]?.role === "user" && (
                <div className="py-6 flex justify-start">
                  <div className="flex items-center gap-2 text-text-secondary">
                    <Loader2 className="animate-spin" size={16} />
                    <span className="text-sm font-medium">Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </main>

        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background via-background to-transparent pt-10 pb-6 px-4 md:px-8">
          {showScrollDown && (
            <div className="absolute -top-12 left-1/2 -translate-x-1/2">
              <button 
                onClick={() => { setShowScrollDown(false); scrollToBottom(); }}
                className="flex items-center gap-1.5 bg-surface-03/90 hover:bg-surface-03 text-text-primary border border-border-subtle backdrop-blur-sm px-3 py-1.5 rounded-full text-xs font-medium shadow-lg transition-all"
              >
                <ArrowDown size={14} />
                Latest
              </button>
            </div>
          )}
          <div className="max-w-4xl mx-auto w-full relative">
            {currentDoc && (
              <div className="flex items-center gap-1.5 text-xs text-text-muted mb-2 px-1">
                <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                Answering from your document
              </div>
            )}
            <div className="bg-surface-02 border border-border-subtle hover:border-border-active focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 rounded-2xl flex items-end p-1.5 transition-all shadow-sm">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  adjustTextareaHeight();
                }}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about your document..."
                className="w-full max-h-[200px] bg-transparent border-none focus:outline-none resize-none px-3 py-2.5 text-text-primary placeholder:text-text-muted disabled:opacity-50"
                rows={1}
                disabled={isLoading}
              />
              {isLoading ? (
                <button
                  onClick={stopGeneration}
                  className="mb-0.5 mr-0.5 p-2.5 bg-surface-03 text-text-primary rounded-xl hover:bg-border-subtle transition-colors shrink-0 flex items-center justify-center"
                  title="Stop generating"
                >
                  <Square size={18} fill="currentColor" />
                </button>
              ) : (
                <button
                  onClick={() => sendMessage(input)}
                  disabled={!input.trim()}
                  className="mb-0.5 mr-0.5 p-2.5 bg-primary text-white rounded-xl disabled:bg-transparent disabled:text-text-muted hover:bg-primary-hover transition-colors shrink-0"
                >
                  <Send size={18} />
                </button>
              )}
            </div>
            <p className="text-center text-xs text-text-muted mt-2">
              DOCrag can make mistakes. Verify important information with your sources.
            </p>
          </div>
        </div>
      </div>

      {activeCitation && (
        <CitationDrawer 
          citation={activeCitation} 
          onClose={() => setActiveCitation(null)} 
        />
      )}
    </div>
  );
}
