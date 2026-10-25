import { X, ExternalLink } from "lucide-react";
import { Citation } from "@/types";

interface CitationDrawerProps {
  citation: Citation | null;
  onClose: () => void;
}

export function CitationDrawer({ citation, onClose }: CitationDrawerProps) {
  if (!citation) return null;

  return (
    <div className="w-full md:w-[320px] flex-shrink-0 bg-surface-01 border-l border-border-subtle h-full flex flex-col shadow-2xl absolute md:relative right-0 top-0 bottom-0 z-20 animate-in slide-in-from-bottom-8 md:slide-in-from-right-8 duration-300">
      <div className="flex items-center justify-between p-4 border-b border-border-subtle">
        <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider">Source</h3>
        <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors p-1 rounded-md hover:bg-surface-03">
          <X size={18} />
        </button>
      </div>
      <div className="p-4 flex-1 overflow-y-auto">
        <div className="bg-surface-02 border border-border-subtle rounded-xl p-4 mb-6 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-primary/10 rounded-lg shrink-0">
              <ExternalLink size={16} className="text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-text-primary break-all">{citation.source_file}</p>
              <p className="text-xs text-text-secondary mt-1">Page {citation.page_number}</p>
              {citation.score !== undefined && (
                <p className="text-xs text-text-muted mt-1">Relevance: {citation.score.toFixed(2)}</p>
              )}
            </div>
          </div>
        </div>
        
        {citation.excerpt && (
          <div>
            <h4 className="text-xs font-semibold text-text-muted mb-3 uppercase tracking-wider">Cited Passage</h4>
            <div className="bg-surface-02/50 border border-border-subtle rounded-xl p-4 text-sm text-text-secondary leading-relaxed font-serif relative">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-xl opacity-80"></div>
              "{citation.excerpt}"
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
