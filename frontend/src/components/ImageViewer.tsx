import { useState, useRef, useEffect, useMemo } from "react";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ExtractedRow } from "@/types/extraction";
import { api } from "@/lib/api";

interface ImageViewerProps {
  documentId: string;
  totalPages: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  selectedRow: ExtractedRow | null;
}

const ImageViewer = ({ documentId, totalPages, currentPage, onPageChange, selectedRow }: ImageViewerProps) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const [imgNatural, setImgNatural] = useState<{ w: number; h: number } | null>(null);

  const currentImageUrl = useMemo(
    () => api.pageImageUrl(documentId, currentPage),
    [documentId, currentPage],
  );
  const pages = useMemo(() => Array.from({ length: totalPages }, (_, i) => i + 1), [totalPages]);

  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setImgNatural(null);
  }, [currentPage]);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom(prev => Math.min(Math.max(0.5, prev + delta), 3));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom > 1) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div className="h-full flex flex-col bg-surface-sunken">
      {/* Header */}
      <div className="h-12 px-4 flex items-center justify-between border-b border-border bg-card">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="h-8 w-8 p-0"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm text-foreground min-w-[100px] text-center">
            Page {currentPage} / {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="h-8 w-8 p-0"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom(prev => Math.max(0.5, prev - 0.25))}
            className="h-8 w-8 p-0"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-xs text-muted-foreground w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom(prev => Math.min(3, prev + 0.25))}
            className="h-8 w-8 p-0"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Image Area */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-hidden relative"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default' }}
      >
        <div 
          className="absolute inset-0 flex items-center justify-center p-4"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
          }}
        >
          {documentId && (
            <div className="relative bg-white shadow-lg rounded">
              <img
                src={currentImageUrl}
                alt={`Page ${currentPage}`}
                className="max-w-full max-h-full object-contain select-none"
                draggable={false}
                onLoad={(e) => {
                  const el = e.currentTarget;
                  setImgNatural({ w: el.naturalWidth, h: el.naturalHeight });
                }}
              />
              
              {/* Highlight overlay for selected row */}
              {selectedRow &&
                selectedRow.pageNumber === currentPage &&
                selectedRow.bbox &&
                imgNatural && (
                <div
                  className="absolute border-2 border-primary/40 bg-primary/10 rounded pointer-events-none transition-all duration-200"
                  style={{
                    left: `${(selectedRow.bbox.x0 / imgNatural.w) * 100}%`,
                    top: `${(selectedRow.bbox.y0 / imgNatural.h) * 100}%`,
                    width: `${((selectedRow.bbox.x1 - selectedRow.bbox.x0) / imgNatural.w) * 100}%`,
                    height: `${((selectedRow.bbox.y1 - selectedRow.bbox.y0) / imgNatural.h) * 100}%`,
                  }}
                />
              )}
            </div>
          )}
        </div>
      </div>

      {/* Page Thumbnails */}
      <div className="h-20 border-t border-border bg-card px-4 py-2 overflow-x-auto">
        <div className="flex gap-2 h-full">
          {pages.map((pageNumber) => (
            <button
              key={pageNumber}
              onClick={() => onPageChange(pageNumber)}
              className={`page-thumbnail h-full aspect-[3/4] flex-shrink-0 overflow-hidden ${
                pageNumber === currentPage ? 'page-thumbnail-active' : ''
              }`}
            >
              <img
                src={api.pageImageUrl(documentId, pageNumber)}
                alt={`Page ${pageNumber}`}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ImageViewer;
