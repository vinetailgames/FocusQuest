# -*- mode: python ; coding: utf-8 -*-

import subprocess
from pathlib import Path


project_root = Path(SPECPATH).resolve()
assets_root = project_root / "assets"


def is_git_ignored(path):
    relative_path = path.relative_to(project_root).as_posix()
    result = subprocess.run(
        [
            "git", "-C", str(project_root), "check-ignore", "--no-index",
            "--quiet", "--", relative_path,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"Could not evaluate .gitignore for {relative_path}")
    return result.returncode == 0


asset_datas = []
if assets_root.is_dir():
    for asset_path in assets_root.rglob("*"):
        if not asset_path.is_file() or is_git_ignored(asset_path):
            continue
        relative_parent = asset_path.relative_to(assets_root).parent
        destination = Path("assets") / relative_parent
        asset_datas.append((str(asset_path), str(destination)))

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=asset_datas + [(str(project_root / 'version.json'), '.')],
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
    name='FocusQuest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project_root / 'assets' / 'icon' / 'icon.ico'),
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
    name='FocusQuest',
)
