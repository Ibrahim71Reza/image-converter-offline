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


def test_cli_report_without_path_writes_to_output_dir(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    outdir = tmp_path / "out"
    Image.new("RGB", (10, 10), "white").save(source)

    assert main([str(source), "--target", "jpg", "--output-dir", str(outdir), "--report"]) == 0
    assert (outdir / "conversion_report.csv").exists()


def test_cli_skips_folder_non_images_by_default(tmp_path: Path) -> None:
    root = tmp_path / "input"
    outdir = tmp_path / "out"
    root.mkdir()
    Image.new("RGB", (10, 10), "white").save(root / "source.png")
    (root / "README.md").write_text("not image", encoding="utf-8")

    assert main([str(root), "--target", "jpg", "--output-dir", str(outdir), "--report"]) == 0
    report = (outdir / "conversion_report.csv").read_text(encoding="utf-8")
    assert "source.png" in report
    assert "README.md" not in report
