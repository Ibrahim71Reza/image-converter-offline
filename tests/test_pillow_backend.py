from pathlib import Path

from PIL import Image

from omniimage.backends.base import ConversionOptions
from omniimage.converter import ConverterService


def test_png_to_jpeg_conversion(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    outdir = tmp_path / "out"
    Image.new("RGBA", (16, 16), (255, 0, 0, 128)).save(source)

    service = ConverterService()
    result = service.convert_one(source, outdir, "jpg", ConversionOptions(overwrite=True))

    assert result.success, result.message
    assert result.output_path.exists()
    assert result.output_path.suffix.lower() in {".jpg", ".jpeg"}
    with Image.open(result.output_path) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"


def test_supported_outputs_are_available_for_png(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (10, 10), "white").save(source)

    service = ConverterService()
    outputs = {fmt.key for fmt in service.supported_outputs_for(source)}

    assert "JPEG" in outputs
    assert "PNG" in outputs
