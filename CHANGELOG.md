# Changelog

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
