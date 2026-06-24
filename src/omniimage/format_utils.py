from __future__ import annotations

from pathlib import Path

FORMAT_ALIASES = {
    "JPG": "JPEG",
    "JPE": "JPEG",
    "TIF": "TIFF",
    "HTM": "HTML",
    "HTML": "HTML",
}


def normalise_format(value: str) -> str:
    fmt = value.upper().strip().lstrip(".")
    return FORMAT_ALIASES.get(fmt, fmt)


def extension_to_format(path_or_extension: str | Path) -> str:
    extension = Path(path_or_extension).suffix if not str(path_or_extension).startswith(".") else str(path_or_extension)
    return normalise_format(extension.lstrip("."))


def safe_report_cell(value: object) -> str:
    """Return a CSV/spreadsheet-safe text cell.

    Spreadsheet apps can treat cells starting with =, +, -, or @ as formulae.
    Prefixing a quote prevents formula injection when opening reports.
    """
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in {"=", "+", "-", "@"} else text
