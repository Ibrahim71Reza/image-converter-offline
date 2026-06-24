from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .backends import ImageMagickBackend, PillowBackend, RawPyBackend
from .backends.base import ConversionJob, ConversionOptions, ConversionResult, FormatInfo, ImageBackend
from .format_utils import normalise_format


@dataclass(frozen=True)
class BackendStatus:
    name: str
    available: bool
    readable_count: int
    writable_count: int


class ConverterService:
    """Facade that selects the best available backend per conversion."""

    def __init__(self, backends: list[ImageBackend] | None = None) -> None:
        # Preference order: rawpy for camera RAW fidelity, ImageMagick for maximum
        # coverage, Pillow for dependable built-in common formats and fallback.
        self.backends: list[ImageBackend] = backends or [RawPyBackend(), ImageMagickBackend(), PillowBackend()]

    def backend_statuses(self) -> list[BackendStatus]:
        statuses: list[BackendStatus] = []
        for backend in self.backends:
            available = backend.is_available()
            if available:
                readable = len(list(backend.input_formats()))
                writable = len(list(backend.output_formats()))
            else:
                readable = 0
                writable = 0
            statuses.append(BackendStatus(backend.name, available, readable, writable))
        return statuses

    def supported_inputs(self) -> list[FormatInfo]:
        return _dedupe_formats(fmt for backend in self.backends if backend.is_available() for fmt in backend.input_formats())

    def supported_input_extensions(self) -> set[str]:
        extensions: set[str] = set()
        for fmt in self.supported_inputs():
            extensions.update(ext.lower() for ext in fmt.extensions)
        return extensions

    def supported_outputs(self) -> list[FormatInfo]:
        return _dedupe_formats(fmt for backend in self.backends if backend.is_available() for fmt in backend.output_formats())

    def supported_outputs_for(self, input_path: Path) -> list[FormatInfo]:
        formats = []
        for backend in self.backends:
            if not backend.is_available():
                continue
            formats.extend(list(backend.supported_outputs_for(input_path)))
        return _dedupe_formats(formats)

    def supported_outputs_for_paths(self, input_paths: Iterable[Path]) -> list[FormatInfo]:
        """Return formats that every supplied input can be converted into.

        This prevents a mixed batch from showing a target that only works for the
        first file. If no paths are supplied, return the global output set.
        """
        paths = list(input_paths)
        if not paths:
            return self.supported_outputs()

        first = self.supported_outputs_for(paths[0])
        common_keys = {fmt.key for fmt in first}
        by_key = {fmt.key: fmt for fmt in first}
        for path in paths[1:]:
            keys = {fmt.key for fmt in self.supported_outputs_for(path)}
            common_keys &= keys
        return sorted((by_key[key] for key in common_keys), key=lambda f: f.label.lower())

    def choose_backend(self, input_path: Path, target_format: str) -> ImageBackend | None:
        target = normalise_format(target_format)
        for backend in self.backends:
            if backend.is_available() and backend.can_read(input_path) and backend.can_write(target):
                return backend
        return None

    def primary_extension_for(self, backend: ImageBackend | None, target_format: str) -> str:
        target = normalise_format(target_format)
        preferred_extensions = {"JPEG": ".jpg", "TIFF": ".tif"}
        if target in preferred_extensions:
            return preferred_extensions[target]
        if backend is not None and backend.is_available():
            for fmt in backend.output_formats():
                if normalise_format(fmt.key) == target:
                    return fmt.primary_extension
        for fmt in self.supported_outputs():
            if normalise_format(fmt.key) == target:
                return fmt.primary_extension
        return f".{target.lower()}"

    def convert_one(
        self,
        input_path: Path,
        output_dir: Path,
        target_format: str,
        options: ConversionOptions | None = None,
        output_path: Path | None = None,
    ) -> ConversionResult:
        started = time.perf_counter()
        input_path = input_path.expanduser().resolve()
        output_dir = output_dir.expanduser().resolve()
        if output_path is not None:
            output_path = output_path.expanduser().resolve()

        if not input_path.exists():
            return ConversionResult(input_path, output_path or output_dir, "None", False, "Input file does not exist.")
        if not input_path.is_file():
            return ConversionResult(input_path, output_path or output_dir, "None", False, "Input path is not a file.")

        backend = self.choose_backend(input_path, target_format)
        if output_path is None:
            extension = self.primary_extension_for(backend, target_format)
            output_path = _make_planned_output_path(
                input_path=input_path,
                output_dir=output_dir,
                extension=extension,
                overwrite=bool(options and options.overwrite),
                used_paths=set(),
            )

        if backend is None:
            return ConversionResult(
                input_path=input_path,
                output_path=output_path,
                backend_name="None",
                success=False,
                message=f"No available backend can convert this file to {normalise_format(target_format)}.",
                elapsed_seconds=time.perf_counter() - started,
            )

        job = ConversionJob(
            input_path=input_path,
            output_dir=output_dir,
            target_format=normalise_format(target_format),
            options=options or ConversionOptions(),
            output_path=output_path,
        )
        result = backend.convert(job)
        return ConversionResult(
            input_path=result.input_path,
            output_path=result.output_path,
            backend_name=result.backend_name,
            success=result.success,
            message=result.message,
            elapsed_seconds=time.perf_counter() - started,
        )

    def convert_batch(
        self,
        input_paths: Iterable[Path],
        output_dir: Path,
        target_format: str,
        options: ConversionOptions | None = None,
        fail_fast: bool = False,
        source_roots: Iterable[Path] | None = None,
        preserve_structure: bool = True,
    ) -> list[ConversionResult]:
        output_dir = output_dir.expanduser().resolve()
        options = options or ConversionOptions()
        roots = [_normalise_root(root) for root in (source_roots or [])]
        used_paths: set[Path] = set()
        results: list[ConversionResult] = []

        for path in input_paths:
            resolved = path.expanduser().resolve()
            backend = self.choose_backend(resolved, target_format)
            extension = self.primary_extension_for(backend, target_format)
            planned_output = _make_planned_output_path(
                input_path=resolved,
                output_dir=output_dir,
                extension=extension,
                overwrite=options.overwrite,
                used_paths=used_paths,
                source_roots=roots,
                preserve_structure=preserve_structure,
            )
            used_paths.add(planned_output)

            result = self.convert_one(resolved, output_dir, target_format, options, output_path=planned_output)
            results.append(result)
            if fail_fast and not result.success:
                break
        return results


