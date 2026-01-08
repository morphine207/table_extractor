import { useMemo, useState } from "react";
import { ExtractedRow, ExtractionSession } from "@/types/extraction";
import ImageViewer from "./ImageViewer";
import ExtractedTable from "./ExtractedTable";
import ExportModal from "./ExportModal";
import { useQuery } from "@tanstack/react-query";
import { api, isApiError } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ResultsWorkspaceProps {
  session: ExtractionSession;
}

const ResultsWorkspace = ({ session }: ResultsWorkspaceProps) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedRow, setSelectedRow] = useState<ExtractedRow | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const { toast } = useToast();

  // Global table is still useful for document-wide counts and navigation metadata,
  // but we render a per-page table because headers can change across pages.
  const globalQuery = useQuery({
    queryKey: ["globalTable", session.documentId],
    queryFn: async () => api.getGlobalTable(session.documentId),
    refetchOnWindowFocus: false,
  });

  const allRows: ExtractedRow[] = useMemo(() => {
    const rows = globalQuery.data?.rows ?? [];
    return rows.map((r, idx) => ({
      id: `${session.documentId}-${r.page_number}-${r.row_index_on_page}-${idx}`,
      pageNumber: r.page_number,
      values: r.values,
      confidence: r.confidence,
      bbox: r.bbox ?? null,
    }));
  }, [globalQuery.data?.rows, session.documentId]);

  const pageQuery = useQuery({
    queryKey: ["pageTable", session.documentId, currentPage],
    queryFn: async () => api.getPageTable(session.documentId, currentPage),
    refetchOnWindowFocus: false,
    retry: (failureCount, err: any) => {
      // If backend says "not ready" (409), keep retrying briefly.
      const status = err?.status as number | undefined;
      if (status === 409) return failureCount < 10;
      return failureCount < 2;
    },
    retryDelay: (attempt) => Math.min(1500, 300 * (attempt + 1)),
  });

  const pageHeader = pageQuery.data?.header ?? [];
  const pageRows: ExtractedRow[] = useMemo(() => {
    const rows = pageQuery.data?.rows ?? [];
    const meta = pageQuery.data?.row_metadata ?? [];
    return rows.map((values, i) => ({
      id: `${session.documentId}-p${currentPage}-r${i}`,
      pageNumber: currentPage,
      values,
      confidence: meta[i]?.confidence ?? 0,
      bbox: meta[i]?.bbox ?? null,
    }));
  }, [currentPage, pageQuery.data?.row_metadata, pageQuery.data?.rows, session.documentId]);

  const handleRowSelect = (row: ExtractedRow) => {
    setSelectedRow(row);
    // Navigate to the page where this row is from
    if (row.pageNumber !== currentPage) {
      setCurrentPage(row.pageNumber);
    }
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= session.totalPages) {
      setCurrentPage(page);
    }
  };

  const handleExport = async (includeConfidence: boolean) => {
    try {
      const res = await api.exportDocument(session.documentId, {
        format: "excel",
        include_confidence: includeConfidence,
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${session.fileName.replace(/\.[^/.]+$/, "")}_extracted.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      toast({
        title: "Export failed",
        description: isApiError(err) ? err.message : "Unable to export file.",
        variant: "destructive",
      });
    }
  };

  const lowConfidenceCount = allRows.filter((r) => r.confidence < 0.8).length;

  return (
    <div className="h-[calc(100vh-3.5rem)] flex animate-fade-in">
      {/* Left: Image Viewer (60%) */}
      <div className="w-[60%] h-full">
        <ImageViewer
          documentId={session.documentId}
          totalPages={session.totalPages}
          currentPage={currentPage}
          onPageChange={handlePageChange}
          selectedRow={selectedRow}
        />
      </div>

      {/* Right: Extracted Table (40%) */}
      <div className="w-[40%] h-full">
        <ExtractedTable
          header={pageHeader}
          rows={pageRows}
          selectedRow={selectedRow}
          onRowSelect={handleRowSelect}
          onExportClick={() => setIsExportModalOpen(true)}
        />
      </div>

      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        totalRows={allRows.length}
        lowConfidenceCount={lowConfidenceCount}
        onExport={handleExport}
      />
    </div>
  );
};

export default ResultsWorkspace;
