from __future__ import annotations

import asyncio
from PIL import Image


DEFAULT_PROMPT = (
    "Extract table information from these images. Return all data, including headings, "
    "as pipe-delimited text. Remove lines containing '-----'. Do not add any extra text "
    "beyond the table data."
)


class GeminiClient:
    def __init__(self, *, api_key: str, model_name: str):
        # Prefer the new SDK to avoid the deprecation warning:
        # - google-genai: import google.genai as genai
        # Fallback only if needed:
        # - google-generativeai: import google.generativeai as genai
        self._genai = None
        self._model = None
        self._client = None
        self._model_name = model_name

        try:
            import google.genai as genai  # type: ignore
        except Exception:  # pragma: no cover
            import google.generativeai as genai  # type: ignore

        self._genai = genai

        # Handle both API shapes:
        # - genai.configure + genai.GenerativeModel (legacy-compatible)
        # - genai.Client (newer client style)
        if hasattr(genai, "configure") and hasattr(genai, "GenerativeModel"):
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(model_name)
        elif hasattr(genai, "Client"):
            self._client = genai.Client(api_key=api_key)
        else:  # pragma: no cover
            raise RuntimeError("Unsupported Gemini SDK. Please install 'google-genai'.")

    async def extract_table_text(self, image: Image.Image, *, prompt: str = DEFAULT_PROMPT) -> str:
        """
        Run model call in a worker thread to avoid blocking the event loop.
        """

        def _call() -> str:
            if self._model is not None:
                resp = self._model.generate_content([prompt, image])
                return getattr(resp, "text", "") or ""
            # Client-style fallback (best-effort)
            resp = self._client.models.generate_content(  # type: ignore[union-attr]
                model=self._model_name,
                contents=[prompt, image],
            )
            return getattr(resp, "text", "") or ""

        return await asyncio.to_thread(_call)


