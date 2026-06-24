<div align="center">

# 🔄 OmniImage Converter

**Portable offline desktop image conversion for Windows, with source support for advanced cross-platform builds.**

[![Platform](https://img.shields.io/badge/Portable%20Release-Windows-blue?style=flat-square)](../../releases)
[![Python](https://img.shields.io/badge/Python-3.12%20tested-blue?style=flat-square&logo=python&logoColor=white)](#)
[![Release](https://img.shields.io/badge/Release-v0.3.1-success?style=flat-square)](../../releases)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

OmniImage is designed for users who want a simple, powerful image converter that works entirely offline. It supports batch processing, preserves folder structures, generates reports, and expands its capabilities dynamically using professional backends like ImageMagick and rawpy.

[🔽 Download](#-download--quick-start) • [✨ Features](#-main-features) • [💻 Command Line](#-command-line-usage) • [🛠️ Developers](#%EF%B8%8F-developer--build-guide)

</div>

---

## 🚀 Download & Quick Start

For normal Windows users, **no Python installation is required**. Just download, extract, and run.

### Windows

1. Go to the **[Releases](../../releases)** page.
2. Download `OmniImage-Portable-v0.3.1-Windows.zip`.
3. **Extract** the ZIP file. Do not run it from inside the ZIP.
4. Open the extracted `OmniImage` folder.
5. Double-click `OmniImage.exe`.
6. Add your images and click **Convert Now**.

---

## 🖼️ What can OmniImage do?

OmniImage handles common and professional image formats. Here are a few example conversions:

| From     | To     | From    | To                  |
| :------- | :----- | :------ | :------------------ |
| **PNG**  | ➡️ JPG | **BMP** | ➡️ PNG              |
| **JPG**  | ➡️ PNG | **GIF** | ➡️ WEBP             |
| **AVIF** | ➡️ GIF | **ICO** | ➡️ PNG              |
| **WEBP** | ➡️ PNG | **TGA** | ➡️ JPG              |
| **TIFF** | ➡️ JPG | **RAW** | ➡️ JPG / PNG / WEBP |

> 💡 **Note:** The exact available formats depend on the conversion backends included or installed on your system. OmniImage detects supported formats dynamically instead of making unrealistic claims about every image format ever created.

---

## ✨ Main Features

### 🖥️ Easy Desktop App
* **Offline First:** No internet required for normal conversion.
* **Portable:** Runs from an extracted portable folder.
* **Drag-and-Drop:** Add individual files or entire folders.
* **Smart UI:** Choose output folders and open them directly from the app.

### ⚡ Batch Conversion
* Convert massive folders of images at once.
* **Recursive Scanning:** Converts images inside sub-folders.
* **Structure Preservation:** Keeps your original folder layout intact (or use flat output via CLI).
* **Safe Output:** Prevents files with the same name from overwriting each other.

### 🎯 Smart Format Handling
* Target formats update automatically based on your queued files.
* Understands format aliases (e.g., treats `.jpg` and `.jpeg` the same).
* Handles transparent images when converting to formats without alpha support, such as JPEG or BMP.
* Skips unsupported/non-image documents automatically.

### 📊 Reports & Logs
* View live progress in the GUI conversion log.
* Automatically generate **CSV Conversion Reports** detailing status, time, output paths, and errors.

---

## ⚙️ Supported Backends

OmniImage is powered by a multi-backend engine. Backend priority is: `rawpy` ➡️ `ImageMagick` ➡️ `Pillow`.

* 🟢 **Pillow:** Handles common formats (PNG, JPG, WEBP, BMP, TIFF, GIF, ICO, TGA, DDS, PCX, PSD read, PDF write).
* 📷 **rawpy:** Handles real camera RAW imports (DNG, NEF, CR2, CR3, ARW, RAF, RW2, ORF, PEF, SRW).
* 🪄 **ImageMagick:** Handles wider professional format coverage. Can be installed on your system or bundled inside `vendor/imagemagick/`.

---

## 💻 Command-Line Usage

OmniImage comes with a fully-featured CLI for automation and advanced users.

**Basic Conversion:**
```bash
omniimage-cli sample.png --target jpg --output-dir converted
```
**Batch & Folder Conversion:**
```bash
# Convert multiple specific files
omniimage-cli one.png two.webp three.tiff --target jpg --output-dir converted

# Convert a folder recursively
omniimage-cli ./input-images --recursive --target webp --output-dir ./converted
```
**Reports & Output Modifiers:**
```bash
# Generate an automatic CSV report
omniimage-cli ./input-images --recursive --target png --output-dir ./converted --report

# Flatten all outputs into a single folder (ignore original folder structure)
omniimage-cli ./input-images --recursive --target png --output-dir ./converted --flat-output
```
**System Info:**
```bash
omniimage-cli --list-backends
omniimage-cli --list-formats
```

---

## ❓ Troubleshooting

<details>
<summary><b>The app does not open?</b></summary>
Make sure you extracted the ZIP first. Do not run the app directly from inside the compressed ZIP.<br>
<i>Correct: Extract ZIP → Open OmniImage folder → Run OmniImage.exe</i>
</details>

<details>
<summary><b>Windows shows a security warning?</b></summary>
Unsigned apps may show a Windows SmartScreen warning. Click <b>More info</b> and then <b>Run anyway</b> (only do this if you downloaded the app from the official GitHub Releases page).
</details>

<details>
<summary><b>A format appears but conversion fails?</b></summary>
Some formats support only certain image modes (e.g., they may not support transparency, animation, or a specific color depth). Try converting to PNG, JPG, TIFF, or WEBP first.
</details>

<details>
<summary><b>RAW files fail to convert?</b></summary>
You must use real camera RAW files. Fake files simply renamed to `.cr2`, `.nef`, or `.dng` will not work.
</details>

<details>
<summary><b>I need more formats!</b></summary>
Install or bundle ImageMagick on your system, then restart OmniImage.
</details>

---

## 🛠️ Developer & Build Guide

*(Click to expand sections below)*

<details>
<summary><b>Local Development Setup</b></summary>

Create and activate a virtual environment:

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .[full,dev,build]
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[full,dev,build]
```

**Run the app:**
```bash
omniimage
# or
python -m omniimage.main
```
</details>

<details>
<summary><b>Building the Portable App</b></summary>

**Windows:**
```powershell
scripts\build_windows.ps1
Compress-Archive -Path "dist\OmniImage" -DestinationPath "OmniImage-Portable-v0.3.1-Windows.zip" -Force
```

**macOS/Linux:**
```bash
bash scripts/build_unix.sh
```
</details>

<details>
<summary><b>Testing & Architecture</b></summary>

Run tests using pytest:
```bash
pytest
```

**Project Structure:**
```text
src/omniimage/
  ├── app.py                     # Desktop GUI
  ├── cli.py                     # CLI entry point
  ├── converter.py               # Backend selection and batch service
  ├── reports.py                 # CSV report writer
  └── backends/                  # Format processing modules
        ├── base.py              
        ├── pillow_backend.py    
        ├── imagemagick_backend.py 
        └── raw_backend.py       

scripts/                         # Build scripts
packaging/                       # PyInstaller templates
tests/                           # Automated test suite
```
</details>

<details>
<summary><b>Public Release Checklist</b></summary>

- [ ] Test Windows portable ZIP on a clean Windows machine.
- [ ] Test PNG, JPEG, WebP, TIFF, BMP, GIF, ICO, AVIF, HEIC/HEIF, SVG, PDF, PSD, and RAW files.
- [ ] Bundle ImageMagick for each platform if maximum offline coverage is required.
- [ ] Confirm licenses for every bundled binary and codec.
- [ ] Sign Windows and macOS releases.
- [ ] Add CI builds for Windows, macOS, and Linux.
- [ ] Scan packaged builds for malware false positives.
- [ ] Keep update checks disabled by default for offline positioning.
</details>

---

## 📜 Release Notes

> **Note:** Portable pre-compiled releases are currently provided for **Windows only**. macOS and Linux users can easily run or build from source using the Developer Setup guide above.

<details>
<summary><b>v0.3.1 (Current)</b></summary>

* Fixed PyInstaller entry point error (`ImportError: attempted relative import...`).
* Added `packaging/pyinstaller_entry.py`.
* Updated Windows build script to build from the wrapper.
* Reduced unnecessary PySide6 collection during packaging.
</details>

<details>
<summary><b>v0.3.0</b></summary>

* `--report` can be used without a path.
* Automatic `conversion_report.csv` inside the output folder.
* Folder scans skip common non-image files by default.
* Recursive output preserves folder structure by default (`--flat-output` added).
* Prevents same-stem overwrite collisions.
* JPEG output standardized to `.jpg`.
</details>

<details>
<summary><b>v0.2.0</b></summary>

* Folder import in GUI (recursive, drag-and-drop).
* Cancel button for long batch jobs.
* CSV conversion reports.
* CLI folder input, fail-fast mode, and format aliases.
* CSV formula-injection protection.
</details>

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.
