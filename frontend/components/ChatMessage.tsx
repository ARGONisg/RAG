import { Message } from "@/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, RefreshCcw } from "lucide-react";

interface ChatMessageProps {
  message: Message;
  onCitationClick: (citation: any) => void;
  onRegenerate?: (message: Message) => void;
  isStreaming?: boolean;
}

export function ChatMessage({ message, onCitationClick, onRegenerate, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`py-6 flex group ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] md:max-w-[75%] rounded-2xl p-5 ${isUser ? "bg-surface-02 border border-border-subtle ml-auto text-text-primary" : "bg-transparent text-text-primary"}`}>
        {!isUser && (
          <div className="font-semibold text-primary mb-2 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs">AI</span>
            DOCrag
          </div>
        )}
        
        <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-surface-03 prose-pre:border prose-pre:border-border-subtle">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {message.citations && message.citations.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border-subtle">
            <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Sources</p>
            <div className="flex flex-wrap gap-2">
              {message.citations.map((citation, idx) => (
                <button
                  key={idx}
                  onClick={() => onCitationClick(citation)}
                  className="inline-flex items-center gap-1.5 px-3 py-1 bg-surface-03 hover:bg-border-subtle border border-border-subtle rounded-full text-xs font-medium text-text-primary transition-colors"
                >
                  <span className="truncate max-w-[200px]">{idx + 1} {citation.source_file} &middot; Page {citation.page_number}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {!isUser && !isStreaming && (
          <div className="opacity-0 group-hover:opacity-100 transition-opacity mt-4 flex gap-2">
            <button 
              onClick={() => navigator.clipboard.writeText(message.content)} 
              className="p-1.5 text-text-muted hover:text-text-primary rounded-md hover:bg-surface-03 transition-colors" 
              title="Copy"
            >
              <Copy size={14} />
            </button>
            <button 
              onClick={() => onRegenerate?.(message)} 
              className="p-1.5 text-text-muted hover:text-text-primary rounded-md hover:bg-surface-03 transition-colors" 
              title="Regenerate"
            >
              <RefreshCcw size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
