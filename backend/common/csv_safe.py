from __future__ import annotations

from typing import Any


CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


def csv_safe_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in CSV_FORMULA_PREFIXES:
        return f"'{text}"
    return text


def spreadsheet_safe_value(value: Any) -> Any:
    if isinstance(value, str) and value and value[0] in CSV_FORMULA_PREFIXES:
        return f"'{value}"
    return value
