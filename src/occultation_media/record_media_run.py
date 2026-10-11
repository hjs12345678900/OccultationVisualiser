"""Record source integrity, code version and timestamp evidence for a media run."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import tomllib


def sha256(path):
    """Return SHA-256 of a file, streamed in bounded chunks without modification."""
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''): digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    """Write UTF-8 JSON data to a file in the newly created output directory."""
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def version():
    """Read the authoritative pyproject version, or installed package metadata."""
    project = Path(__file__).resolve().parents[2]/'pyproject.toml'
    if project.is_file(): return tomllib.loads(project.read_text())['project']['version']
    return importlib.metadata.version('occultation-media')


def input_manifest(paths):
    """Hash every actual curve, fit and image input; return unique absolute files."""
    return [dict(path=str(p), sha256=sha256(p), bytes=p.stat().st_size)
            for p in dict.fromkeys(Path(p).resolve() for p in paths)]


def finish_record(out, inputs, status, error=None):
    """Recheck immutable inputs and save code/environment evidence, even on error."""
    integrity = all(sha256(record['path']) == record['sha256'] for record in inputs)
    if not integrity: status, error = 'failed', 'Input files changed during media generation'
    source = out/'source_snapshot'
    code = {p.name:sha256(p) for p in sorted(source.glob('*.py'))}
    state=json.loads((source/'code_state.json').read_text())
    write_json(out/'run_metadata.json', dict(status=status, error=error, **state,
        completed_utc=datetime.now(timezone.utc).isoformat(), python=sys.version, platform=platform.platform(),
        input_integrity_verified=integrity, input_files=inputs, source_sha256=code,
        dependencies={name:importlib.metadata.version(name) for name in ('numpy','Pillow','astropy','imageio-ffmpeg')}))
    write_json(out/'status.json', dict(status=status, error=error))
    if not integrity: raise ValueError(error)


def snapshot_code(out):
    """Save executing project source before rendering, preserving reproducibility."""
    snapshot=out/'source_snapshot'
    snapshot.mkdir()
    for path in Path(__file__).parent.glob('*.py'):shutil.copy2(path,snapshot/path.name)
    git=dict(commit=None,dirty=None)
    try:
        commit=subprocess.run(['git','rev-parse','HEAD'],cwd=Path(__file__).parent,capture_output=True,text=True,timeout=5)
        status=subprocess.run(['git','status','--porcelain'],cwd=Path(__file__).parent,capture_output=True,text=True,timeout=5)
        if commit.returncode==0:git=dict(commit=commit.stdout.strip(),dirty=bool(status.stdout.strip()))
    except (OSError,subprocess.TimeoutExpired):pass
    write_json(snapshot/'code_state.json',dict(version=version(),git=git,command=sys.argv))
