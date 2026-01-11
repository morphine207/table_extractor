from __future__ import annotations

from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


class Settings(BaseModel):
    app_name: str = "table-extractor-backend"
    api_v1_prefix: str = "/api/v1"
    storage_dir: str = os.getenv("STORAGE_DIR", os.path.join(os.getcwd(), "storage"))
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    gemini_prompt: str = os.getenv(
        "GEMINI_PROMPT",
        "Extract table information from these images. Return all data, including headings, "
        "as pipe-delimited text. Remove lines containing '-----'. Do not add any extra text "
        "beyond the table data.",
    )

    # Biggest speed lever: DPI (override via env if needed).
    pdf_render_dpi: int = int(os.getenv("PDF_RENDER_DPI", "200"))

    # Chunking defaults (override as needed).
    # These are logical units before DPI scaling in the processor.
    default_chunk_height: int = int(os.getenv("CHUNK_HEIGHT", "700"))
    default_overlap: int = int(os.getenv("CHUNK_OVERLAP", "40"))

    # Concurrency for Gemini calls (keep small to avoid 429s).
    gemini_concurrency: int = int(os.getenv("GEMINI_CONCURRENCY", "3"))

    # Downscale chunk images before sending to Gemini (reduces upload + model work).
    max_chunk_width: int = int(os.getenv("MAX_CHUNK_WIDTH", "1600"))

    # Disk I/O controls (chunk images + raw text are expensive).
    save_page_images: bool = _env_bool("SAVE_PAGE_IMAGES", True)
    save_chunk_images: bool = _env_bool("SAVE_CHUNK_IMAGES", False)
    save_raw_chunks: bool = _env_bool("SAVE_RAW_CHUNKS", False)

    # Faster PNG writes (bigger files, but much less CPU).
    png_compress_level: int = int(os.getenv("PNG_COMPRESS_LEVEL", "1"))
    # Comma-separated list of allowed origins, e.g.:
    #   CORS_ALLOW_ORIGINS=https://<your-swa>.azurestaticapps.net,https://www.yourdomain.com
    cors_allow_origins: list[str] = (
        [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")]
        if os.getenv("CORS_ALLOW_ORIGINS")
        else ["*"]
    )


settings = Settings()


