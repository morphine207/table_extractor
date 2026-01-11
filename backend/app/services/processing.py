from __future__ import annotations

import asyncio
import json
import os
import re
import traceback
from datetime import datetime, timezone
from uuid import uuid4

from PIL import Image

from app.core.config import settings
from app.services.chunking import iter_vertical_chunks
from app.services.gemini import GeminiClient, DEFAULT_PROMPT
from app.services.parsing import (
    parse_extracted_text,
    adjust_table_rows,
    row_confidence,
    dedupe_consecutive_rows,
)
from app.storage.filesystem import FilesystemStorage
from app.storage.progress import InMemoryProgressStore


def new_document_id() -> str:
    return uuid4().hex


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: str, payload: object) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _write_bytes(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text or "")


def _save_png(img: Image.Image, path: str, *, compress_level: int = 1) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Lower compression = faster CPU, larger files (good tradeoff for pipelines).
    img.save(path, format="PNG", compress_level=int(compress_level))


def _downscale_for_gemini(img: Image.Image) -> Image.Image:
    """
    Reduce image size before sending to the model. This improves latency and reduces upload cost.
    """
    max_w = int(getattr(settings, "max_chunk_width", 0) or 0)
    if max_w <= 0 or img.width <= max_w:
        return img
    ratio = max_w / float(img.width)
    new_h = max(1, int(round(img.height * ratio)))
    return img.resize((max_w, new_h), Image.LANCZOS)


def _row_bbox_for_chunk(*, page_width: int, top: int, bottom: int, idx: int, n: int) -> dict:
    if n <= 0:
        n = 1
    h = max(1.0, (bottom - top) / n)
    y0 = int(round(top + idx * h))
    y1 = int(round(min(bottom, top + (idx + 1) * h)))
    return {"x0": 0, "y0": y0, "x1": int(page_width), "y1": int(y1)}

def _friendly_error_message(err: Exception) -> str:
    msg = str(err) or err.__class__.__name__
    # Surface Gemini quota issues clearly.
    if "ResourceExhausted" in err.__class__.__name__ or "Quota exceeded" in msg or "exceeded your current quota" in msg:
        return "Gemini rate limit/quota exceeded. Please wait a bit and try again (or upgrade billing/limits)."
    return msg


def _parse_retry_seconds(msg: str) -> float | None:
    # Example seen in logs: "Please retry in 31.184393644s."
    m = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", msg, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


