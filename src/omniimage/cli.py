from __future__ import annotations

import argparse
from pathlib import Path

from .backends.base import ConversionOptions
from .converter import ConverterService
from .file_discovery import directory_source_roots, expand_input_paths
from .reports import write_csv_report

_AUTO_REPORT = "__auto__"
_DIRECTORY_SCAN_EXCLUDED_EXTENSIONS = {
    ".csv", ".ini", ".json", ".log", ".md", ".rtf", ".text", ".txt", ".xml", ".yaml", ".yml"
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline image file converter.")
    parser.add_argument("inputs", nargs="*", type=Path, help="Input image file(s) or folder(s).")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("converted"), help="Output folder.")
    parser.add_argument("-t", "--target", help="Target image format, e.g. png, jpg, webp, tiff.")
    parser.add_argument("-q", "--quality", type=int, default=92, help="Lossy output quality 1-100.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files.")
    parser.add_argument("--strip-metadata", action="store_true", help="Remove metadata from output files.")
    parser.add_argument("--no-animation", action="store_true", help="Do not attempt to preserve animation frames.")
    parser.add_argument("--background", default="white", help="Background color for alpha-to-JPEG/BMP conversion.")
    parser.add_argument("--recursive", action="store_true", help="When an input is a folder, include files recursively.")
    parser.add_argument(
        "--report",
        nargs="?",
        const=_AUTO_REPORT,
        default=None,
        help="Write a CSV conversion report. Optionally pass a report path. If no path is supplied, writes conversion_report.csv inside the output folder.",
    )
    parser.add_argument("--fail-fast", action="store_true", help="Stop batch conversion after the first failed file.")
    parser.add_argument(
        "--include-unsupported",
        action="store_true",
        help="When scanning folders, include files with unsupported/non-image extensions so failures are reported instead of skipped.",
    )
    parser.add_argument(
        "--flat-output",
        action="store_true",
        help="Do not preserve input folder structure inside the output folder.",
    )
    parser.add_argument("--list-backends", action="store_true", help="Print backend status and exit.")
    parser.add_argument("--list-formats", action="store_true", help="Print supported input/output formats and exit.")
    return parser


def _resolve_report_path(report_arg: str | None, output_dir: Path) -> Path | None:
    if report_arg is None:
        return None
    if report_arg == _AUTO_REPORT:
        return output_dir / "conversion_report.csv"
    return Path(report_arg)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    service = ConverterService()
    if args.list_backends:
        for status in service.backend_statuses():
            availability = "available" if status.available else "missing"
            print(f"{status.name}: {availability}; reads={status.readable_count}; writes={status.writable_count}")
        return 0

    if args.list_formats:
        print("Readable formats:")
        for fmt in service.supported_inputs():
            print(f"  {fmt.key}: {fmt.label} {' '.join(fmt.extensions)}")
        print("\nWritable formats:")
        for fmt in service.supported_outputs():
            print(f"  {fmt.key}: {fmt.label} {' '.join(fmt.extensions)}")
        return 0

    if not args.inputs:
        parser.error("at least one input file/folder is required unless using --list-backends or --list-formats")
    if not args.target:
        parser.error("--target is required for conversion")

    files = expand_input_paths(
        args.inputs,
        recursive=args.recursive,
        allowed_extensions=service.supported_input_extensions() - _DIRECTORY_SCAN_EXCLUDED_EXTENSIONS,
        include_unsupported_files=args.include_unsupported,
    )
    if not files:
        parser.error("no image files found in the supplied input path(s)")

    options = ConversionOptions(
        quality=args.quality,
        overwrite=args.overwrite,
        preserve_metadata=not args.strip_metadata,
        preserve_animation=not args.no_animation,
        background=args.background,
    )
    results = service.convert_batch(
        files,
        args.output_dir,
        args.target,
        options,
        fail_fast=args.fail_fast,
        source_roots=directory_source_roots(args.inputs),
        preserve_structure=not args.flat_output,
    )
    exit_code = 0
    for result in results:
        mark = "OK" if result.success else "FAIL"
        print(
            f"[{mark}] {result.input_path} -> {result.output_path} "
            f"({result.backend_name}, {result.elapsed_seconds:.2f}s) {result.message}"
        )
        if not result.success:
            exit_code = 1

    report_path = _resolve_report_path(args.report, args.output_dir)
    if report_path:
        written = write_csv_report(report_path, results)
        print(f"Report written: {written}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
