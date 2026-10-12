"""Reproduce Western Windows ANSI decoding of unescaped UTF-8 PyOTE notes."""
from contextlib import contextmanager
from pathlib import Path
import io
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from occultation_media.gui_config import build_config
from occultation_media.gui_observer import DEFAULTS
from occultation_media.read_saved_snr import station_snr
from occultation_media.read_saved_transitions import saved_transitions
from occultation_media.station_sample import MediaSample
from occultation_media.launcher import main as launch


@contextmanager
def ansi_default():
    """Use real CP1252 decoding whenever filesystem callers omit encoding."""
    original = io.open
    def windows_open(file, mode='r', buffering=-1, encoding=None, errors=None,
                     newline=None, closefd=True, opener=None):
        if 'b' not in mode and encoding in (None, 'locale'):
            encoding = 'cp1252'
        return original(file, mode, buffering, encoding, errors, newline, closefd, opener)
    with patch('io.open', windows_open):
        yield


class SavedUtf8Tests(unittest.TestCase):
    def test_worker_error_keeps_unicode_diagnostic_on_ansi_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            request, result = Path(tmp)/'request.json', Path(tmp)/'result.json'
            request.write_text(json.dumps(dict(source='运行.adv'), ensure_ascii=False), encoding='utf-8')
            with ansi_default(), patch('sys.argv', ['app', '--adv-worker', str(request), str(result)]), \
                 patch('occultation_media.decode_adv_worker.main', side_effect=ValueError('运行记录错误')):
                with self.assertRaises(SystemExit) as failure:
                    launch()
                self.assertEqual(failure.exception.code, 1)
                self.assertIn('运行记录错误', result.read_text(encoding='utf-8'))

    def test_desktop_mode_timing_and_snr_on_ansi_windows(self):
        epoch = np.datetime64('2026-09-12T09:54:00', 'ns')
        rows = [MediaSample(10+i, epoch+np.timedelta64(i*200, 'ms'), .2, 100)
                for i in range(6)]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            curve, source, result = root/'curve.csv', root/'frames.ser', root/'result.json'
            curve.write_text('#INSTRUMENT-SHUTTER: 200000000\nFrameNum,timeInfo,signal-target\n', encoding='utf-8')
            source.touch()
            payload = json.dumps(dict(mode='C3', timesAreValid=True, Dframe=11.5, Rframe=13.5,
                                      Dtime=35640.3, Rtime=35640.7, B=100, A=40, sigmaB=10,
                                      note='运行记录 — résumé'), ensure_ascii=False)
            # U+8FD0 includes byte 0x90, undefined in CP1252, as in the report.
            self.assertIn(b'\x90', payload.encode('utf-8'))
            for encoding in ('utf-8', 'utf-8-sig'):
                with self.subTest(encoding=encoding):
                    result.write_bytes(payload.encode(encoding))
                    with ansi_default():
                        cfg = build_config(dict(event='Altona', target='Star', date_utc='2026-09-12',
                            window_mode='dr', skip_gaps='skip', step_s='.2', language='en', output_root=tmp),
                            [dict(DEFAULTS, curve=str(curve), source=str(source), pyote_result=str(result))])
                        station = cfg['stations'][0]
                        self.assertEqual(station['native_mode'], 'C3')
                        d, r, provenance = saved_transitions(station, rows)
                        self.assertEqual(d, epoch+np.timedelta64(300, 'ms'))
                        self.assertEqual(r, epoch+np.timedelta64(700, 'ms'))
                        metric = station_snr(station, rows, d, r)
                        self.assertEqual(metric['snr'], 10)
                        self.assertEqual(metric['dnr'], 6)
                        self.assertFalse(metric['estimated'])


if __name__ == '__main__':
    unittest.main()
