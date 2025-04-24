# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['audio_parser/analyze.py', 'audio_parser/assembly.py', 'audio_parser/config.py', 'audio_parser/db.py', 'audio_parser/main.py', 'audio_parser/pyinstaller.py', 'audio_parser/utils.py'],
    pathex=['audio_parser/__pycache__'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='analyze',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='analyze',
)
