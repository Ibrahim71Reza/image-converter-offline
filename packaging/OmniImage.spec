# Optional PyInstaller spec. The simpler build scripts are usually enough.
# Run from repository root with: pyinstaller packaging/OmniImage.spec

from pathlib import Path

block_cipher = None
root = Path.cwd()

a = Analysis(
    [str(root / "src" / "omniimage" / "main.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[(str(root / "vendor" / "imagemagick"), "vendor/imagemagick")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OmniImage",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OmniImage",
)
