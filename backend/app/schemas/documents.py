from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Any


DocumentState = Literal["queued", "processing", "completed", "failed"]


class UploadResponse(BaseModel):
    document_id: str
    num_pages: int
    state: DocumentState
    created_at: datetime


class StatusResponse(BaseModel):
    document_id: str
    state: DocumentState
    progress: int = Field(ge=0, le=100)
    current_page: int | None = None
    current_chunk: int | None = None
    total_pages: int | None = None
    total_chunks: int | None = None
    message: str | None = None
    updated_at: datetime


class ImageBBox(BaseModel):
    # Pixel coordinates in the rendered page image space
    x0: int
    y0: int
    x1: int
    y1: int


class CellConfidence(BaseModel):
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class RowMetadata(BaseModel):
    page_number: int
    chunk_index: int
    bbox: ImageBBox
    confidence: float = Field(ge=0.0, le=1.0)


class PageTableResponse(BaseModel):
    document_id: str
    page_number: int
    header: list[str]
    rows: list[list[str]]
    row_metadata: list[RowMetadata]


class GlobalTableRow(BaseModel):
    page_number: int
    row_index_on_page: int
    values: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: ImageBBox | None = None


class GlobalTableResponse(BaseModel):
    document_id: str
    header: list[str]
    rows: list[GlobalTableRow]


class ExportRequest(BaseModel):
    format: Literal["csv", "excel"] = "excel"
    include_confidence: bool = True
    # reserved for future UX toggles / filtering
    options: dict[str, Any] = Field(default_factory=dict)


