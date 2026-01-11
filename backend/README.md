## Table Extractor Backend (FastAPI)

This backend replaces the previous Streamlit implementation with a **stateless FastAPI API** that a decoupled frontend can consume.

### Quick start

- **Install**:

```bash
pip install -r requirements.txt
```

- **Configure** (copy `env.example` to `.env` if your environment supports it, or export vars):
  - `GEMINI_API_KEY=...`
  - Optional performance knobs (see `env.example`):
    - `PDF_RENDER_DPI` (lower = faster)
    - `GEMINI_CONCURRENCY` (small parallelism helps; too high may 429)
    - `CHUNK_HEIGHT`, `CHUNK_OVERLAP` (fewer chunks = fewer model calls)
    - `SAVE_CHUNK_IMAGES`, `SAVE_RAW_CHUNKS` (keep off unless debugging)

- **Run**:

```bash
uvicorn main:app --reload
```

### API (v1)

- `POST /api/v1/documents/upload` (multipart form)
  - `file`: PDF
  - `pdf_password` (optional): password for encrypted PDFs
- `GET /api/v1/documents/{document_id}/status`
- `GET /api/v1/documents/{document_id}/pages/{page_number}/image`
- `GET /api/v1/documents/{document_id}/pages/{page_number}/table`
- `GET /api/v1/documents/{document_id}/table`
- `POST /api/v1/documents/{document_id}/export`

### Storage

Outputs are written under `STORAGE_DIR` (default `./storage`):
- `original.pdf`
- `pages/{n}.png`
- `chunks/page_{n}/chunk_{k}.png`
- `raw/page_{n}/chunk_{k}.txt` (Gemini raw output)
- `tables/page_{n}.json`, `tables/global.json`
- exports are generated on-demand


