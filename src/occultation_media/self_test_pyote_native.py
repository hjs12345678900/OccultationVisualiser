"""Verify native PyOTE TXT through the frozen desktop worker and exports."""
from pathlib import Path
import json
from .desktop_job import start_job
from .gui_config import build_config
from .gui_observer import DEFAULTS

HEADER = ('aperture name,time err +/-secs,DNR,FP metric,magDrop,percent drop,'
          'duration (secs),D time,R time,D frame,R frame,B,A,sigmaB,sigmaA,'
          'observed drop,FP drop,FP margin\n')


def verify(root):
    """Return import evidence for both text formats; raise on changed saved values.

    Reuse the parent test's six synthetic SER frames and PyMovie samples. TXT
    fixtures carry Chinese source paths and declare fitted-reading integration;
    the test asserts that this metadata does not alter saved D/R or frame UTC.
    """
    root = Path(root)
    directory = root/'PyOTE-原生结果'
    directory.mkdir()
    contents = {
        'fit_metrics.txt': HEADER+'\nSource file is C:\\运行\\native.csv\n\n'
        +'signal-target,.1,9,1,2,90,.6,[00:00:00.6000],[00:00:01.2000],2,4,100,10,10,2,90,10,80\n',
        'native.pyote_log.txt': '\n'.join([
            '#################### PYOTE 5.4.2 session started: fixture ####################',
            'filename: C:\\运行\\native.csv', 'timeDelta: 0.6 seconds per block',
            'Timestamps appear valid @ D and R',
            'Block integration of size 2 has been applied to this light curve.',
            'All times are calculated/reported based on the assumption that timestamps are start-of-exposure times.',
            'D: 0.9500 containment intervals:  {+/- 0.1} seconds',
            'R: 0.9500 containment intervals:  {+/- 0.2} seconds',
            'fit metrics for signal-target',
            'fit metrics === B: 100.00  A: 10.00 sigmaB: 10.00  sigmaA: 2.00',
            'fit metrics === D frame number: 2.0000', 'fit metrics === R frame number: 4.0000',
            'fit metrics === D time: [00:00:00.6000]', 'fit metrics === R time: [00:00:01.2000]'])}
    summaries = []
    for number, (name, text) in enumerate(contents.items()):
        result = directory/name
        result.write_text(text, encoding='utf-8-sig')
        cfg = build_config(dict(event='Native PyOTE', target='Target', date_utc='2026-01-01',
            step_s='.3', language='both', window_mode='full', skip_gaps='skip', output_root=str(directory)),
            [dict(DEFAULTS, name='原生 TXT', curve=str(root/'native.csv'),
                  source=str(root/'frames.ser'), pyote_result=str(result))])
        config = directory/f'config-{number}.json'
        config.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
        job, output = directory/f'job-{number}', directory/f'media-{number}'
        job.mkdir()
        process = start_job(['--media-config', str(config), '--output-dir', str(output)], job)
        process.wait(timeout=120)
        status = json.loads((job/'result.json').read_text(encoding='utf-8'))
        if process.returncode or not status['ok']:
            raise AssertionError('Native PyOTE job failed: '+str(status))
        meta = json.loads((output/'media_metadata.json').read_text(encoding='utf-8'))
        station = meta['stations'][0]
        if station['D_utc'] != '2026-01-01T00:00:00.600000000' or station['R_utc'] != '2026-01-01T00:00:01.200000000':
            raise AssertionError('Native TXT D/R changed')
        snr = station['baseline_snr']
        if snr['snr'] != 10 or snr['dnr'] != 9 or snr['noise_scope'] != 'PyOTE fitted readings':
            raise AssertionError('Native TXT baseline parameters/scope changed')
        if station['matched_images'] != 6 or station['residual_max_s'] != 0:
            raise AssertionError('Native TXT source/curve UTC changed')
        if name.endswith('.pyote_log.txt'):
            if snr['integration_readings'] != 2 or station['timing']['errors95_s'] != {'D': .1, 'R': .2}:
                raise AssertionError('Log integration/errors were not retained')
        record = json.loads((output/'run_metadata.json').read_text(encoding='utf-8'))
        if not record['input_integrity_verified']:
            raise AssertionError('Native TXT input integrity failed')
        summaries.append(dict(format=snr['result_format'], saved_utc_and_snr_unchanged=True,
                              frame_matches=6, input_integrity_verified=True))
    return dict(native_txt_imports=summaries, isolated_desktop_jobs=True, languages=['en','zh'])
