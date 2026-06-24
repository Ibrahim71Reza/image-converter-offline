from __future__ import annotations

import argparse
from pathlib import Path

from .converter import ConverterService
from .backends.base import ConversionOptions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline image file converter.")
    parser.add_argument("inputs", nargs="+", type=Path, help="Input image file(s).")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("converted"), help="Output folder.")
    parser.add_argument("-t", "--target", required=True, help="Target image format, e.g. png, jpg, webp, tiff.")
    parser.add_argument("-q", "--quality", type=int, default=92, help="Lossy output quality 1-100.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files.")
    parser.add_argument("--strip-metadata", action="store_true", help="Remove metadata from output files.")
    parser.add_argument("--background", default="white", help="Background color for alpha-to-JPEG conversion.")
    parser.add_argument("--list-backends", action="store_true", help="Print backend status and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    service = ConverterService()
    if args.list_backends:
        for status in service.backend_statuses():
            availability = "available" if status.available else "missing"
            print(f"{status.name}: {availability}; reads={status.readable_count}; writes={status.writable_count}")
        return 0

    options = ConversionOptions(
        quality=args.quality,
        overwrite=args.overwrite,
        preserve_metadata=not args.strip_metadata,
        background=args.background,
    )
    results = service.convert_batch(args.inputs, args.output_dir, args.target, options)
    exit_code = 0
    for result in results:
        mark = "OK" if result.success else "FAIL"
        print(f"[{mark}] {result.input_path} -> {result.output_path} ({result.backend_name}) {result.message}")
        if not result.success:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
