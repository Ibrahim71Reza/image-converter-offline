from __future__ import annotations

import csv
from pathlib import Path

from .backends.base import ConversionResult
from .format_utils import safe_report_cell


def write_csv_report(path: Path, results: list[ConversionResult]) -> Path:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["success", "input_path", "output_path", "backend", "message", "elapsed_seconds"])
        for result in results:
            writer.writerow(
                [
                    "yes" if result.success else "no",
                    safe_report_cell(result.input_path),
                    safe_report_cell(result.output_path),
                    safe_report_cell(result.backend_name),
                    safe_report_cell(result.message),
                    f"{result.elapsed_seconds:.3f}",
                ]
            )
    return path
