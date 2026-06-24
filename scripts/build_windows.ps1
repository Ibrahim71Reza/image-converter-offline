$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -e ".[full,build]"

pyinstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "OmniImage" `
  --add-data "vendor/imagemagick;vendor/imagemagick" `
  --collect-all PySide6 `
  --collect-all PIL `
  src/omniimage/main.py

Write-Host "Build complete. Check dist/OmniImage/"
