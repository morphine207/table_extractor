import { Loader2 } from "lucide-react";

interface ProcessingIndicatorProps {
  currentPage: number;
  totalPages: number;
  fileName: string;
  currentChunk?: number | null;
  totalChunks?: number | null;
  percent?: number;
  message?: string | null;
}

const ProcessingIndicator = ({
  currentPage,
  totalPages,
  fileName,
  currentChunk,
  totalChunks,
  percent,
  message,
}: ProcessingIndicatorProps) => {
  const progress = typeof percent === "number" ? percent : totalPages > 0 ? (currentPage / totalPages) * 100 : 0;

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-3.5rem)] px-6 animate-fade-in">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center mb-8">
          <Loader2 className="w-10 h-10 text-primary animate-spin" />
        </div>
        
        <h2 className="text-lg font-medium text-foreground text-center mb-2">
          Processing {fileName}
        </h2>
        
        <p className="text-sm text-muted-foreground text-center mb-6">
          Processing page {Math.max(0, currentPage)} of {Math.max(0, totalPages)}
          {typeof currentChunk === "number" && typeof totalChunks === "number"
            ? ` • chunk ${currentChunk} of ${totalChunks}`
            : "…"}
        </p>
        {message ? (
          <p className="text-xs text-muted-foreground text-center mb-4">
            {message}
          </p>
        ) : null}

        <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
          <div 
            className="h-full bg-primary transition-all duration-300 ease-out rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default ProcessingIndicator;
