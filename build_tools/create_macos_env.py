"""Create an architecture-specific build environment without Rosetta on M Macs."""
from pathlib import Path
import subprocess
import sys
import argparse
import platform
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--architecture',choices=('arm64','x86_64'),default=platform.machine())
architecture=parser.parse_args().architecture
env=root/f'.venv-build-{architecture}'
subprocess.run([sys.executable,'-m','venv','--copies',str(env)],check=True)
for path in (env/'bin').glob('python*'):
    if path.is_symlink() or not path.is_file():continue
    info=subprocess.run(['lipo','-archs',str(path)],capture_output=True,text=True)
    if info.returncode:continue
    if architecture not in info.stdout.split():raise SystemExit(f'Python must contain {architecture}; use a python.org universal2 installation.')
    if len(info.stdout.split())>1:
        thin=path.with_name(path.name+'.thin')
        subprocess.run(['lipo',str(path),'-thin',architecture,'-output',str(thin)],check=True)
        thin.replace(path)
python=env/'bin/python'
subprocess.run([str(python),'-m','pip','install','-e',str(root)+'[build]'],check=True)
subprocess.run([str(python),str(root/'build_tools/build.py')],cwd=root,check=True)
