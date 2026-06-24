from pathlib import Path

from PIL import Image

from omniimage.cli import main


def test_cli_list_backends_without_inputs(capsys) -> None:
    assert main(["--list-backends"]) == 0
    output = capsys.readouterr().out
    assert "Pillow" in output


def test_cli_conversion_and_report(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    outdir = tmp_path / "out"
    report = tmp_path / "report.csv"
    Image.new("RGB", (10, 10), "white").save(source)

    assert main([str(source), "--target", "jpg", "--output-dir", str(outdir), "--report", str(report)]) == 0
    assert any(path.suffix.lower() in {".jpg", ".jpeg"} for path in outdir.iterdir())
    assert report.exists()
    assert "success,input_path,output_path,backend,message,elapsed_seconds" in report.read_text(encoding="utf-8")
