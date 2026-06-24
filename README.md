# OmniImage Converter

OmniImage Converter is a portable offline desktop application for batch image conversion.

The app is designed around a realistic professional principle: no single library can guarantee every image format ever created, so the converter uses multiple backends and a plugin-style architecture.

- **Pillow backend**: dependable built-in path for common formats such as PNG, JPEG, WebP, BMP, TIFF, GIF, ICO and more.
- **ImageMagick backend**: wide-format engine for public releases. Bundle ImageMagick into `vendor/imagemagick/` or install it on the target machine.
- **rawpy backend**: optional camera RAW importer for formats such as DNG, NEF, CR2, ARW, RAF and others.

## Current features

- Offline desktop GUI
- Drag-and-drop image list
- Batch conversion
- Dynamic target-format list based on available backends
- Quality control for lossy output
- Preserve metadata when possible
- Preserve animation when possible
- Alpha handling for JPEG output
- Non-overwrite mode with automatic numbered filenames
- CLI for automation and testing
- Local Git-ready structure
- PyInstaller packaging scripts for portable releases

## Why “all image conversions on earth” cannot be promised literally

Some formats are proprietary, obsolete, undocumented, patent/licence restricted, platform-specific, or require external delegates such as Ghostscript or camera vendor SDKs. This project handles that professionally by:

1. shipping strong default coverage,
2. using ImageMagick for maximum broad-format support,
3. exposing only conversions supported by the installed/bundled backends,
4. allowing new format backends to be added without rewriting the app.

## Install for development

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e .[full,dev,build]
```

## Run desktop app

```bash
omniimage
```

or:

```bash
python -m omniimage.main
```

## Run CLI

```bash
omniimage-cli sample.png --target jpg --output-dir converted
```

Check backend status:

```bash
omniimage-cli --list-backends sample.png --target png
```

## Bundle ImageMagick for maximum offline coverage

For a global publishable release, include the platform-specific ImageMagick binary in:

```text
vendor/imagemagick/
```

Expected executable names:

- Windows: `vendor/imagemagick/magick.exe`
- macOS/Linux: `vendor/imagemagick/magick`

You can also set this environment variable during development:

```bash
OMNIIMAGE_MAGICK=/absolute/path/to/magick
```

## Build portable app

### Windows

```powershell
scripts\build_windows.ps1
```

### macOS/Linux

```bash
bash scripts/build_unix.sh
```

Build output will be created under `dist/`.

## Release checklist for a serious public app

- Bundle ImageMagick per platform.
- Test conversions across at least: PNG, JPEG, WebP, TIFF, BMP, GIF, ICO, HEIC/HEIF, AVIF, SVG, PDF, EPS, PSD, camera RAW.
- Confirm licenses for every bundled binary and codec.
- Sign Windows/macOS releases.
- Add crash logging and update checks only if they respect offline mode.
- Add automated CI builds for Windows, macOS, and Linux.

## Project structure

```text
src/omniimage/
  app.py                         # PySide6 desktop UI
  cli.py                         # CLI entry point
  converter.py                   # backend selection and batch service
  backends/
    base.py                      # backend protocol and data models
    pillow_backend.py            # common image conversion
    imagemagick_backend.py       # wide-format ImageMagick conversion
    raw_backend.py               # optional camera RAW support
scripts/
  build_windows.ps1
  build_unix.sh
packaging/
  OmniImage.spec
```
