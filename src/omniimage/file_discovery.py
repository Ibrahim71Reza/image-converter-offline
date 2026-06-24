from __future__ import annotations

from pathlib import Path
from typing import Iterable


def expand_input_paths(paths: Iterable[Path], recursive: bool = False) -> list[Path]:
    """Expand file and directory inputs into a stable, de-duplicated file list."""
    seen: set[Path] = set()
    files: list[Path] = []

    for raw_path in paths:
        path = raw_path.expanduser()
        if path.is_dir():
            iterator = path.rglob("*") if recursive else path.iterdir()
            candidates = sorted((candidate for candidate in iterator if candidate.is_file()), key=lambda p: str(p).lower())
        else:
            candidates = [path]

        for candidate in candidates:
            resolved = candidate.resolve() if candidate.exists() else candidate.absolute()
            if resolved not in seen:
                seen.add(resolved)
                files.append(resolved)

    return files
