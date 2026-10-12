"""Build and smoke-test an OS-native desktop release; no cross compilation."""
from pathlib import Path
import json
import os
import platform
import shutil
import subprocess
import sys
import tomllib

root=Path(__file__).resolve().parents[1]
from collect_licenses import collect
from package_user_guide import copy_user_guide
from prepare_adv_bundle import prepare
if platform.system() not in ('Windows','Darwin'):
    raise SystemExit('Run the build on Windows x64 or macOS arm64/x86_64 Python.')
vendor=prepare(root)
os.environ['PYTHONPATH']=os.pathsep.join(filter(None,[str(vendor),os.environ.get('PYTHONPATH','')]))
collect(root)
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,check=True)
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','OccultationVisualiser.spec'],cwd=root,check=True)
mac=platform.system()=='Darwin'
exe=root/('dist/OccultationVisualiser.app/Contents/MacOS/OccultationVisualiser' if mac else 'dist/OccultationVisualiser/OccultationVisualiser.exe')
report=root/'dist/package-self-test.json'
subprocess.run([str(exe),'--self-test',str(report)],check=True)
results=json.loads(report.read_text())
if not results['ok']:raise SystemExit('Package self-test failed')
if results['architecture']!=platform.machine():raise SystemExit('Frozen application architecture differs from build Python')
results['version']=tomllib.loads((root/'pyproject.toml').read_text())['project']['version']
provenance=vendor/'advcore-build.json'
if platform.system()=='Darwin' and platform.machine()=='arm64':
    results['advcore_build']=json.loads(provenance.read_text())
if mac:
    subprocess.run([str(exe),'--gui-smoke'],check=True)
    results['gui_startup']=True
    flavor='Apple-Silicon' if platform.machine()=='arm64' else 'Intel'
    package=root/f'dist/OccultationVisualiser-macOS-{flavor}'
    package.mkdir(exist_ok=True)
    staged_app=package/'OccultationVisualiser.app'
    if staged_app.exists(): shutil.rmtree(staged_app)
    shutil.copytree(root/'dist/OccultationVisualiser.app',staged_app,symlinks=True)
    copy_user_guide(root,package)
    archive=root/f'dist/OccultationVisualiser-macOS-{flavor}.zip'
    subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(package),str(archive)],check=True)
else:
    copy_user_guide(root,root/'dist/OccultationVisualiser')
    archive=Path(shutil.make_archive(str(root/'dist/OccultationVisualiser-Windows-x64'),'zip',root/'dist','OccultationVisualiser'))
report.write_text(json.dumps(results,indent=2))
print(f'Release: {archive}')
