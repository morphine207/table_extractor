from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app.core.config import settings
from app.schemas.documents import (
    UploadResponse,
    StatusResponse,
    PageTableResponse,
    GlobalTableResponse,
    ExportRequest,
)
from app.services.exporting import to_csv_bytes, to_excel_bytes_multi
from app.services.processing import DocumentProcessor, new_document_id
from app.services.pdf import pdf_num_pages
from app.storage.filesystem import FilesystemStorage
from app.storage.progress import InMemoryProgressStore


router = APIRouter()

_storage = FilesystemStorage(settings.storage_dir)
_progress = InMemoryProgressStore()
_processor = DocumentProcessor(storage=_storage, progress=_progress)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    pdf_password: str | None = Form(default=None),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await file.read()

    try:
        num_pages = pdf_num_pages(pdf_bytes, password=pdf_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error opening PDF: {e}")

    document_id = new_document_id()
    _storage.document_paths(document_id)  # ensure dirs exist
    _progress.create(document_id, total_pages=num_pages)

    # Fire-and-forget processing
    asyncio.create_task(
        _processor.process_pdf_bytes(
            document_id=document_id,
            pdf_bytes=pdf_bytes,
            pdf_password=pdf_password,
        )
    )

    return UploadResponse(
        document_id=document_id,
        num_pages=num_pages,
        state="queued",
        created_at=_utcnow(),
    )


@router.get("/{document_id}/status", response_model=StatusResponse)
async def document_status(document_id: str):
    st = _progress.get(document_id)
    if not st:
        raise HTTPException(status_code=404, detail="Document not found.")
    return StatusResponse(
        document_id=document_id,
        state=st.state,
        progress=st.progress,
        current_page=st.current_page,
        current_chunk=st.current_chunk,
        total_pages=st.total_pages,
        total_chunks=st.total_chunks,
        message=st.message,
        updated_at=st.updated_at,
    )


@router.get("/{document_id}/pages/{page_number}/image")
async def get_page_image(document_id: str, page_number: int):
    if page_number < 1:
        raise HTTPException(status_code=400, detail="page_number must be >= 1")
    paths = _storage.document_paths(document_id)
    img_path = os.path.join(paths.pages_dir, f"{page_number}.png")
    if not os.path.exists(img_path):
        st = _progress.get(document_id)
        if not st:
            raise HTTPException(status_code=404, detail="Document not found.")
        raise HTTPException(status_code=409, detail="Page image not available yet.")
    return FileResponse(img_path, media_type="image/png")


@router.get("/{document_id}/pages/{page_number}/table", response_model=PageTableResponse)
async def get_page_table(document_id: str, page_number: int):
    if page_number < 1:
        raise HTTPException(status_code=400, detail="page_number must be >= 1")
    paths = _storage.document_paths(document_id)
    table_path = os.path.join(paths.tables_dir, f"page_{page_number}.json")
    if not os.path.exists(table_path):
        st = _progress.get(document_id)
        if not st:
            raise HTTPException(status_code=404, detail="Document not found.")
        raise HTTPException(status_code=409, detail="Table not available yet.")
    with open(table_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return PageTableResponse(**payload)


@router.get("/{document_id}/table", response_model=GlobalTableResponse)
async def get_global_table(document_id: str):
    paths = _storage.document_paths(document_id)
    global_path = os.path.join(paths.tables_dir, "global.json")
    if not os.path.exists(global_path):
        st = _progress.get(document_id)
        if not st:
            raise HTTPException(status_code=404, detail="Document not found.")
        raise HTTPException(status_code=409, detail="Global table not available yet.")
    with open(global_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return GlobalTableResponse(**payload)


@router.post("/{document_id}/export")
async def export_document(document_id: str, req: ExportRequest):
    paths = _storage.document_paths(document_id)
    global_path = os.path.join(paths.tables_dir, "global.json")
    if not os.path.exists(global_path):
        st = _progress.get(document_id)
        if not st:
            raise HTTPException(status_code=404, detail="Document not found.")
        raise HTTPException(status_code=409, detail="Global table not available yet.")

    if req.format == "csv":
        # CSV is single-sheet by nature: normalize across pages.
        with open(global_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        rows: list[dict] = payload.get("rows") or []

        # Union headers across per-page tables (intelligent normalization).
        union_header: list[str] = []
        page_headers: dict[int, list[str]] = {}
        total_pages = (_progress.get(document_id).total_pages if _progress.get(document_id) else None) or 0
        for p in range(1, int(total_pages) + 1):
            page_path = os.path.join(paths.tables_dir, f"page_{p}.json")
            if not os.path.exists(page_path):
                continue
            with open(page_path, "r", encoding="utf-8") as pf:
                page_payload = json.load(pf)
            h = page_payload.get("header") or []
            page_headers[p] = h
            for col in h:
                if col not in union_header:
                    union_header.append(col)

        out_rows = []
        for r in rows:
            page_no = int(r.get("page_number") or 0)
            values = r.get("values") or []
            h = page_headers.get(page_no, [])
            row_map = {h[i]: values[i] for i in range(min(len(h), len(values)))}
            out = {"page_number": page_no, **{c: row_map.get(c, "") for c in union_header}}
            if req.include_confidence:
                out["confidence"] = float(r.get("confidence") or 0.0)
            out_rows.append(out)

        df = pd.DataFrame(out_rows, columns=["page_number", *union_header, *(["confidence"] if req.include_confidence else [])])
        content = to_csv_bytes(df)
        media_type = "text/csv"
        filename = f"{document_id}.csv"
    else:
        # Excel: one sheet per page (supports changing table structures).
        st = _progress.get(document_id)
        total_pages = int(st.total_pages or 0) if st else 0
        sheets: dict[str, pd.DataFrame] = {}
        for p in range(1, total_pages + 1):
            page_path = os.path.join(paths.tables_dir, f"page_{p}.json")
            if not os.path.exists(page_path):
                raise HTTPException(status_code=409, detail=f"Page {p} table not available yet.")
            with open(page_path, "r", encoding="utf-8") as pf:
                page_payload = json.load(pf)
            header: list[str] = page_payload.get("header") or []
            values: list[list[str]] = page_payload.get("rows") or []
            df_page = pd.DataFrame(values, columns=header if header else None)
            if req.include_confidence:
                meta = page_payload.get("row_metadata") or []
                df_page["confidence"] = [float(m.get("confidence") or 0.0) for m in meta]
            sheets[f"Page {p}"] = df_page

        try:
            content = to_excel_bytes_multi(sheets)
        except ModuleNotFoundError as e:
            # pandas ExcelWriter(engine="openpyxl") requires openpyxl installed
            if "openpyxl" in str(e):
                raise HTTPException(
                    status_code=500,
                    detail="Excel export requires 'openpyxl'. Install it with: pip install openpyxl",
                )
            raise
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{document_id}.xlsx"

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)


