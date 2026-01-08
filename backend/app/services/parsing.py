from __future__ import annotations

from typing import Iterable


def parse_extracted_text(text: str, *, delimiter: str = "|") -> list[list[str]]:
    """
    Parse Gemini pipe-delimited table output into rows.
    - Removes lines containing '-----'
    - Ignores empty lines
    - Trims outer delimiter cells (e.g. '| a | b |' -> ['a','b'])
    """
    rows: list[list[str]] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "-----" in line:
            continue

        parts = [p.strip() for p in line.split(delimiter)]
        # If the model wraps lines like: | a | b |
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]

        if not parts:
            continue
        rows.append(parts)

    return rows


def adjust_table_rows(header: list[str], rows: Iterable[list[str]]) -> list[list[str]]:
    """
    Adjust each row so that it matches the header length.
    If a row has extra columns, trim them; if it has fewer, pad with empty strings.
    """
    adjusted: list[list[str]] = []
    num_cols = len(header)
    for row in rows:
        r = list(row)
        if len(r) > num_cols:
            r = r[:num_cols]
        elif len(r) < num_cols:
            r = r + [""] * (num_cols - len(r))
        adjusted.append(r)
    return adjusted


def row_confidence(row: list[str]) -> float:
    """
    Deterministic heuristic confidence (0..1) based on completeness.
    This is a placeholder until the pipeline produces model-provided confidences.
    """
    if not row:
        return 0.0
    non_empty = sum(1 for c in row if str(c).strip() != "")
    return max(0.0, min(1.0, non_empty / max(1, len(row))))


def dedupe_consecutive_rows(rows: list[list[str]]) -> list[list[str]]:
    """
    Removes exact consecutive duplicates (common with overlap chunking).
    """
    out: list[list[str]] = []
    last: list[str] | None = None
    for r in rows:
        normalized = [c.strip() for c in r]
        if last is not None and normalized == last:
            continue
        out.append(r)
        last = normalized
    return out


