# OmniImage Converter

**OmniImage Converter** is a portable offline desktop application for batch image conversion. It is designed for common everyday conversions such as PNG → JPEG, WebP → PNG, TIFF → JPEG, GIF → WebP, and for wider professional format support through optional/bundled backends.

The project is built with a realistic global-release principle: no honest application can guarantee every image format ever invented, because some formats are proprietary, undocumented, obsolete, licensed, or require external codecs. OmniImage solves this professionally with multiple backends, dynamic format detection, and a plugin-style architecture.

## What is new in v0.2.0

- Folder import in the GUI
- Recursive folder import
- Drag-and-drop folder support
- Cancel button for long batch jobs
- CSV conversion report generation
- Safer target-format list for mixed batches: the GUI now shows formats that every queued file can convert to
- CLI no longer requires dummy inputs for `--list-backends` or `--list-formats`
- CLI folder input support
- CLI recursive mode
- CLI CSV report output
- CLI fail-fast mode
- Shared format-alias handling: `jpg` → `JPEG`, `tif` → `TIFF`
- CSV formula-injection protection in reports
- Better tests for path discovery, reports, aliases, non-overwrite mode, CLI, and ImageMagick format parsing
- Version bumped to `0.2.0`

## Core features

- Offline desktop GUI
- Portable-app build scripts
- Drag-and-drop file and folder queue
- Batch conversion
- Dynamic target-format list based on installed/bundled backends
- Mixed-batch-safe target list
- Quality control for lossy output
- Preserve metadata when possible
- Preserve animation when possible
- Alpha handling for JPEG/BMP output
- Non-overwrite mode with automatic numbered filenames
- CSV conversion reports
- CLI for automation and testing
- Local Git-ready structure
- PyInstaller packaging scripts for portable releases

## Conversion backends

- **rawpy backend**: optional camera RAW importer for formats such as DNG, NEF, CR2, ARW, RAF, RW2, ORF, and others.
- **ImageMagick backend**: wide-format engine for public releases. Bundle ImageMagick into `vendor/imagemagick/` or install it on the target machine.
- **Pillow backend**: dependable built-in path for common formats such as PNG, JPEG, WebP, BMP, TIFF, GIF, ICO, PDF, TGA, DDS, PCX, PSD reading, and more depending on the local Pillow build.

Backend preference order is:

1. rawpy
2. ImageMagick
3. Pillow

That order gives camera RAW files a high-quality RAW-specific path, uses ImageMagick for broad public-release coverage, and keeps Pillow as a strong common-format fallback.

## Install for development

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .[full,dev,build]
```

macOS/Linux:

```bash
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

Convert one file:

```bash
omniimage-cli sample.png --target jpg --output-dir converted
```

Convert multiple files:

```bash
omniimage-cli one.png two.webp three.tiff --target jpg --output-dir converted
```

Convert a folder recursively:

```bash
omniimage-cli ./input-images --recursive --target webp --output-dir ./converted
```

Write a CSV report:

```bash
omniimage-cli ./input-images --recursive --target png --output-dir ./converted --report ./converted/report.csv
```

Check backend status:

```bash
omniimage-cli --list-backends
```

List supported formats:

```bash
omniimage-cli --list-formats
```

## Bundle ImageMagick for maximum offline coverage

For a serious global release, include the correct platform-specific ImageMagick binary in:

```text
vendor/imagemagick/
```

Expected executable names:

- Windows: `vendor/imagemagick/magick.exe`
- macOS/Linux: `vendor/imagemagick/magick`
- fallback name: `vendor/imagemagick/convert`

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

## Test

```bash
pytest
```

Current included test suite covers:

- PNG → JPEG conversion
- Alpha-to-JPEG handling
- Supported target lookup
- Non-overwrite filename generation
- Recursive path discovery
- CLI backend listing
- CLI conversion report generation
- CSV report safety
- ImageMagick format-list parsing

## Project structure

```text
src/omniimage/
  app.py                         # PySide6 desktop UI
  cli.py                         # CLI entry point
  converter.py                   # backend selection and batch service
  file_discovery.py              # file/folder expansion helpers
  format_utils.py                # target format aliases and CSV safety
  reports.py                     # CSV report writer
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
vendor/imagemagick/
  .gitkeep                       # put platform-specific ImageMagick binaries here for releases
```

## Release checklist for a serious public app

- Bundle ImageMagick separately for Windows, macOS, and Linux.
- Test conversions across at least: PNG, JPEG, WebP, TIFF, BMP, GIF, ICO, HEIC/HEIF, AVIF, SVG, PDF, EPS, PSD, and camera RAW.
- Confirm licenses for every bundled binary and codec.
- Sign Windows/macOS releases.
- Add CI builds for Windows, macOS, and Linux.
- Run malware/false-positive checks on packaged `.exe` builds.
- Decide whether update checks are allowed; keep them disabled by default for true offline positioning.

## Important limitation

OmniImage can be made extremely broad, but it cannot truthfully promise every image conversion that exists on earth. A public, trustworthy product should say: **supports a very wide and extensible image-format set, with exact supported formats shown inside the app based on installed/bundled backends.**
