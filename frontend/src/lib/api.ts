export type UploadResponse = {
  document_id: string;
  num_pages: number;
  state: "queued" | "processing" | "completed" | "failed";
  created_at: string;
};

export type StatusResponse = {
  document_id: string;
  state: "queued" | "processing" | "completed" | "failed";
  progress: number;
  current_page?: number | null;
  current_chunk?: number | null;
  total_pages?: number | null;
  total_chunks?: number | null;
  message?: string | null;
  updated_at: string;
};

export type ImageBBox = { x0: number; y0: number; x1: number; y1: number };

export type RowMetadata = {
  page_number: number;
  chunk_index: number;
  bbox: ImageBBox;
  confidence: number;
};

export type PageTableResponse = {
  document_id: string;
  page_number: number;
  header: string[];
  rows: string[][];
  row_metadata: RowMetadata[];
};

export type GlobalTableRow = {
  page_number: number;
  row_index_on_page: number;
  values: string[];
  confidence: number;
  bbox?: ImageBBox | null;
};

export type GlobalTableResponse = {
  document_id: string;
  header: string[];
  rows: GlobalTableRow[];
};

export type ExportRequest = {
  format: "csv" | "excel";
  include_confidence: boolean;
};

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const DEFAULT_BASE_URL = "";

export function apiBaseUrl(): string {
  // Vite env var (recommended in dev): VITE_API_BASE_URL=http://localhost:8000
  const v = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined;
  return (v ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBaseUrl()}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, text || res.statusText);
  }
  return (await res.json()) as T;
}

export const api = {
  async uploadDocument(file: File, pdfPassword?: string): Promise<UploadResponse> {
    const fd = new FormData();
    fd.append("file", file);
    if (pdfPassword) fd.append("pdf_password", pdfPassword);
    return await fetchJson<UploadResponse>("/api/v1/documents/upload", {
      method: "POST",
      body: fd,
    });
  },

  async getStatus(documentId: string): Promise<StatusResponse> {
    return await fetchJson<StatusResponse>(`/api/v1/documents/${documentId}/status`);
  },

  pageImageUrl(documentId: string, pageNumber: number): string {
    return `${apiBaseUrl()}/api/v1/documents/${documentId}/pages/${pageNumber}/image`;
  },

  async getPageTable(documentId: string, pageNumber: number): Promise<PageTableResponse> {
    return await fetchJson<PageTableResponse>(
      `/api/v1/documents/${documentId}/pages/${pageNumber}/table`,
    );
  },

  async getGlobalTable(documentId: string): Promise<GlobalTableResponse> {
    return await fetchJson<GlobalTableResponse>(`/api/v1/documents/${documentId}/table`);
  },

  async exportDocument(documentId: string, req: ExportRequest): Promise<Response> {
    const res = await fetch(`${apiBaseUrl()}/api/v1/documents/${documentId}/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new ApiError(res.status, text || res.statusText);
    }
    return res;
  },
};

export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError;
}


