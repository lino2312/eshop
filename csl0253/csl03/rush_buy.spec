# -*- mode: python ; coding: utf-8 -*-

# 单线程简化版抢购助手 PyInstaller 打包配置
# 打包命令: pyinstaller rush_buy.spec

a = Analysis(
    ['rush_buy.py'],
    pathex=[],
    binaries=[],
    datas=[('y1871.wav', '.'), ('account.txt', '.'), ('auth_config.py', '.')],
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
    a.binaries,
    a.datas,
    [],
    name='rush_buy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
