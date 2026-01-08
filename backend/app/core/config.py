from __future__ import annotations

from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    app_name: str = "table-extractor-backend"
    api_v1_prefix: str = "/api/v1"
    storage_dir: str = os.getenv("STORAGE_DIR", os.path.join(os.getcwd(), "storage"))
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    pdf_render_dpi: int = int(os.getenv("PDF_RENDER_DPI", "300"))
    cors_allow_origins: list[str] = (
        [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")]
        if os.getenv("CORS_ALLOW_ORIGINS")
        else ["*"]
    )


settings = Settings()


