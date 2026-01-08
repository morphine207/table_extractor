from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
import threading


DocumentState = Literal["queued", "processing", "completed", "failed"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ProgressState:
    document_id: str
    state: DocumentState = "queued"
    progress: int = 0
    current_page: int | None = None
    current_chunk: int | None = None
    total_pages: int | None = None
    total_chunks: int | None = None
    message: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


class InMemoryProgressStore:
    """
    Simple single-process progress store.
    Replace with Redis/Postgres for multi-worker / multi-instance deployments.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._data: dict[str, ProgressState] = {}

    def create(self, document_id: str, *, total_pages: int | None = None) -> ProgressState:
        with self._lock:
            state = ProgressState(document_id=document_id, total_pages=total_pages)
            self._data[document_id] = state
            return state

    def get(self, document_id: str) -> ProgressState | None:
        with self._lock:
            return self._data.get(document_id)

    def update(self, document_id: str, **kwargs) -> ProgressState:
        with self._lock:
            state = self._data[document_id]
            for k, v in kwargs.items():
                setattr(state, k, v)
            state.updated_at = utcnow()
            self._data[document_id] = state
            return state


