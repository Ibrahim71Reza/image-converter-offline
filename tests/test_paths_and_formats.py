from pathlib import Path

from PIL import Image

from omniimage.backends.base import ConversionOptions
from omniimage.backends.imagemagick_backend import _parse_magick_format_list
from omniimage.converter import ConverterService
from omniimage.file_discovery import expand_input_paths
from omniimage.format_utils import normalise_format, safe_report_cell


def test_format_aliases() -> None:
    assert normalise_format("jpg") == "JPEG"
    assert normalise_format(".tif") == "TIFF"
    assert normalise_format("png") == "PNG"


def test_non_overwrite_creates_numbered_file(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    outdir = tmp_path / "out"
    outdir.mkdir()
    existing = outdir / "source.jpg"
    Image.new("RGB", (8, 8), "white").save(source)
    existing.write_bytes(b"do-not-overwrite")

    service = ConverterService()
    result = service.convert_one(source, outdir, "jpg", ConversionOptions(overwrite=False))

    assert result.success, result.message
    assert result.output_path.name == "source_1.jpg"
    assert existing.read_bytes() == b"do-not-overwrite"


def test_expand_input_paths_recursive(tmp_path: Path) -> None:
    root = tmp_path / "input"
    nested = root / "nested"
    nested.mkdir(parents=True)
    a = root / "a.png"
    b = nested / "b.png"
    a.write_bytes(b"a")
    b.write_bytes(b"b")

    assert expand_input_paths([root], recursive=False) == [a.resolve()]
    assert expand_input_paths([root], recursive=True) == [a.resolve(), b.resolve()]


def test_csv_formula_cells_are_escaped() -> None:
    assert safe_report_cell("=HYPERLINK('x')").startswith("'")
    assert safe_report_cell("normal") == "normal"


def test_parse_imagemagick_format_list() -> None:
    output = """
   Format  Module    Mode  Description
-------------------------------------------------------------------------------
      PNG* PNG       rw-   Portable Network Graphics
     JPEG* JPEG      rw-   Joint Photographic Experts Group JFIF format
      HEIC HEIC      rw+   High Efficiency Image Format
"""
    formats = _parse_magick_format_list(output)

    assert formats["PNG"].can_read is True
    assert formats["PNG"].can_write is True
    assert formats["JPEG"].primary_extension == ".jpg"
    assert formats["HEIC"].can_write is True
