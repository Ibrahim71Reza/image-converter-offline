from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol


@dataclass(frozen=True, order=True)
class FormatInfo:
    """A single image format exposed by a conversion backend."""

    key: str
    label: str
    extensions: tuple[str, ...]
    can_read: bool = True
    can_write: bool = True

    @property
    def primary_extension(self) -> str:
        return self.extensions[0] if self.extensions else f".{self.key.lower()}"


@dataclass(frozen=True)
class ConversionOptions:
    """User-selectable options for output conversion."""

    quality: int = 92
    overwrite: bool = False
    preserve_metadata: bool = True
    preserve_animation: bool = True
    background: str = "white"


@dataclass(frozen=True)
class ConversionJob:
    input_path: Path
    output_dir: Path
    target_format: str
    options: ConversionOptions = ConversionOptions()


@dataclass(frozen=True)
class ConversionResult:
    input_path: Path
    output_path: Path
    backend_name: str
    success: bool
    message: str = ""
    elapsed_seconds: float = 0.0


class ImageBackend(Protocol):
    name: str

    def is_available(self) -> bool:
        ...

    def input_formats(self) -> Iterable[FormatInfo]:
        ...

    def output_formats(self) -> Iterable[FormatInfo]:
        ...

    def can_read(self, path: Path) -> bool:
        ...

    def can_write(self, target_format: str) -> bool:
        ...

    def supported_outputs_for(self, path: Path) -> Iterable[FormatInfo]:
        ...

    def convert(self, job: ConversionJob) -> ConversionResult:
        ...
