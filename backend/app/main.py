from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    allow_credentials = True
    if settings.cors_allow_origins == ["*"]:
        # Starlette disallows allow_credentials=True with wildcard origins.
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()


