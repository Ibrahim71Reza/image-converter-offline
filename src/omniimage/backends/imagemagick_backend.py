from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from .base import ConversionJob, ConversionResult, FormatInfo
from .pillow_backend import _make_output_path
from ..format_utils import normalise_format


class ImageMagickBackend:
    """Wide-format backend powered by ImageMagick's `magick` executable.

    The app remains fully offline. For public releases, bundle ImageMagick inside
    vendor/imagemagick/ or ship a platform-specific app package that includes it.
    """

    name = "ImageMagick"

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or self._find_magick()
        self._formats: dict[str, FormatInfo] | None = None

    def is_available(self) -> bool:
        return self.executable is not None

    def input_formats(self) -> Iterable[FormatInfo]:
        return sorted((f for f in self._load_formats().values() if f.can_read), key=lambda f: f.label)

    def output_formats(self) -> Iterable[FormatInfo]:
        return sorted((f for f in self._load_formats().values() if f.can_write), key=lambda f: f.label)

    def can_read(self, path: Path) -> bool:
        if not self.is_available():
            return False
        fmt = self._format_from_extension(path.suffix)
        return bool(fmt and fmt in {f.key for f in self.input_formats()})

    def can_write(self, target_format: str) -> bool:
        if not self.is_available():
            return False
        fmt = normalise_format(target_format)
        return fmt in {f.key for f in self.output_formats()}

    def supported_outputs_for(self, path: Path) -> Iterable[FormatInfo]:
        if not self.can_read(path):
            return []
        return self.output_formats()

    def convert(self, job: ConversionJob) -> ConversionResult:
        if not self.executable:
            return ConversionResult(job.input_path, job.input_path, self.name, False, "ImageMagick executable was not found.")

        target_format = normalise_format(job.target_format)
        format_info = self._load_formats().get(target_format)
        if not format_info or not format_info.can_write:
            return ConversionResult(job.input_path, job.input_path, self.name, False, f"ImageMagick cannot write {target_format}.")

        output_path = job.output_path or _make_output_path(job.input_path, job.output_dir, format_info.primary_extension, job.options.overwrite)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.executable,
            str(job.input_path),
            "-auto-orient",
        ]

        if not job.options.preserve_metadata:
            cmd.append("-strip")

        if target_format in {"JPEG", "JPG", "WEBP", "AVIF", "HEIC", "HEIF"}:
            cmd.extend(["-quality", str(max(1, min(100, int(job.options.quality))))])

        # JPEG cannot store transparency; composite on the requested background.
        if target_format in {"JPEG", "JPG"}:
            cmd.extend(["-background", job.options.background, "-alpha", "remove", "-alpha", "off"])

        cmd.append(f"{target_format}:{output_path}")

        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                message = (completed.stderr or completed.stdout or "ImageMagick failed.").strip()
                return ConversionResult(job.input_path, output_path, self.name, False, message)
            return ConversionResult(job.input_path, output_path, self.name, True, "Converted successfully.")
        except Exception as exc:  # noqa: BLE001
            return ConversionResult(job.input_path, output_path, self.name, False, str(exc))

    def _load_formats(self) -> dict[str, FormatInfo]:
        if self._formats is not None:
            return self._formats

        if not self.executable:
            self._formats = {}
            return self._formats

        completed = subprocess.run(
            [self.executable, "-list", "format"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            self._formats = {}
            return self._formats

        self._formats = _parse_magick_format_list(completed.stdout)
        return self._formats

    @staticmethod
    def _format_from_extension(extension: str) -> str:
        return normalise_format(extension)

    @staticmethod
    def _find_magick() -> str | None:
        env_path = os.environ.get("OMNIIMAGE_MAGICK")
        if env_path and Path(env_path).exists():
            return env_path

        bundled = _bundled_magick_candidates()
        for candidate in bundled:
            if candidate.exists():
                return str(candidate)

        return shutil.which("magick") or shutil.which("convert")


def _bundled_magick_candidates() -> list[Path]:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
    names = ["magick.exe", "magick", "convert"]
    return [root / "vendor" / "imagemagick" / name for name in names]


def _parse_magick_format_list(output: str) -> dict[str, FormatInfo]:
    """Parse `magick -list format` output.

    Example meaningful line shape:
        PNG* PNG       rw-   Portable Network Graphics
        HEIC  HEIC      rw+   High Efficiency Image Format
    """
    formats: dict[str, FormatInfo] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("---") or line.startswith("Format"):
            continue
        # ImageMagick 7 commonly prints either:
        #   PNG* PNG       rw-   Portable Network Graphics
        # or:
        #   PNG* rw-       Portable Network Graphics
        match = re.match(
            r"^(?P<name>[A-Za-z0-9_+.-]+)\*?\s+(?:(?P<module>\S+)\s+)?(?P<mode>[rRwW+-]{2,4})\s*(?P<desc>.*)$",
            line,
        )
        if not match:
            continue

        key = match.group("name").upper().lstrip("*")
        mode = match.group("mode").lower()
        desc = match.group("desc").strip() or key
        can_read = "r" in mode
        can_write = "w" in mode
        extension = ".jpg" if key == "JPEG" else f".{key.lower()}"

        formats[key] = FormatInfo(
            key=key,
            label=f"{key} — {desc}" if desc != key else key,
            extensions=(extension,),
            can_read=can_read,
            can_write=can_write,
        )

    return formats
