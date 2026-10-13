"""Reproduce a date-mismatched 709-sample CSV with independently timed RAVF."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from ravf import RavfWriter, RavfFrameType
from occultation_media.make_station_media import make_station_media
from occultation_media.gui_error_text import error_text
from occultation_media.record_media_run import sha256


class AlignmentReportingTests(unittest.TestCase):
    def write_observation(self, root):
        """Write native start times on Oct 4; CSV clocks deliberately omit dates."""
        base = np.datetime64('2026-10-04T09:30:26', 'ns')
        epoch = np.datetime64('2010-01-01', 'ns')
        source = root/'20261004_093026.ravf'
        required = [('COLOR-TYPE',0), ('IMAGE-ENDIANESS',1), ('IMAGE-WIDTH',4),
                    ('IMAGE-HEIGHT',2), ('IMAGE-ROW-STRIDE',8), ('IMAGE-FORMAT',1),
                    ('FRAME-TIMING-ACCURACY',1000)]
        pixels = np.arange(8, dtype='<u2').tobytes()
        clocks = []
        with contextlib.redirect_stdout(io.StringIO()), source.open('wb') as stream:
            writer = RavfWriter(stream, required, [])
            for i in range(709):
                time = base+np.timedelta64(i*100, 'ms')
                clocks.append(str(time).split('T')[1])
                writer.write_frame(stream, RavfFrameType.LIGHT, pixels,
                    int((time-epoch)/np.timedelta64(1,'ns')), 99_940_000, 7, 0, 0, 0, 0)
            writer.finish(stream)
        curve = root/'Yamandu.csv'
        curve.write_text('FrameNum,timeInfo,signal-Yamandu\n' + '\n'.join(
            f'{i},[{clock}],100' for i,clock in enumerate(clocks)), encoding='utf-8')
        station = dict(name='Peter', curve_format='pymovie_csv', curve=str(curve),
            source=str(source), target_column='signal-Yamandu', exposure_s=.09994,
            timestamp_reference='start', source_timestamp_reference='start',
            source_first_frame='auto', mapping_tolerance_s=.001)
        cfg = dict(event='Yamandu', target='star', date_utc='2026-10-13',
            alignment='absolute_utc', step_s=.2, language='en', window_mode='full',
            playback_mode='real_time', stations=[station])
        return cfg, source, curve

    def save_config(self, root, cfg):
        path = root/'config.json'
        path.write_text(json.dumps(cfg), encoding='utf-8')
        return path

    def test_wrong_date_fails_verification_and_generation_with_original_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg, source, curve = self.write_observation(root)
            before = [sha256(source), sha256(curve)]
            config = self.save_config(root, cfg)
            for verify in (True, False):
                out = root/f'failed-{verify}'
                log = io.StringIO()
                with contextlib.redirect_stdout(log), self.assertRaises(ValueError) as raised:
                    make_station_media(config, out, verify_only=verify)
                message = str(raised.exception)
                self.assertIn('No source images match', message)
                self.assertIn('2026-10-13T09:30:26.049970000', message)
                self.assertIn('2026-10-04T09:30:26.049970000', message)
                self.assertIn('709 samples; 0 mapped real images', log.getvalue())
                self.assertNotIn('原始影像', error_text(message, 'English'))
                self.assertNotIn('No source images match', error_text(message, '中文'))
                report = json.loads((out/'alignment_report.json').read_text(encoding='utf-8'))['stations'][0]
                self.assertEqual(report['matched_images'], 0)
                self.assertEqual(report['source_format'], 'RAVF')
                self.assertEqual(report['mapping_tolerance_s'], .001)
                self.assertLess(report['closest_residual_s'], -8*86400)
                run = json.loads((out/'run_metadata.json').read_text(encoding='utf-8'))
                self.assertEqual(run['status'], 'failed')
                self.assertTrue(run['input_integrity_verified'])
                self.assertEqual(len(run['input_files']), 3)
            self.assertEqual([sha256(source), sha256(curve)], before)

    def test_corrected_date_maps_all_709_images_and_exports_selected_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg, _, _ = self.write_observation(root)
            cfg['date_utc'] = '2026-10-04'
            config = self.save_config(root, cfg)
            with contextlib.redirect_stdout(io.StringIO()):
                make_station_media(config, root/'verified', verify_only=True)
            meta = json.loads((root/'verified/media_metadata.json').read_text(encoding='utf-8'))
            self.assertEqual(meta['stations'][0]['matched_images'], 709)
            self.assertEqual(meta['stations'][0]['residual_min_s'], 0)
            cfg.update(window_mode='manual', start_utc='2026-10-04T09:30:26.04997',
                       end_utc='2026-10-04T09:30:27.04997')
            config = self.save_config(root, cfg)
            with contextlib.redirect_stdout(io.StringIO()):
                make_station_media(config, root/'export')
            meta = json.loads((root/'export/media_metadata.json').read_text(encoding='utf-8'))
            self.assertEqual(meta['stations'][0]['displayed_images'], 6)
            self.assertTrue(meta['no_event_time_shift'])
            self.assertTrue(Path(meta['outputs']['en']['mp4']).is_file())

    def test_empty_station_remains_allowed_alongside_a_matching_station(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg, _, curve = self.write_observation(root)
            cfg['date_utc'] = '2026-10-04'
            other = root/'other.csv'
            other.write_text(curve.read_text(encoding='utf-8').replace('[09:', '[10:'), encoding='utf-8')
            cfg['stations'].append({**cfg['stations'][0], 'name':'Later', 'curve':str(other)})
            cfg.update(window_mode='manual', start_utc='2026-10-04T09:30:26.04997',
                       end_utc='2026-10-04T09:30:27.04997')
            with contextlib.redirect_stdout(io.StringIO()):
                make_station_media(self.save_config(root,cfg), root/'partial', verify_only=True)
            meta = json.loads((root/'partial/media_metadata.json').read_text(encoding='utf-8'))
            self.assertEqual([s['matched_images'] for s in meta['stations']], [709,0])
            self.assertTrue(meta['warnings'])

    def test_timestamp_verification_writes_to_a_strict_windows_ansi_console(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg, _, _ = self.write_observation(root)
            cfg['date_utc'] = '2026-10-04'
            raw = io.BytesIO()
            with io.TextIOWrapper(raw, encoding='cp1252', errors='strict') as console:
                with contextlib.redirect_stdout(console):
                    make_station_media(self.save_config(root,cfg), root/'ansi', verify_only=True)
                console.flush()
                output = raw.getvalue().decode('cp1252')
            self.assertIn('709 mapped real images', output)
            self.assertIn('Source UTC: 2026-10-04', output)
            self.assertIn('原始影像 UTC: 2026-10-04', error_text(output,'中文'))
