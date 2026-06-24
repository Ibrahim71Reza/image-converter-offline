from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageSequence, UnidentifiedImageError

from .base import ConversionJob, ConversionOptions, ConversionResult, FormatInfo
from ..format_utils import normalise_format


# Friendly names for common Pillow format keys.
_FORMAT_LABELS = {
    "JPEG": "JPEG / JPG",
    "PNG": "PNG",
    "WEBP": "WebP",
    "BMP": "Bitmap / BMP",
    "TIFF": "TIFF",
    "GIF": "GIF",
    "ICO": "Windows Icon / ICO",
    "PPM": "Portable Pixmap / PPM",
    "PDF": "PDF",
    "TGA": "Targa / TGA",
    "DDS": "DirectDraw Surface / DDS",
    "EPS": "Encapsulated PostScript / EPS",
    "PCX": "PCX",
    "PSD": "Photoshop PSD",
    "MPO": "MPO",
    "XBM": "XBM",
}


class PillowBackend:
    """Common-format conversion backend using Pillow."""

    name = "Pillow"

    def __init__(self) -> None:
        Image.init()
        self._extension_to_format = {
            ext.lower(): fmt.upper() for ext, fmt in Image.registered_extensions().items()
        }
        self._read_formats = {fmt.upper() for fmt in Image.OPEN.keys()}
        self._write_formats = {fmt.upper() for fmt in Image.SAVE.keys()}
        self._formats = self._build_formats()

    def is_available(self) -> bool:
        return True

    def _build_formats(self) -> dict[str, FormatInfo]:
        grouped: dict[str, list[str]] = {}
        for ext, fmt in self._extension_to_format.items():
            grouped.setdefault(fmt, []).append(ext)

        formats: dict[str, FormatInfo] = {}
        for fmt, extensions in grouped.items():
            can_read = fmt in self._read_formats
            can_write = fmt in self._write_formats
            if not can_read and not can_write:
                continue
            ordered_ext = _ordered_extensions(fmt, extensions)
            formats[fmt] = FormatInfo(
                key=fmt,
                label=_FORMAT_LABELS.get(fmt, fmt),
                extensions=ordered_ext,
                can_read=can_read,
                can_write=can_write,
            )
        return formats

    def input_formats(self) -> Iterable[FormatInfo]:
        return sorted((f for f in self._formats.values() if f.can_read), key=lambda f: f.label)

    def output_formats(self) -> Iterable[FormatInfo]:
        return sorted((f for f in self._formats.values() if f.can_write), key=lambda f: f.label)

    def can_read(self, path: Path) -> bool:
        if path.suffix.lower() in self._extension_to_format:
            return True
        try:
            with Image.open(path) as img:
                return bool(img.format)
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            return False

    def can_write(self, target_format: str) -> bool:
        return normalise_format(target_format) in self._write_formats

    def supported_outputs_for(self, path: Path) -> Iterable[FormatInfo]:
        if not self.can_read(path):
            return []
        return self.output_formats()

    def convert(self, job: ConversionJob) -> ConversionResult:
        target_format = normalise_format(job.target_format)
        if not self.can_write(target_format):
            return ConversionResult(job.input_path, job.input_path, self.name, False, f"Pillow cannot write {job.target_format}.")

        output_path = job.output_path or _make_output_path(
            job.input_path, job.output_dir, self._formats[target_format].primary_extension, job.options.overwrite
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(job.input_path) as img:
                save_kwargs = _save_kwargs(img, target_format, job.options)

                if getattr(img, "is_animated", False) and job.options.preserve_animation and target_format in {"GIF", "WEBP", "TIFF"}:
                    frames = [_prepare_frame(frame.copy(), target_format, job.options) for frame in ImageSequence.Iterator(img)]
                    first, rest = frames[0], frames[1:]
                    first.save(
                        output_path,
                        format=target_format,
                        save_all=True,
                        append_images=rest,
                        duration=img.info.get("duration", 100),
                        loop=img.info.get("loop", 0),
                        **save_kwargs,
                    )
                else:
                    prepared = _prepare_frame(img.copy(), target_format, job.options)
                    prepared.save(output_path, format=target_format, **save_kwargs)

            return ConversionResult(job.input_path, output_path, self.name, True, "Converted successfully.")
        except Exception as exc:  # noqa: BLE001 - UI needs user-facing message.
            return ConversionResult(job.input_path, output_path, self.name, False, str(exc))

def _ordered_extensions(fmt: str, extensions: list[str]) -> tuple[str, ...]:
    preferred = {
        "JPEG": [".jpg", ".jpeg", ".jpe"],
        "TIFF": [".tif", ".tiff"],
    }
    unique = set(extensions)
    ordered: list[str] = []
    for ext in preferred.get(fmt, []):
        if ext in unique:
            ordered.append(ext)
            unique.remove(ext)
    ordered.extend(sorted(unique, key=lambda e: (len(e), e)))
    return tuple(ordered)


def _make_output_path(input_path: Path, output_dir: Path, extension: str, overwrite: bool) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate = output_dir / f"{input_path.stem}{extension}"
    if overwrite or not candidate.exists():
        return candidate
    index = 1
    while True:
        numbered = output_dir / f"{input_path.stem}_{index}{extension}"
        if not numbered.exists():
            return numbered
        index += 1


def _prepare_frame(image: Image.Image, target_format: str, options: ConversionOptions) -> Image.Image:
    # Formats such as JPEG and BMP do not support alpha. Composite on a configurable background.
    no_alpha_formats = {"JPEG", "BMP", "PPM"}
    if target_format in no_alpha_formats and image.mode in {"RGBA", "LA", "P"}:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, options.background)
        background.alpha_composite(rgba)
        return background.convert("RGB")

    if target_format == "JPEG" and image.mode not in {"RGB", "L"}:
        return image.convert("RGB")

    return image


def _save_kwargs(image: Image.Image, target_format: str, options: ConversionOptions) -> dict[str, object]:
    kwargs: dict[str, object] = {}
    quality_formats = {"JPEG", "WEBP", "AVIF", "HEIF"}
    if target_format in quality_formats:
        kwargs["quality"] = int(max(1, min(100, options.quality)))

    if target_format == "JPEG":
        kwargs["optimize"] = True
        kwargs["progressive"] = True

    if target_format == "PNG":
        kwargs["optimize"] = True

    if options.preserve_metadata:
        exif = image.info.get("exif")
        icc_profile = image.info.get("icc_profile")
        if exif and target_format in {"JPEG", "WEBP", "TIFF"}:
            kwargs["exif"] = exif
        if icc_profile and target_format in {"JPEG", "PNG", "WEBP", "TIFF"}:
            kwargs["icc_profile"] = icc_profile

    return kwargs
