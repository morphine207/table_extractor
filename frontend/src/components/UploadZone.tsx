import { useState, useCallback } from "react";
import { Upload, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
}

const UploadZone = ({ onFileSelect }: UploadZoneProps) => {
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  }, [onFileSelect]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-3.5rem)] px-6">
      <div className="w-full max-w-xl">
        <div
          className={`upload-zone ${isDragActive ? 'upload-zone-active' : ''} p-12 flex flex-col items-center justify-center cursor-pointer bg-card`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-6">
            <Upload className="w-7 h-7 text-muted-foreground" />
          </div>
          
          <h2 className="text-lg font-medium text-foreground mb-2">
            Upload PDF
          </h2>
          
          <p className="text-sm text-muted-foreground mb-6">
            Multi-page PDFs supported
          </p>

          <input
            id="file-input"
            type="file"
            accept=".pdf"
            onChange={handleFileInput}
            className="hidden"
          />
        </div>

        <div className="flex justify-center mt-4">
          <Button
            variant="outline"
            onClick={() => document.getElementById('file-input')?.click()}
            className="gap-2"
          >
            <FolderOpen className="w-4 h-4" />
            Browse files
          </Button>
        </div>

        <p className="text-xs text-muted-foreground text-center mt-6">
          Files are processed securely and not shared
        </p>
      </div>
    </div>
  );
};

export default UploadZone;
