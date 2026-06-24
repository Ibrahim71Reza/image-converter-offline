# Changelog

## 0.3.0 - CLI hardening after real batch tests

### Added
- Optional report path behavior: `--report` now works without an argument and writes `conversion_report.csv` inside the output folder.
- `--include-unsupported` for deliberate unsupported-file/error-report testing.
- `--flat-output` for users who want all outputs in one folder.
- Batch output planning that preserves source folder structure by default.
- Collision-safe output naming for same-stem inputs, e.g. `sample.png` and `sample.jpg` no longer overwrite each other when converted to the same target.
- Tests for auto reports, folder filtering, output collision safety, and folder-structure preservation.

### Changed
- Folder scans skip common non-image project/document files such as `.md`, `.json`, `.txt`, `.csv`, `.yaml`, and `.log` by default.
- JPEG output paths now prefer `.jpg` consistently.

### Fixed
- Prevented same-stem files from silently overwriting earlier batch outputs when `--overwrite` is enabled.
- Removed the need to pass a CSV path after `--report` for common CLI usage.

## 0.2.0 - Final starter upgrade

### Added

- GUI folder import.
- Recursive folder import.
- Drag-and-drop folder expansion.
- Batch cancellation support in the GUI.
- CSV conversion reports.
- CLI folder input support.
- CLI recursive mode.
- CLI `--list-formats` command.
- CLI `--report` option.
- CLI `--fail-fast` option.
- Shared file-discovery helper.
- Shared format-alias helper.
- CSV report safety helper.
- Architecture and release documentation.
- GitHub Actions test workflow.
- More tests for CLI, reports, file discovery, format aliases, ImageMagick parsing, and non-overwrite behavior.

### Changed

- Version bumped from `0.1.0` to `0.2.0`.
- Backend priority changed to rawpy → ImageMagick → Pillow.
- GUI target-format dropdown now shows the common supported output formats for all queued files, not just the first file.
- `--list-backends` and `--list-formats` no longer require input files.
- Conversion results now include elapsed time.

### Fixed

- ImageMagick format parser now supports both common `magick -list format` layouts.
- Safer CSV report cells to prevent spreadsheet formula execution.
