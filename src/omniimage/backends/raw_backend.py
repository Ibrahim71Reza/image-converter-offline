from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image

from .base import ConversionJob, ConversionResult, FormatInfo
from .pillow_backend import _make_output_path, _prepare_frame, _save_kwargs
from ..format_utils import normalise_format

RAW_EXTENSIONS = (
    ".3fr", ".ari", ".arw", ".bay", ".braw", ".cr2", ".cr3", ".crw", ".dcr", ".dng",
    ".erf", ".fff", ".iiq", ".k25", ".kdc", ".mdc", ".mef", ".mos", ".mrw", ".nef",
    ".nrw", ".orf", ".pef", ".raf", ".raw", ".rw2", ".rwl", ".sr2", ".srf", ".srw",
)

OUTPUT_FORMATS = {
    "JPEG": FormatInfo("JPEG", "JPEG / JPG", (".jpg", ".jpeg"), can_read=False, can_write=True),
    "PNG": FormatInfo("PNG", "PNG", (".png",), can_read=False, can_write=True),
    "TIFF": FormatInfo("TIFF", "TIFF", (".tif", ".tiff"), can_read=False, can_write=True),
    "WEBP": FormatInfo("WEBP", "WebP", (".webp",), can_read=False, can_write=True),
}


class RawPyBackend:
    """Camera RAW import backend. Requires optional dependency: rawpy + numpy."""

    name = "rawpy"

    def __init__(self) -> None:
        try:
            import rawpy  # noqa: F401
            import numpy  # noqa: F401
            self._available = True
        except Exception:  # noqa: BLE001
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def input_formats(self) -> Iterable[FormatInfo]:
        return [FormatInfo("RAW", "Camera RAW", RAW_EXTENSIONS, can_read=True, can_write=False)]

    def output_formats(self) -> Iterable[FormatInfo]:
        return sorted(OUTPUT_FORMATS.values(), key=lambda f: f.label)

    def can_read(self, path: Path) -> bool:
        return self.is_available() and path.suffix.lower() in RAW_EXTENSIONS

    def can_write(self, target_format: str) -> bool:
        return normalise_format(target_format) in OUTPUT_FORMATS

    def supported_outputs_for(self, path: Path) -> Iterable[FormatInfo]:
        if not self.can_read(path):
            return []
        return self.output_formats()

    def convert(self, job: ConversionJob) -> ConversionResult:
        if not self.is_available():
            return ConversionResult(job.input_path, job.input_path, self.name, False, "rawpy is not installed.")

        target_format = normalise_format(job.target_format)
        info = OUTPUT_FORMATS.get(target_format)
        if not info:
            return ConversionResult(job.input_path, job.input_path, self.name, False, f"rawpy cannot write {target_format}.")

        output_path = _make_output_path(job.input_path, job.output_dir, info.primary_extension, job.options.overwrite)
        try:
            import rawpy
            import numpy as np

            with rawpy.imread(str(job.input_path)) as raw:
                rgb = raw.postprocess()
            image = Image.fromarray(np.asarray(rgb))
            prepared = _prepare_frame(image, target_format, job.options)
            prepared.save(output_path, format=target_format, **_save_kwargs(prepared, target_format, job.options))
            return ConversionResult(job.input_path, output_path, self.name, True, "Converted successfully.")
        except Exception as exc:  # noqa: BLE001
            return ConversionResult(job.input_path, output_path, self.name, False, str(exc))
