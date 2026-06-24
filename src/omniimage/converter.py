from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .backends import ImageMagickBackend, PillowBackend, RawPyBackend
from .backends.base import ConversionJob, ConversionOptions, ConversionResult, FormatInfo, ImageBackend


@dataclass(frozen=True)
class BackendStatus:
    name: str
    available: bool
    readable_count: int
    writable_count: int


class ConverterService:
    """Facade that selects the best available backend per conversion."""

    def __init__(self, backends: list[ImageBackend] | None = None) -> None:
        # Preference order: ImageMagick for maximum coverage, rawpy for camera RAW,
        # Pillow for dependable built-in common formats.
        self.backends: list[ImageBackend] = backends or [ImageMagickBackend(), RawPyBackend(), PillowBackend()]

    def backend_statuses(self) -> list[BackendStatus]:
        statuses: list[BackendStatus] = []
        for backend in self.backends:
            if backend.is_available():
                readable = len(list(backend.input_formats()))
                writable = len(list(backend.output_formats()))
            else:
                readable = 0
                writable = 0
            statuses.append(BackendStatus(backend.name, backend.is_available(), readable, writable))
        return statuses

    def supported_inputs(self) -> list[FormatInfo]:
        return _dedupe_formats(fmt for backend in self.backends if backend.is_available() for fmt in backend.input_formats())

    def supported_outputs(self) -> list[FormatInfo]:
        return _dedupe_formats(fmt for backend in self.backends if backend.is_available() for fmt in backend.output_formats())

    def supported_outputs_for(self, input_path: Path) -> list[FormatInfo]:
        formats = []
        for backend in self.backends:
            if not backend.is_available():
                continue
            formats.extend(list(backend.supported_outputs_for(input_path)))
        return _dedupe_formats(formats)

    def choose_backend(self, input_path: Path, target_format: str) -> ImageBackend | None:
        target = _normalise_format(target_format)
        for backend in self.backends:
            if backend.is_available() and backend.can_read(input_path) and backend.can_write(target):
                return backend
        return None

    def convert_one(
        self,
        input_path: Path,
        output_dir: Path,
        target_format: str,
        options: ConversionOptions | None = None,
    ) -> ConversionResult:
        input_path = input_path.expanduser().resolve()
        output_dir = output_dir.expanduser().resolve()
        if not input_path.exists():
            return ConversionResult(input_path, output_dir, "None", False, "Input file does not exist.")
        if not input_path.is_file():
            return ConversionResult(input_path, output_dir, "None", False, "Input path is not a file.")

        backend = self.choose_backend(input_path, target_format)
        if backend is None:
            return ConversionResult(
                input_path=input_path,
                output_path=output_dir / input_path.name,
                backend_name="None",
                success=False,
                message=f"No available backend can convert this file to {_normalise_format(target_format)}.",
            )

        job = ConversionJob(input_path=input_path, output_dir=output_dir, target_format=_normalise_format(target_format), options=options or ConversionOptions())
        return backend.convert(job)

    def convert_batch(
        self,
        input_paths: Iterable[Path],
        output_dir: Path,
        target_format: str,
        options: ConversionOptions | None = None,
    ) -> list[ConversionResult]:
        return [self.convert_one(path, output_dir, target_format, options) for path in input_paths]


def _normalise_format(value: str) -> str:
    fmt = value.upper().lstrip(".")
    if fmt == "JPG":
        return "JPEG"
    return fmt


def _dedupe_formats(formats: Iterable[FormatInfo]) -> list[FormatInfo]:
    by_key: dict[str, FormatInfo] = {}
    for fmt in formats:
        key = _normalise_format(fmt.key)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = fmt
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
