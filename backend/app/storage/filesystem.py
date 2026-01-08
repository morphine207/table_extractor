from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentPaths:
    root: str
    pdf_path: str
    pages_dir: str
    chunks_dir: str
    tables_dir: str
    raw_dir: str
    exports_dir: str


class FilesystemStorage:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def document_paths(self, document_id: str) -> DocumentPaths:
        root = os.path.join(self.base_dir, document_id)
        pdf_path = os.path.join(root, "original.pdf")
        pages_dir = os.path.join(root, "pages")
        chunks_dir = os.path.join(root, "chunks")
        tables_dir = os.path.join(root, "tables")
        raw_dir = os.path.join(root, "raw")
        exports_dir = os.path.join(root, "exports")

        for d in (root, pages_dir, chunks_dir, tables_dir, raw_dir, exports_dir):
            os.makedirs(d, exist_ok=True)

        return DocumentPaths(
            root=root,
            pdf_path=pdf_path,
            pages_dir=pages_dir,
            chunks_dir=chunks_dir,
            tables_dir=tables_dir,
            raw_dir=raw_dir,
            exports_dir=exports_dir,
        )


