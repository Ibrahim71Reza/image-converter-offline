"""PyInstaller entry point for OmniImage.

Do not point PyInstaller directly at src/omniimage/main.py. A direct file
entry makes Python execute it as a top-level script, which breaks relative
imports inside the package after freezing. This wrapper imports the package
entry point normally, preserving package context in the frozen app.
"""

from omniimage.main import main


if __name__ == "__main__":
    raise SystemExit(main())
