# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for MS Feature DB Matcher
# Usage: pyinstaller ms_feature_db_matcher.spec

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    [str(root / "app.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[(str(root / "database"), "database")],
    hiddenimports=["ms_feature_db_matcher"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "scipy", "numpy.testing"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MS Feature DB Matcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=sys.platform == "darwin",
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="MS Feature DB Matcher.app",
        icon=None,
        bundle_identifier="com.ms-feature-db-matcher",
    )
