# -*- mode: python ; coding: utf-8 -*-


# ============================================================
# Analysis
# ============================================================

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],

    # Runtime data files.
    #
    # The GUI uses CanopyCCGR.ico.
    # main.py uses CanopyCCGR.png for the Qt splash.
    #
    datas=[
        ('CanopyCCGR.ico', '.'),
        ('CanopyCCGR.png', '.'),
    ],

    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


# ============================================================
# Python archive
# ============================================================

pyz = PYZ(
    a.pure
)


# ============================================================
# Executable
# ============================================================

exe = EXE(
    pyz,
    a.scripts,
    [],

    exclude_binaries=True,

    name='CanopyCCGR',

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

    icon=['CanopyCCGR.ico'],
)


# ============================================================
# One-directory collection
# ============================================================

coll = COLLECT(
    exe,

    a.binaries,

    a.datas,

    strip=False,

    upx=True,

    upx_exclude=[],

    name='CanopyCCGR',
)