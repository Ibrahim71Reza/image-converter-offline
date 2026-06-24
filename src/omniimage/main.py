from __future__ import annotations


def main() -> int:
    try:
        from .app import run
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            print("PySide6 is not installed. Run: pip install -e .")
            return 1
        raise
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
