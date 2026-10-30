"use client";

import { useState } from "react";
import { Plus, MessageSquare, Trash2, Edit2, Check, X } from "lucide-react";
import { ChatSession } from "@/types";

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId: string;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  onRenameSession: (id: string, newTitle: string) => void;
  isOpen: boolean;
}

export function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onRenameSession,
  isOpen,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  const handleStartRename = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditingTitle(session.title);
  };

  const handleSaveRename = (id: string, e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.stopPropagation();
    if (editingTitle.trim()) {
      onRenameSession(id, editingTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  return (
    <div
      className={`
        fixed inset-y-0 left-0 z-30 md:relative flex flex-col bg-surface-01 border-r border-border-subtle h-full 
        transition-all duration-300 ease-in-out
        ${isOpen ? "w-[260px] translate-x-0" : "-translate-x-full md:translate-x-0 md:w-[68px]"}
      `}
    >
      {/* Brand Header */}
      <div className="p-4 border-b border-border-subtle h-16 flex flex-col justify-center shrink-0 whitespace-nowrap overflow-hidden">
        <h1 className="text-xl font-bold text-text-primary tracking-tight">
          {isOpen ? "DOCrag" : "DR"}
        </h1>
        {isOpen && (
          <p className="text-sm text-text-secondary mt-1 transition-opacity duration-300">
            Your document assistant
          </p>
        )}
      </div>

      {/* New Chat Button */}
      <div className="p-4 shrink-0">
        <button
          onClick={onNewChat}
          title="New Chat"
          className={`flex items-center justify-center gap-2 bg-primary hover:bg-primary-hover text-text-primary py-2 rounded-lg font-medium transition-all duration-200 overflow-hidden whitespace-nowrap active:scale-95 hover:scale-[1.02] hover:shadow-[0_0_15px_rgba(255,107,0,0.3)] ${
            isOpen ? "w-full px-4" : "w-10 h-10 px-0 mx-auto"
          }`}
        >
          <Plus size={18} className="shrink-0" />
          {isOpen && <span>New Chat</span>}
        </button>
      </div>

      {/* Recent Chats List */}
      <div className={`px-4 pb-4 flex-1 overflow-y-auto ${!isOpen ? "items-center" : ""}`}>
        {isOpen && (
          <h2 className="text-xs font-semibold text-text-muted mb-3 uppercase tracking-wider">
            Recent Chats
          </h2>
        )}

        <div className="space-y-1">
          {sessions.length === 0 ? (
            isOpen && (
              <p className="text-xs text-text-muted px-2 py-1 italic">No recent chats</p>
            )
          ) : (
            sessions.map((session) => {
              const isActive = session.id === currentSessionId;
              const isEditing = editingId === session.id;

              return (
                <div
                  key={session.id}
                  className="group relative flex items-center w-full"
                >
                  {isEditing && isOpen ? (
                    <div className="w-full flex items-center gap-1.5 px-2 py-1.5 bg-surface-02 border border-primary/40 rounded-lg">
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleSaveRename(session.id, e);
                          if (e.key === "Escape") setEditingId(null);
                        }}
                        autoFocus
                        className="flex-1 bg-transparent text-sm text-text-primary focus:outline-none min-w-0"
                      />
                      <button
                        onClick={(e) => handleSaveRename(session.id, e)}
                        title="Save"
                        className="p-1 hover:text-green-500 text-text-muted transition-colors"
                      >
                        <Check size={14} />
                      </button>
                      <button
                        onClick={handleCancelRename}
                        title="Cancel"
                        className="p-1 hover:text-red-500 text-text-muted transition-colors"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => onSelectSession(session.id)}
                      title={session.title}
                      className={`
                        w-full text-left flex items-center gap-2.5 py-2 rounded-lg transition-all
                        ${isOpen ? "px-3 pr-16" : "justify-center px-0 h-10"}
                        ${
                          isActive
                            ? "bg-surface-03 text-text-primary font-medium shadow-sm"
                            : "hover:bg-surface-02 text-text-secondary hover:text-text-primary"
                        }
                      `}
                    >
                      <MessageSquare
                        size={16}
                        className={`shrink-0 ${
                          isActive
                            ? "text-primary"
                            : "text-text-muted group-hover:text-primary transition-colors"
                        }`}
                      />
                      {isOpen && (
                        <span className="text-sm truncate flex-1">{session.title}</span>
                      )}
                    </button>
                  )}

                  {/* Actions (Rename / Delete) */}
                  {isOpen && !isEditing && (
                    <div className="absolute right-2 opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity">
                      <button
                        onClick={(e) => handleStartRename(session, e)}
                        title="Rename"
                        className="p-1 rounded hover:bg-surface-03 text-text-muted hover:text-text-primary transition-colors"
                      >
                        <Edit2 size={13} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session.id);
                        }}
                        title="Delete chat"
                        className="p-1 rounded hover:bg-surface-03 text-text-muted hover:text-red-500 transition-colors"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