class DocumentProcessor:
    """
    Orchestrates the end-to-end pipeline and persists outputs to filesystem storage.
    """

    def __init__(self, *, storage: FilesystemStorage, progress: InMemoryProgressStore):
        self.storage = storage
        self.progress = progress

    async def process_pdf_bytes(
        self,
        *,
        document_id: str,
        pdf_bytes: bytes,
        pdf_password: str | None,
        chunk_height: int = 500,
        overlap: int = 50,
        prompt: str = DEFAULT_PROMPT,
    ) -> None:
        paths = self.storage.document_paths(document_id)

        try:
            if not settings.gemini_api_key:
                self.progress.update(
                    document_id,
                    state="failed",
                    message="Missing GEMINI_API_KEY environment variable.",
                    progress=0,
                )
                return

            from app.services.pdf import pdf_to_images  # local import to keep service boundaries clean

            self.progress.update(document_id, state="processing", message=None)

            # Save original (off the event loop)
            await asyncio.to_thread(_write_bytes, paths.pdf_path, pdf_bytes)

            images = pdf_to_images(pdf_bytes, password=pdf_password, dpi=settings.pdf_render_dpi)
            total_pages = len(images)

            # Precompute total chunks for progress.
            per_page_chunks = []
            total_chunks = 0
            # Keep chunking roughly consistent in *physical* size by scaling with DPI.
            scale = max(1.0, float(settings.pdf_render_dpi) / 72.0)
            chunk_height_px = int(round(chunk_height * scale))
            overlap_px = int(round(overlap * scale))
            for img in images:
                chunks = iter_vertical_chunks(img, chunk_height=chunk_height_px, overlap=overlap_px)
                per_page_chunks.append(chunks)
                total_chunks += len(chunks)

            self.progress.update(document_id, total_pages=total_pages, total_chunks=total_chunks)

            gemini = GeminiClient(api_key=settings.gemini_api_key, model_name=settings.gemini_model)

            global_header: list[str] | None = None
            global_rows: list[dict] = []

            chunk_counter = 0

            sem = asyncio.Semaphore(max(1, int(getattr(settings, "gemini_concurrency", 1) or 1)))

            async def _extract_with_retries(img: Image.Image, *, chunk_label: str) -> str:
                max_attempts = 6
                base_wait = 2.0
                last_err: Exception | None = None

                for attempt in range(1, max_attempts + 1):
                    try:
                        txt = await gemini.extract_table_text(img, prompt=prompt)
                        # Clear transient message if any
                        self.progress.update(document_id, message=None)
                        return txt
                    except Exception as e:
                        last_err = e
                        # Detect Gemini quota errors (google.api_core.exceptions.ResourceExhausted)
                        retry_s = _parse_retry_seconds(str(e))
                        wait_s = retry_s if retry_s is not None else min(60.0, base_wait * (2 ** (attempt - 1)))
                        # Update status so frontend doesn't look "stuck"
                        self.progress.update(
                            document_id,
                            message=(
                                f"Rate limited by Gemini ({chunk_label}). Retrying in {wait_s:.0f}s "
                                f"(attempt {attempt}/{max_attempts})…"
                            ),
                        )
                        await asyncio.sleep(wait_s)

                # exhausted retries
                assert last_err is not None
                raise last_err

            for page_idx, page_img in enumerate(images, start=1):
                self.progress.update(document_id, current_page=page_idx, current_chunk=None)

                # Save page image (optional; kept ON by default because /pages/{n}/image serves it)
                if getattr(settings, "save_page_images", True):
                    page_path = os.path.join(paths.pages_dir, f"{page_idx}.png")
                    await asyncio.to_thread(
                        _save_png,
                        page_img,
                        page_path,
                        compress_level=int(getattr(settings, "png_compress_level", 1) or 1),
                    )

                header: list[str] | None = None
                page_rows: list[list[str]] = []
                page_row_meta: list[dict] = []

                chunks = per_page_chunks[page_idx - 1]
                page_width, _page_height = page_img.size

                async def _extract_one_chunk(chunk) -> tuple[int, str]:
                    # Optional: persist chunk image (very expensive; OFF by default)
                    if getattr(settings, "save_chunk_images", False):
                        chunk_dir = os.path.join(paths.chunks_dir, f"page_{page_idx}")
                        chunk_img_path = os.path.join(chunk_dir, f"chunk_{chunk.chunk_index}.png")
                        await asyncio.to_thread(
                            _save_png,
                            chunk.image,
                            chunk_img_path,
                            compress_level=int(getattr(settings, "png_compress_level", 1) or 1),
                        )

                    img_for_gemini = _downscale_for_gemini(chunk.image)

                    async with sem:
                        txt = await _extract_with_retries(
                            img_for_gemini,
                            chunk_label=f"page {page_idx} chunk {chunk.chunk_index}",
                        )

                    # Optional: persist raw model output (expensive; OFF by default)
                    if getattr(settings, "save_raw_chunks", False):
                        raw_dir = os.path.join(paths.raw_dir, f"page_{page_idx}")
                        raw_path = os.path.join(raw_dir, f"chunk_{chunk.chunk_index}.txt")
                        await asyncio.to_thread(_write_text, raw_path, txt)

                    return int(chunk.chunk_index), (txt or "")

                # 1) Extract text for all chunks with bounded parallelism.
                tasks = [asyncio.create_task(_extract_one_chunk(c)) for c in chunks]
                chunk_text_by_index: dict[int, str] = {}
                try:
                    for fut in asyncio.as_completed(tasks):
                        idx, txt = await fut
                        chunk_text_by_index[idx] = txt
                        chunk_counter += 1
                        self.progress.update(
                            document_id,
                            current_chunk=idx,
                            progress=int(round((chunk_counter / max(1, total_chunks)) * 100)),
                        )
                except Exception:
                    for t in tasks:
                        t.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    raise
                finally:
                    self.progress.update(document_id, current_chunk=None)

                # 2) Parse/merge sequentially in chunk order for stable dedupe behavior.
                for chunk in chunks:
                    chunk_text = chunk_text_by_index.get(int(chunk.chunk_index), "") or ""

                    parsed = parse_extracted_text(chunk_text, delimiter="|")
                    if not parsed:
                        continue

                    if header is None:
                        header = parsed[0]
                        data_rows = parsed[1:]
                    else:
                        normalized_header = [h.strip() for h in header]
                        candidate = [c.strip() for c in parsed[0]]
                        if candidate == normalized_header:
                            data_rows = parsed[1:]
                        else:
                            data_rows = parsed

                    data_rows = adjust_table_rows(header, data_rows) if header else data_rows

                    # Dedupe overlap (exact consecutive duplicates)
                    deduped = dedupe_consecutive_rows(data_rows)
                    kept: list[list[str]] = []
                    for r in deduped:
                        if page_rows and [c.strip() for c in r] == [c.strip() for c in page_rows[-1]]:
                            continue
                        kept.append(r)

                    n = len(kept)
                    for i, row in enumerate(kept):
                        bbox = _row_bbox_for_chunk(
                            page_width=page_width, top=chunk.top, bottom=chunk.bottom, idx=i, n=n
                        )
                        conf = row_confidence(row)
                        page_rows.append(row)
                        page_row_meta.append(
                            {
                                "page_number": page_idx,
                                "chunk_index": chunk.chunk_index,
                                "bbox": bbox,
                                "confidence": conf,
                            }
                        )

                if header is None:
                    header = []

                # Save per-page table JSON
                page_table_payload = {
                    "document_id": document_id,
                    "page_number": page_idx,
                    "header": header,
                    "rows": page_rows,
                    "row_metadata": page_row_meta,
                    "generated_at": _utc_iso(),
                }
                await asyncio.to_thread(
                    _write_json,
                    os.path.join(paths.tables_dir, f"page_{page_idx}.json"),
                    page_table_payload,
                )

                # Append to global
                if global_header is None and header:
                    global_header = header

                for r_idx, (row, meta) in enumerate(zip(page_rows, page_row_meta)):
                    global_rows.append(
                        {
                            "page_number": page_idx,
                            "row_index_on_page": r_idx,
                            "values": row,
                            "confidence": float(meta.get("confidence", 0.0)),
                            "bbox": meta.get("bbox"),
                        }
                    )

            global_payload = {
                "document_id": document_id,
                "header": global_header or [],
                "rows": global_rows,
                "generated_at": _utc_iso(),
            }
            await asyncio.to_thread(_write_json, os.path.join(paths.tables_dir, "global.json"), global_payload)

            self.progress.update(document_id, state="completed", current_chunk=None, current_page=None, progress=100, message=None)
        except Exception as e:
            # Persist error details for debugging
            try:
                os.makedirs(paths.raw_dir, exist_ok=True)
                with open(os.path.join(paths.raw_dir, "error.txt"), "w", encoding="utf-8") as f:
                    f.write(_friendly_error_message(e) + "\n\n")
                    f.write(traceback.format_exc())
            except Exception:
                pass

            self.progress.update(
                document_id,
                state="failed",
                message=_friendly_error_message(e),
                current_chunk=None,
                current_page=None,
            )


