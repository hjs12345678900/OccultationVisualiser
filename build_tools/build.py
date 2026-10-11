"""Build and smoke-test an OS-native desktop release; no cross compilation."""
from pathlib import Path
import json
import platform
import shutil
import subprocess
import sys
import zipfile

root=Path(__file__).resolve().parents[1]
from collect_licenses import collect
from package_user_guide import copy_user_guide
collect(root)
if platform.system() not in ('Windows','Darwin'):
    raise SystemExit('Run the build on Windows x64 or Intel-compatible macOS Python.')
if platform.system()=='Darwin' and platform.machine()!='x86_64':
    raise SystemExit('Use Intel Python/Rosetta for the macOS release; ADV native library is Intel.')
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,check=True)
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','OccultationVisualiser.spec'],cwd=root,check=True)
mac=platform.system()=='Darwin'
exe=root/('dist/OccultationVisualiser.app/Contents/MacOS/OccultationVisualiser' if mac else 'dist/OccultationVisualiser/OccultationVisualiser.exe')
report=root/'dist/package-self-test.json'
subprocess.run([str(exe),'--self-test',str(report)],check=True)
if not json.loads(report.read_text())['ok']:raise SystemExit('Package self-test failed')
if mac:
    package=root/'dist/OccultationVisualiser-macOS-Intel'
    package.mkdir(exist_ok=True)
    shutil.copytree(root/'dist/OccultationVisualiser.app',package/'OccultationVisualiser.app',dirs_exist_ok=True,symlinks=True)
    copy_user_guide(root,package)
    archive=root/'dist/OccultationVisualiser-macOS-Intel.zip'
    subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(package),str(archive)],check=True)
else:
    copy_user_guide(root,root/'dist/OccultationVisualiser')
    archive=Path(shutil.make_archive(str(root/'dist/OccultationVisualiser-Windows-x64'),'zip',root/'dist','OccultationVisualiser'))
print(f'Release: {archive}')
