from __future__ import annotations

from pathlib import Path
from typing import Iterable


def expand_input_paths(
    paths: Iterable[Path],
    recursive: bool = False,
    allowed_extensions: set[str] | None = None,
    include_unsupported_files: bool = True,
) -> list[Path]:
    """Expand file and directory inputs into a stable, de-duplicated file list.

    Explicit file inputs are always returned. For directory inputs, callers can
    pass `allowed_extensions` and set `include_unsupported_files=False` to avoid
    pulling README, JSON, CSV, or other non-image files into image batch jobs.
    """
    seen: set[Path] = set()
    files: list[Path] = []
    allowed = {ext.lower() for ext in allowed_extensions or set()}

    for raw_path in paths:
        path = raw_path.expanduser()
        path_is_dir = path.is_dir()
        if path_is_dir:
            iterator = path.rglob("*") if recursive else path.iterdir()
            candidates = sorted((candidate for candidate in iterator if candidate.is_file()), key=lambda p: str(p).lower())
        else:
            candidates = [path]

        for candidate in candidates:
            if path_is_dir and allowed and not include_unsupported_files and candidate.suffix.lower() not in allowed:
                continue
            resolved = candidate.resolve() if candidate.exists() else candidate.absolute()
            if resolved not in seen:
                seen.add(resolved)
                files.append(resolved)

    return files


def directory_source_roots(paths: Iterable[Path]) -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for raw_path in paths:
        path = raw_path.expanduser()
        if not path.is_dir():
            continue
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            roots.append(resolved)
    return roots
