import { Plus, MessageSquare, Edit2 } from "lucide-react";

interface SidebarProps {
  onNewChat: () => void;
  isOpen: boolean;
}

export function Sidebar({ onNewChat, isOpen }: SidebarProps) {
  return (
    <div 
      className={`
        fixed inset-y-0 left-0 z-30 md:relative flex flex-col bg-surface-01 border-r border-border-subtle h-full 
        transition-all duration-300 ease-in-out
        ${isOpen ? "w-[260px] translate-x-0" : "-translate-x-full md:translate-x-0 md:w-[68px]"}
      `}
    >
      <div className="p-4 border-b border-border-subtle h-16 flex flex-col justify-center shrink-0 whitespace-nowrap overflow-hidden">
        <h1 className="text-xl font-bold text-text-primary tracking-tight">
          {isOpen ? "DOCrag" : "DR"}
        </h1>
        {isOpen && <p className="text-sm text-text-secondary mt-1 transition-opacity duration-300">Your document assistant</p>}
      </div>

      <div className="p-4 shrink-0">
        <button
          onClick={onNewChat}
          title="New Chat"
          className={`flex items-center justify-center gap-2 bg-primary hover:bg-primary-hover text-text-primary py-2 rounded-lg font-medium transition-all duration-200 overflow-hidden whitespace-nowrap active:scale-95 hover:scale-[1.02] hover:shadow-[0_0_15px_rgba(255,107,0,0.3)] ${isOpen ? "w-full px-4" : "w-10 h-10 px-0 mx-auto"}`}
        >
          <Plus size={18} className="shrink-0" />
          {isOpen && <span>New Chat</span>}
        </button>
      </div>

      <div className={`px-4 pb-4 flex-1 overflow-y-auto ${!isOpen ? "items-center" : ""}`}>
        {isOpen && <h2 className="text-xs font-semibold text-text-muted mb-3 uppercase tracking-wider">Recent Chats</h2>}
        <div className="space-y-1">
          {/* Static placeholders */}
          <button title="What is this document about?" className={`w-full text-left flex items-center gap-2 py-2 rounded-lg hover:bg-surface-03 bg-surface-02/50 text-text-primary hover:-translate-y-[1px] transition-all group relative ${isOpen ? "px-3" : "justify-center px-0 h-10"}`}>
            <MessageSquare size={16} className="text-primary transition-colors shrink-0" />
            {isOpen && (
              <>
                <span className="text-sm truncate flex-1 pr-6">What is this document about?</span>
                <div className="absolute right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Edit2 size={14} className="text-text-muted hover:text-text-primary" />
                </div>
              </>
            )}
          </button>
          <button title="Explain the methodology" className={`w-full text-left flex items-center gap-2 py-2 rounded-lg hover:bg-surface-03 text-text-secondary hover:text-text-primary hover:-translate-y-[1px] transition-all group relative ${isOpen ? "px-3" : "justify-center px-0 h-10"}`}>
            <MessageSquare size={16} className="text-text-muted group-hover:text-primary transition-colors shrink-0" />
            {isOpen && (
              <>
                <span className="text-sm truncate flex-1 pr-6">Explain the methodology</span>
                <div className="absolute right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Edit2 size={14} className="text-text-muted hover:text-text-primary" />
                </div>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
