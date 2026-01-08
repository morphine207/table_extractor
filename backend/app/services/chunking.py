from __future__ import annotations

from dataclasses import dataclass
from PIL import Image


@dataclass(frozen=True)
class ImageChunk:
    chunk_index: int
    top: int
    bottom: int
    left: int
    right: int
    image: Image.Image


def iter_vertical_chunks(
    page_image: Image.Image,
    *,
    chunk_height: int = 500,
    overlap: int = 50,
) -> list[ImageChunk]:
    """
    Matches the existing Streamlit logic:
    - fixed chunk height (default 500px)
    - overlap (default 50px)
    """
    width, height = page_image.size
    chunks: list[ImageChunk] = []

    chunk_idx = 0
    y = 0
    while y < height:
        top = max(0, y - (overlap if chunk_idx > 0 else 0))
        bottom = min(height, y + chunk_height + overlap)
        left = 0
        right = width
        chunk_img = page_image.crop((left, top, right, bottom))
        chunks.append(
            ImageChunk(
                chunk_index=chunk_idx + 1,
                top=top,
                bottom=bottom,
                left=left,
                right=right,
                image=chunk_img,
            )
        )
        chunk_idx += 1
        y += chunk_height

    return chunks


