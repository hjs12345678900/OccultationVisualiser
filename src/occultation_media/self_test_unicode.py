"""Verify UTF-8 saved results and a Unicode desktop job in the frozen runtime."""
from pathlib import Path
import json
import locale
import shutil
import sys
from .desktop_job import start_job
from .gui_config import build_config
from .gui_observer import DEFAULTS


def verify(root):
    """Run the actual GUI worker protocol with Chinese paths and PyOTE notes.

    Reuse the synthetic timed SER/CSV from the parent self-test. Assert saved
    D/R (UTC seconds), B/sigmaB and exact source/curve matching survive the
    complete isolated export job. No source timestamps or data are refitted.
    """
    directory = Path(root) / '运行-台站'
    directory.mkdir()
    for name in ('frames.ser', 'native.csv', 'frames.CameraSettings.txt'):
        shutil.copy2(Path(root) / name, directory / name)
    result = directory / 'PyOTE结果.json'
    result.write_text(json.dumps(dict(mode='raw', timesAreValid=True, Dframe=2, Rframe=4,
        Dtime=.6, Rtime=1.2, B=100, A=10, sigmaB=10,
        note='运行记录 — résumé'), ensure_ascii=False), encoding='utf-8-sig')
    cfg = build_config(dict(event='运行', target='Target', date_utc='2026-01-01', step_s='.3',
        language='both', window_mode='full', skip_gaps='skip', output_root=str(directory)),
        [dict(DEFAULTS, name='观测者运行', curve=str(directory/'native.csv'),
              source=str(directory/'frames.ser'), pyote_result=str(result))])
    config = directory / '配置.json'
    config.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
    job = directory / 'job-output'
    job.mkdir()
    process = start_job(['--media-config', str(config), '--output-dir', str(directory/'media')], job)
    process.wait(timeout=120)
    status = json.loads((job/'result.json').read_text(encoding='utf-8'))
    if process.returncode or not status['ok']:
        raise AssertionError('Unicode desktop job failed: ' + str(status))
    meta = json.loads((directory/'media/media_metadata.json').read_text(encoding='utf-8'))
    station = meta['stations'][0]
    if station['baseline_snr']['snr'] != 10 or station['baseline_snr']['estimated']:
        raise AssertionError('Saved native SNR changed')
    if station['D_utc'] != '2026-01-01T00:00:00.600000000' or station['R_utc'] != '2026-01-01T00:00:01.200000000':
        raise AssertionError('Saved native D/R changed')
    if station['matched_images'] != 6 or station['residual_max_s'] != 0:
        raise AssertionError('Unicode job frame/UTC matching differs')
    return dict(pyote_utf8_bom=True, unicode_paths=True, isolated_desktop_job=True,
                saved_snr_and_utc_unchanged=True, default_encoding=locale.getencoding(),
                python_utf8_mode=sys.flags.utf8_mode)
