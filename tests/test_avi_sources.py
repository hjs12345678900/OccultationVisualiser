"""AVI frames must follow declared identity, never container cadence or guesses."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
from occultation_media.self_test_avi import write_fixture, verify
from occultation_media.read_frame_sources import open_source
from occultation_media.prepare_station_frames import StationFrames
from occultation_media.station_sample import MediaSample
from occultation_media.gui_config import build_config
from occultation_media.gui_observer import DEFAULTS
from occultation_media.migrate_desktop_project import migrate_project


class AviTests(unittest.TestCase):
    def test_codecs_irregular_midnight_and_real_bilingual_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=verify(Path(tmp))
            self.assertTrue(result['bilingual_export'])
            self.assertEqual(result['codecs']['ffv1'],0)

    def test_sparse_curve_and_cropped_partial_recording(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'crop.avi';expected=write_fixture(path)
            start=np.datetime64('2026-09-12T23:59:59.950','ns')
            rows=[MediaSample(frame,start+np.timedelta64(i*200,'ms'),.1,100,(),(0.,0.),0,0,(32,16))
                  for i,frame in enumerate([99,100,102,105,106])]
            cfg=dict(name='A',source=str(path),source_first_frame=100,timestamp_reference='midpoint')
            frames=StationFrames(cfg,rows)
            self.assertEqual(frames.mapping,{1:0,2:2,3:5})
            frames.prepare(range(5));self.assertEqual(set(frames.prepared),{1,2,3})
            self.assertTrue(all(r['residual_s'] is None for r in frames.records.values()))
            for first in ('auto',None,True,1.5,-1):
                with self.assertRaisesRegex(ValueError,'source_first_frame'):
                    StationFrames(dict(cfg,source_first_frame=first),rows)
            with self.assertRaisesRegex(ValueError,'no independent UTC'):
                StationFrames(dict(cfg,source_minus_curve_s=.03),rows)
            with self.assertRaisesRegex(ValueError,'No curve frames'):
                StationFrames(dict(cfg,source_first_frame=1000),rows)
            with self.assertRaises(IndexError):open_source(path).read(6)

    def test_invalid_and_truncated_avi_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.avi';path.write_bytes(b'not AVI')
            with self.assertRaisesRegex(ValueError,'RIFF'):open_source(path)
            write_fixture(Path(tmp)/'full.avi')
            data=(Path(tmp)/'full.avi').read_bytes();path.write_bytes(data[:len(data)//2])
            with self.assertRaisesRegex(ValueError,'Truncated'):open_source(path)
            path.write_bytes(b'RIFF'+(16).to_bytes(4,'little')+b'AVI '+b'\0'*12)
            with self.assertRaises(ValueError):open_source(path)

    def test_gui_requires_frame_and_clock_and_project_preserves_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'curve.csv').touch();(root/'source.avi').touch()
            event=dict(event='Test',target='Star',date_utc='2026-09-12',window_mode='full',
                       step_s='.1',language='en',output_root=tmp)
            obs=dict(DEFAULTS,curve=str(root/'curve.csv'),source=str(root/'source.avi'),
                     exposure_mode='manual',exposure_ms='100')
            with self.assertRaisesRegex(ValueError,'timestamp convention'):build_config(event,[obs])
            obs['avi_timestamp_reference']='end'
            with self.assertRaisesRegex(ValueError,'frame ID'):build_config(event,[obs])
            obs['source_first_frame']='100'
            cfg=build_config(event,[obs]);self.assertEqual(cfg['stations'][0]['timestamp_reference'],'end')
            _,loaded=migrate_project(dict(gui_version=1,event=event,observers=[obs]),DEFAULTS)
            self.assertEqual(loaded[0]['avi_timestamp_reference'],'end')
            self.assertEqual(loaded[0]['source_first_frame'],'100')
            quality=build_config(event,[dict(obs,source_first_frame='')],quality_only=True)
            self.assertEqual(quality['stations'][0]['timestamp_reference'],'end')
