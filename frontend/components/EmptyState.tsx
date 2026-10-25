import { UploadCloud } from "lucide-react";

interface EmptyStateProps {
  onUploadClick: () => void;
  onExampleClick: (text: string) => void;
  hasDocument: boolean;
}

export function EmptyState({ onUploadClick, onExampleClick, hasDocument }: EmptyStateProps) {
  const examples = [
    "Summarize the document",
    "What are the key findings?",
    "Explain the main concepts",
    "What are the important points?"
  ];

  return (
    <div className="h-full flex flex-col items-center justify-center p-8 max-w-[800px] mx-auto w-full">
      <div className="text-center w-full">
        <h2 className="text-3xl font-bold text-text-primary mb-6 tracking-tight animate-in fade-in slide-in-from-bottom-2 duration-300">
          What would you like to know about your document?
        </h2>
        <p className="text-lg text-text-secondary mb-8 animate-in fade-in slide-in-from-bottom-2 duration-300 delay-75 fill-mode-both">
          Upload a document and ask questions about its contents.
        </p>

        {!hasDocument && (
          <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-150 fill-mode-both mb-12 flex justify-center">
            <button
              onClick={onUploadClick}
              className="flex items-center gap-2 bg-primary hover:bg-primary-hover text-text-primary px-8 py-3.5 rounded-xl font-medium transition-all duration-200 text-[15px] shadow-[0_2px_10px_rgba(255,107,0,0.2)] hover:shadow-[0_4px_16px_rgba(255,122,26,0.3)] hover:scale-[1.01] active:scale-[0.98]"
            >
              <UploadCloud size={18} />
              Upload Document
            </button>
          </div>
        )}
        
        <div className={`w-full ${!hasDocument ? "animate-in fade-in slide-in-from-bottom-2 duration-300 delay-200 fill-mode-both" : "animate-in fade-in slide-in-from-bottom-2 duration-300 delay-75 fill-mode-both"}`}>
          <p className="text-sm font-medium text-text-muted mb-5 text-center">Try asking</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl mx-auto">
            {examples.map((example, idx) => (
              <button
                key={idx}
                onClick={() => onExampleClick(example)}
                className="text-left px-5 py-4 bg-surface-02 border border-border-subtle rounded-xl hover:bg-surface-03 hover:border-primary/40 transition-all duration-200 text-text-secondary hover:text-text-primary hover:-translate-y-[2px] shadow-sm hover:shadow-md animate-in fade-in slide-in-from-bottom-2 fill-mode-both"
                style={{ animationDelay: `${(!hasDocument ? 250 : 150) + (idx * 50)}ms`, animationDuration: '300ms' }}
              >
                <p className="font-medium text-[15px] leading-snug">{example}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
