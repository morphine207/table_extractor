export type ConfidenceLevel = 'high' | 'medium' | 'low';

export type FilterOption = 'all' | 'low-confidence';

export interface ImageBBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface ExtractedRow {
  id: string;
  pageNumber: number;
  values: string[];
  confidence: number;
  bbox?: ImageBBox | null;
}

export interface ExtractionSession {
  documentId: string;
  fileName: string;
  totalPages: number;
}
