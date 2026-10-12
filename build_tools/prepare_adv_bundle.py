"""Build the pinned, unmodified ADVCore source for native Apple Silicon.

The shipped source archive and MPL notice preserve upstream provenance without
network downloads. Stage a private Adv2 package so the user's installed decoder
is never replaced. The ctypes ABI and detector/timestamp decoding are unchanged.
"""
from pathlib import Path
import hashlib
from importlib import metadata
import json
import platform
import shutil
import subprocess
import tarfile

COMMIT = 'bbcda85214540c2e8996b7715887c358f68141cd'
SOURCE_SHA256 = '6f731f7ff558edb4daeb825fc16f8211e2e352f0c5c02b0a2127c1932769d02b'


def validate_architecture(path, expected):
    """Reject incompatible Mach-O libraries before freezing an application."""
    architectures = subprocess.check_output(['lipo', '-archs', str(path)], text=True).split()
    if expected not in architectures:
        raise RuntimeError(f'{path} supports {architectures}, but the build needs {expected}')


def prepare(root):
    """Return a private dependency directory matching the running interpreter."""
    root = Path(root)
    vendor = root / 'build_vendor'
    vendor.mkdir(exist_ok=True)
    original = Path(metadata.distribution('Adv2').locate_file('Adv2'))
    staged = vendor / 'Adv2'
    if original.resolve() != staged.resolve():
        if staged.exists():
            shutil.rmtree(staged)
        shutil.copytree(original, staged)
    if platform.system() != 'Darwin':
        return vendor
    architecture = platform.machine()
    library = staged / 'Adv2DLLlibs/libAdvCore.dylib'
    if architecture == 'arm64':
        archive = root / 'src/occultation_media/assets/licenses/ADVCore/source.tar.gz'
        if hashlib.sha256(archive.read_bytes()).hexdigest() != SOURCE_SHA256:
            raise RuntimeError('ADVCore source archive checksum differs from the pinned revision')
        work = vendor / 'advcore'
        work.mkdir(exist_ok=True)
        with tarfile.open(archive) as source:
            source.extractall(work, filter='data')
        sources = work / 'ADVCore/src'
        obj = work / 'quicklz.o'
        flags = ['-arch', 'arm64', '-mmacosx-version-min=14.0', '-O2', '-fPIC']
        subprocess.run(['clang', *flags, '-c', str(sources / 'quicklz.c'), '-o', str(obj)], check=True)
        subprocess.run(['clang++', *flags, '-std=c++11', '-fvisibility=hidden',
                        '-fvisibility-inlines-hidden', '-dynamiclib',
                        *(str(p) for p in sorted(sources.glob('*.cpp'))), str(obj),
                        '-o', str(library)], check=True)
        (vendor / 'advcore-build.json').write_text(json.dumps(dict(
            architecture=architecture, upstream_commit=COMMIT, source_sha256=SOURCE_SHA256,
            library_sha256=hashlib.sha256(library.read_bytes()).hexdigest()), indent=2))
    validate_architecture(library, architecture)
    return vendor


if __name__ == '__main__':
    print(prepare(Path(__file__).resolve().parents[1]))
