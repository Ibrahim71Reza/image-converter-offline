# Architecture

OmniImage uses a backend-selection architecture.

## Layers

1. **GUI / CLI layer**
   - `app.py` provides the PySide6 desktop interface.
   - `cli.py` provides automation and testing commands.

2. **Service layer**
   - `converter.py` owns backend discovery, supported-format aggregation, backend selection, and batch conversion.

3. **Backend layer**
   - `backends/base.py` defines the shared protocol and data models.
   - `backends/raw_backend.py` handles camera RAW through rawpy.
   - `backends/imagemagick_backend.py` handles broad ImageMagick conversions.
   - `backends/pillow_backend.py` handles common built-in conversions.

4. **Utility layer**
   - `file_discovery.py` expands files and folders.
   - `format_utils.py` normalizes format aliases and protects CSV output.
   - `reports.py` writes conversion reports.

## Backend choice

The default order is rawpy → ImageMagick → Pillow.

- rawpy is preferred for camera RAW because it is purpose-built for RAW demosaicing.
- ImageMagick is preferred for broad format support when bundled or installed.
- Pillow is used as a dependable common-format fallback.

## Adding a new backend

Create a class implementing the `ImageBackend` protocol:

- `is_available()`
- `input_formats()`
- `output_formats()`
- `can_read(path)`
- `can_write(target_format)`
- `supported_outputs_for(path)`
- `convert(job)`

Then add it to the default backend list in `ConverterService.__init__`.
