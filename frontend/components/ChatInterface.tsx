"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, PanelLeft, FileText, Sun, Moon, Square, ArrowDown } from "lucide-react";
import { Message, Citation, ChatSession } from "@/types";
import { ChatMessage } from "./ChatMessage";
import { EmptyState } from "./EmptyState";
import { FileUpload } from "./FileUpload";
import { CitationDrawer } from "./CitationDrawer";
import { Sidebar } from "./Sidebar";

export function ChatInterface() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionCounter, setSessionCounter] = useState<number>(1);
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [currentDoc, setCurrentDoc] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [showScrollDown, setShowScrollDown] = useState(false);

  // Load chat sessions from localStorage on mount
  useEffect(() => {
    try {
      const savedSessions = localStorage.getItem("docrag_chat_sessions");
      const savedCounter = localStorage.getItem("docrag_chat_counter");
      if (savedCounter) {
        setSessionCounter(parseInt(savedCounter, 10) || 1);
      }
      if (savedSessions) {
        const parsed: ChatSession[] = JSON.parse(savedSessions);
        if (parsed.length > 0) {
          setSessions(parsed);
          setSessionId(parsed[0].id);
          setMessages(parsed[0].messages || []);
          setCurrentDoc(parsed[0].currentDoc || null);
          return;
        }
      }
    } catch (err) {
      console.error("Failed to load chat sessions from localStorage", err);
    }
  }, []);

  // Save chat sessions to localStorage
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem("docrag_chat_sessions", JSON.stringify(sessions));
    } else {
      localStorage.removeItem("docrag_chat_sessions");
    }
  }, [sessions]);

  // Save counter to localStorage
  useEffect(() => {
    localStorage.setItem("docrag_chat_counter", sessionCounter.toString());
  }, [sessionCounter]);

  // Sync messages & currentDoc to active session in sessions list
  useEffect(() => {
    if (messages.length > 0) {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId ? { ...s, messages, currentDoc } : s
        )
      );
    }
  }, [messages, currentDoc, sessionId]);

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
    setSessions((prev) =>
      prev.map((s) => (s.id === sessionId ? { ...s, currentDoc: filename } : s))
    );
  };

  const startNewChat = () => {
    stopGeneration();
    setSessionId(crypto.randomUUID());
    setMessages([]);
    setActiveCitation(null);
  };

  const handleSelectSession = (id: string) => {
    if (id === sessionId) return;
    stopGeneration();
    const target = sessions.find((s) => s.id === id);
    if (target) {
      setSessionId(target.id);
      setMessages(target.messages || []);
      setCurrentDoc(target.currentDoc || null);
      setActiveCitation(null);
    }
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  };

  const handleDeleteSession = (id: string) => {
    const remaining = sessions.filter((s) => s.id !== id);
    setSessions(remaining);
    if (id === sessionId) {
      if (remaining.length > 0) {
        setSessionId(remaining[0].id);
        setMessages(remaining[0].messages || []);
        setCurrentDoc(remaining[0].currentDoc || null);
      } else {
        startNewChat();
      }
    }
  };

  const handleRenameSession = (id: string, newTitle: string) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, title: newTitle } : s))
    );
  };

  const handleRegenerate = (messageToRegenerate: Message) => {
    const index = messages.findIndex((m) => m.id === messageToRegenerate.id);
    if (index > 0) {
      const prevMessage = messages[index - 1];
      if (prevMessage.role === 'user') {
        setMessages((prev) => prev.slice(0, index));
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
        setIsSidebarOpen((prev) => !prev);
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

    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      citations: [],
    };

    // Auto-create Chat 1, Chat 2, etc. in Recent Chats when a chat starts
    const sessionExists = sessions.some((s) => s.id === sessionId);
    if (!sessionExists) {
      const title = `Chat ${sessionCounter}`;
      const newSession: ChatSession = {
        id: sessionId,
        title,
        messages: [userMessage, assistantMessage],
        currentDoc,
        createdAt: Date.now(),
      };
      setSessions((prev) => [newSession, ...prev]);
      setSessionCounter((prev) => prev + 1);
    }

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setIsLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const history = messages.map(({ role, content }) => ({ role, content }));
      
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const response = await fetch(`${apiBase}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          query: text,
          session_id: sessionId,
          doc_name: currentDoc,
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

  const activeSession = sessions.find((s) => s.id === sessionId);

  return (
    <div className="flex h-screen bg-background text-text-primary overflow-hidden">
      {/* Mobile Sidebar Backdrop */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-20 md:hidden" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar with Recent Chats */}
      <Sidebar 
        sessions={sessions}
        currentSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewChat={() => {
          startNewChat();
          if (window.innerWidth < 768) setIsSidebarOpen(false);
        }}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
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

            {/* Current Chat Title */}
            <span className="text-sm font-semibold text-text-primary hidden sm:inline-block">
              {activeSession ? activeSession.title : `Chat ${sessionCounter}`}
            </span>

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
                  <div className="flex items-center gap-2 text-text-muted text-sm italic">
                    <Loader2 size={16} className="animate-spin text-primary" />
                    Searching relevant context and generating response...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}

          {showScrollDown && (
            <button
              onClick={scrollToBottom}
              className="absolute bottom-28 right-8 p-2 rounded-full bg-surface-02 border border-border-subtle text-text-secondary hover:text-text-primary shadow-lg hover:bg-surface-03 transition-all z-10"
              aria-label="Scroll to bottom"
            >
              <ArrowDown size={18} />
            </button>
          )}
        </main>

        <div className="border-t border-border-subtle bg-background p-4 relative z-0">
          <div className="max-w-4xl mx-auto">
            <div className="relative flex items-end bg-surface-01 border border-border-subtle rounded-2xl p-2 focus-within:border-primary/50 transition-all shadow-sm">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  adjustTextareaHeight();
                }}
                onKeyDown={handleKeyDown}
                placeholder={currentDoc ? `Ask about "${currentDoc}"...` : "Upload a document to ask questions..."}
                rows={1}
                disabled={isLoading}
                className="w-full bg-transparent border-0 focus:outline-none resize-none px-3 py-2 text-text-primary placeholder:text-text-muted text-[15px] max-h-48"
              />
              {isLoading ? (
                <button
                  type="button"
                  onClick={stopGeneration}
                  className="mb-0.5 mr-0.5 p-2.5 bg-surface-02 border border-border-subtle text-text-primary rounded-xl hover:bg-surface-03 transition-colors shrink-0"
                  title="Stop generation"
                >
                  <Square size={16} className="fill-current text-primary" />
                </button>
              ) : (
                <button
                  type="button"
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