def _dedupe_formats(formats: Iterable[FormatInfo]) -> list[FormatInfo]:
    by_key: dict[str, FormatInfo] = {}
    for fmt in formats:
        key = normalise_format(fmt.key)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = FormatInfo(
                key=key,
                label=fmt.label,
                extensions=fmt.extensions,
                can_read=fmt.can_read,
                can_write=fmt.can_write,
            )
            continue

        extensions = tuple(sorted(set(existing.extensions + fmt.extensions), key=lambda e: (len(e), e)))
        by_key[key] = FormatInfo(
            key=existing.key,
            label=existing.label if len(existing.label) <= len(fmt.label) else fmt.label,
            extensions=extensions,
            can_read=existing.can_read or fmt.can_read,
            can_write=existing.can_write or fmt.can_write,
        )
    return sorted(by_key.values(), key=lambda f: f.label.lower())


def _normalise_root(root: Path) -> Path:
    return root.expanduser().resolve()


def _relative_parent_for(input_path: Path, source_roots: Iterable[Path]) -> Path:
    for root in sorted(source_roots, key=lambda p: len(str(p)), reverse=True):
        try:
            return input_path.relative_to(root).parent
        except ValueError:
            continue
    return Path()


def _make_planned_output_path(
    input_path: Path,
    output_dir: Path,
    extension: str,
    overwrite: bool,
    used_paths: set[Path],
    source_roots: Iterable[Path] | None = None,
    preserve_structure: bool = False,
) -> Path:
    """Create a collision-safe output path for one conversion.

    The first output uses the clean stem, e.g. `photo.png`. If another file in
    the same batch would produce the same output path, a source-extension suffix
    is added, e.g. `photo__from_jpg.png`. Existing files are overwritten only
    when the user explicitly allowed overwrite and the path has not already been
    used in the current batch.
    """
    extension = extension if extension.startswith(".") else f".{extension}"
    relative_parent = _relative_parent_for(input_path, source_roots or []) if preserve_structure else Path()
    target_dir = (output_dir / relative_parent).resolve()
    base = input_path.stem
    candidate = (target_dir / f"{base}{extension}").resolve()

    if candidate in used_paths:
        source_ext = input_path.suffix.lower().lstrip(".") or "source"
        candidate = (target_dir / f"{base}__from_{source_ext}{extension}").resolve()

    if candidate not in used_paths and (overwrite or not candidate.exists()):
        return candidate

    index = 1
    stem = candidate.stem
    while True:
        numbered = (candidate.parent / f"{stem}_{index}{candidate.suffix}").resolve()
        if numbered not in used_paths and (overwrite or not numbered.exists()):
            return numbered
        index += 1
