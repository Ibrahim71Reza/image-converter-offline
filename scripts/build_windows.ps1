$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -e ".[full,build]"

pyinstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "OmniImage" `
  --add-data "vendor/imagemagick;vendor/imagemagick" `
  --collect-submodules PIL `
  packaging/pyinstaller_entry.py

Write-Host "Build complete. Check dist/OmniImage/"
