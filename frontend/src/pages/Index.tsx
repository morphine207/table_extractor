import { useEffect, useMemo, useState } from "react";
import Header from "@/components/Header";
import UploadZone from "@/components/UploadZone";
import ProcessingIndicator from "@/components/ProcessingIndicator";
import ResultsWorkspace from "@/components/ResultsWorkspace";
import { ExtractionSession } from "@/types/extraction";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, isApiError } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

type AppState = 'upload' | 'processing' | 'results';

const Index = () => {
  const [state, setState] = useState<AppState>('upload');
  const [fileName, setFileName] = useState('');
  const [session, setSession] = useState<ExtractionSession | null>(null);
  const { toast } = useToast();

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => api.uploadDocument(file),
    onSuccess: (res, file) => {
      setSession({
        documentId: res.document_id,
        fileName: file.name,
        totalPages: res.num_pages,
      });
      setState("processing");
    },
    onError: (err: unknown) => {
      toast({
        title: "Upload failed",
        description: isApiError(err) ? err.message : "Unable to upload PDF.",
        variant: "destructive",
      });
      setState("upload");
    },
  });

  const statusQuery = useQuery({
    queryKey: ["documentStatus", session?.documentId],
    enabled: Boolean(session?.documentId),
    queryFn: async () => api.getStatus(session!.documentId),
    refetchInterval: (q) => {
      const data = q.state.data as any;
      const s = data?.state as string | undefined;
      if (s === "completed" || s === "failed") return false;
      return 500;
    },
  });

  useEffect(() => {
    const st = statusQuery.data;
    if (!st) return;
    if (st.state === "completed") setState("results");
    if (st.state === "failed") {
      toast({
        title: "Processing failed",
        description: st.message ?? "The document could not be processed.",
        variant: "destructive",
      });
      setState("upload");
      setSession(null);
    }
  }, [statusQuery.data, toast]);

  const handleFileSelect = (file: File) => {
    setFileName(file.name);
    setState("processing");
    uploadMutation.mutate(file);
  };

  const processingView = useMemo(() => {
    const st = statusQuery.data;
    const totalPages = session?.totalPages ?? st?.total_pages ?? 0;
    return {
      currentPage: st?.current_page ?? 0,
      totalPages,
      currentChunk: st?.current_chunk ?? null,
      totalChunks: st?.total_chunks ?? null,
      percent: st?.progress ?? 0,
      message: st?.message ?? null,
    };
  }, [session?.totalPages, statusQuery.data]);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {state === 'upload' && (
        <UploadZone onFileSelect={handleFileSelect} />
      )}
      
      {state === 'processing' && (
        <ProcessingIndicator
          currentPage={processingView.currentPage}
          totalPages={processingView.totalPages}
          fileName={fileName}
          currentChunk={processingView.currentChunk}
          totalChunks={processingView.totalChunks}
          percent={processingView.percent}
          message={processingView.message}
        />
      )}
      
      {state === 'results' && session && (
        <ResultsWorkspace session={session} />
      )}
    </div>
  );
};

export default Index;
