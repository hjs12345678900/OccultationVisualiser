"""Compare two frozen ADV workers against every frame of a real recording.

Observations are read-only. Exact uint32 pixel hashes, native UTC midpoint ns and
exposure ns must agree; no stretch, photometry, rounding or resampling is used.
Temporary decoded buffers are removed after each batch. The JSON evidence
records source and executable hashes without copying the observation itself.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def decode(executable, source, indices, directory):
    directory.mkdir()
    request, result = directory / 'request.json', directory / 'result.json'
    request.write_text(json.dumps(dict(source=str(source), indices=indices,
                                      output_dir=str(directory))), encoding='utf-8')
    subprocess.run([str(executable), '--adv-worker', str(request), str(result)], check=True)
    metadata = json.loads(result.read_text(encoding='utf-8-sig'))
    hashes = {index: digest(directory / f'{index}.raw') for index in indices}
    return metadata, hashes


def compare(first, second, source, output):
    """Write evidence only after all main-stream frames agree byte-for-byte."""
    first, second, source = map(lambda p: Path(p).resolve(), (first, second, source))
    source_hash = digest(source)
    with tempfile.TemporaryDirectory(prefix='adv-compare-') as temporary:
        root = Path(temporary)
        left, _ = decode(first, source, [], root / 'first')
        right, _ = decode(second, source, [], root / 'second')
        if left != right:
            raise AssertionError('Recording metadata differs')
        count = left['count']
    evidence = hashlib.sha256()
    for start in range(0, count, 32):
        indices = list(range(start, min(start + 32, count)))
        with tempfile.TemporaryDirectory(prefix='adv-compare-') as temporary:
            root = Path(temporary)
            left, pixels_left = decode(first, source, indices, root / 'first')
            right, pixels_right = decode(second, source, indices, root / 'second')
            if left != right or pixels_left != pixels_right:
                raise AssertionError(f'Pixels or native timestamps differ at batch {start}')
            evidence.update(json.dumps([left, pixels_left], sort_keys=True).encode())
    if digest(source) != source_hash:
        raise AssertionError('Source changed during verification')
    report = dict(ok=True, source=source.name, source_sha256=source_hash, frames=count,
                  pixels_exact=True, utc_and_exposure_ns_exact=True,
                  input_integrity_verified=True, evidence_sha256=evidence.hexdigest(),
                  executables=[dict(sha256=digest(exe), architecture=subprocess.check_output(
                      ['lipo', '-archs', str(exe)], text=True).strip()) for exe in (first, second)])
    Path(output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('first', 'second', 'source', 'output'):
        parser.add_argument('--' + field, required=True)
    print(json.dumps(compare(**vars(parser.parse_args())), indent=2))
