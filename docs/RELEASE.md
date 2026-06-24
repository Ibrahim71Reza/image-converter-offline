# Release guide

## 1. Prepare vendor binaries

Place platform-specific ImageMagick binaries under `vendor/imagemagick/` before packaging.

Expected executable names:

- `magick.exe` for Windows
- `magick` for macOS/Linux
- `convert` as fallback

Do not commit vendor binaries unless their licenses and redistribution terms are confirmed.

## 2. Run tests

```bash
pytest
```

## 3. Build

Windows:

```powershell
scripts\build_windows.ps1
```

macOS/Linux:

```bash
bash scripts/build_unix.sh
```

## 4. Smoke-test packaged app

Test at least these conversions:

- PNG → JPEG
- JPEG → PNG
- WebP → PNG
- TIFF → JPEG
- GIF → WebP with animation preservation
- PNG with transparency → JPEG with background
- HEIC/HEIF → JPEG if the bundled codecs support it
- Camera RAW → JPEG if rawpy is included and supported on the target platform

## 5. Sign and distribute

Recommended production steps:

- Windows code signing
- macOS notarization
- VirusTotal/false-positive checks
- Separate builds per operating system
- Clear license notices for bundled binaries/codecs
