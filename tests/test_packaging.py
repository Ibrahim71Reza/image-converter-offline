from pathlib import Path


def test_pyinstaller_entry_uses_package_import() -> None:
    entry = Path("packaging/pyinstaller_entry.py")
    assert entry.exists()
    text = entry.read_text(encoding="utf-8")
    assert "from omniimage.main import main" in text
    assert "from ." not in text


def test_windows_build_uses_pyinstaller_entry_wrapper() -> None:
    script = Path("scripts/build_windows.ps1").read_text(encoding="utf-8")
    assert "packaging/pyinstaller_entry.py" in script
    assert "src/omniimage/main.py" not in script
