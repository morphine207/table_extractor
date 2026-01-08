from __future__ import annotations

from io import BytesIO
import pandas as pd


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_excel_bytes(df: pd.DataFrame, *, sheet_name: str = "Extracted") -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return bio.getvalue()


def to_excel_bytes_multi(sheets: dict[str, pd.DataFrame]) -> bytes:
    """
    Create an .xlsx with one sheet per key in `sheets`.
    Sheet names are truncated to Excel's 31-char limit.
    """
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for name, df in sheets.items():
            sheet_name = (name or "Sheet")[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    return bio.getvalue()


