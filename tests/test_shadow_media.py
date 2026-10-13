"""Exercise frame-time simulation, optional-map exports and desktop persistence."""
import csv
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
import numpy as np
from astropy.io import fits
from PIL import Image
from occultation_media.read_occult_prediction import parse_prediction
from occultation_media.plan_shadow_simulation import ShadowSimulation
from occultation_media.make_station_media import load_config,make_station_media
from occultation_media.migrate_desktop_project import migrate_project
from occultation_media.gui_observer import DEFAULTS
from occultation_media.gui_config import build_config

PREDICTION=Path(__file__).resolve().parents[1]/'examples/altona_20260912.occelmnt'


class ShadowMediaTests(unittest.TestCase):
    def test_actual_frame_midpoints_do_not_apply_saved_offsets_again(self):
        geometry=parse_prediction(PREDICTION.read_text(encoding='utf-8'))
        utc=np.datetime64('2026-09-12T09:54:30','ns')
        records={0:dict(source_midpoint_utc=str(utc+np.timedelta64(32200000,'ns')),applied_source_minus_curve_s=.0322)}
        station=dict(config=dict(name='Melbourne',latitude_deg=-37.8136,longitude_deg=144.9631),
                     rows=[SimpleNamespace(utc=utc,frame=1234)],frames=SimpleNamespace(mapping={0:77},records=records))
        simulation=ShadowSimulation(geometry,{},[station],np.array([utc,utc+np.timedelta64(240,'s')]))
        state=simulation.frame_state(station,0)
        expected=simulation.position(utc)
        self.assertEqual(state['center'],expected)
        self.assertNotEqual(state['center'],simulation.position(np.datetime64(records[0]['source_midpoint_utc'],'ns')))
        self.assertEqual(state['frame'],1234)
        self.assertIsNone(simulation.frame_state(station,None))
        self.assertIsNone(simulation.frame_state(station,1))

    def test_desktop_opt_in_and_legacy_project_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);curve=root/'curve.csv';source=root/'source.ser';curve.touch();source.touch()
            source.with_suffix('.CameraSettings.txt').write_text('Exposure=200ms\n',encoding='utf-8')
            event=dict(event='Altona',target='Star',date_utc='2026-09-12',window_mode='full',
                       step_s='.2',language='en',output_root=tmp,shadow_enabled='1',shadow_prediction_file=str(PREDICTION))
            obs={**DEFAULTS,'curve':str(curve),'source':str(source)}
            cfg=build_config(event,[obs])
            self.assertTrue(cfg['shadow_simulation']['enabled'])
            self.assertNotIn('shadow_simulation',build_config({**event,'shadow_enabled':'0'},[obs]))
            self.assertNotIn('shadow_simulation',build_config({**event,'shadow_prediction_file':'missing'},[obs],quality_only=True))
            with self.assertRaises(FileNotFoundError):build_config({**event,'shadow_prediction_file':'missing'},[obs])
            migrated,_=migrate_project(dict(gui_version=1,event={'event':'old'},observers=[]),DEFAULTS)
            self.assertEqual(migrated['shadow_enabled'],'0')

    def test_real_bilingual_encoding_with_missing_location_and_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stations=[]
            for k in range(2):
                base=np.datetime64('2026-09-12T09:54:29.900','ns')+np.timedelta64(k*3,'s')
                source=root/f'fits{k}';source.mkdir()
                lines=['FrameNum,timeInfo,signal-target,xcentroid-target,ycentroid-target']
                for i in range(4):
                    utc=base+np.timedelta64(i*200,'ms')
                    lines.append(f'{i},[{str(utc).split("T")[1]}],100,8,8')
                    fits.writeto(source/f'{i}.fits',np.arange(256,dtype=np.uint16).reshape(16,16),
                                 fits.Header({'DATE-OBS':str(utc),'EXPTIME':.2}))
                curve=root/f'curve{k}.csv';curve.write_text('\n'.join(lines),encoding='utf-8')
                station=dict(name=f'S{k}',curve_format='pymovie_csv',curve=str(curve),source=str(source),
                             target_column='signal-target',exposure_s=.2,timestamp_reference='start',
                             source_timestamp_reference='start',mapping_tolerance_s=1e-9)
                if k==0:station.update(latitude_deg=-37.8136,longitude_deg=144.9631)
                stations.append(station)
            (root/'prediction.occelmnt').write_bytes(PREDICTION.read_bytes())
            cfg=dict(event='Altona',target='Star',date_utc='2026-09-12',alignment='absolute_utc',language='both',
                     step_s=.2,window_mode='full',skip_gaps=True,playback_mode='fixed_duration',video_duration_s=1,
                     stations=stations,shadow_simulation=dict(enabled=True,prediction_file='prediction.occelmnt'))
            path=root/'cfg.json';path.write_text(json.dumps(cfg),encoding='utf-8')
            self.assertEqual(load_config(path)['shadow_simulation']['prediction_file'],str((root/'prediction.occelmnt').resolve()))
            out=make_station_media(path,root/'out')
            meta=json.loads((out/'media_metadata.json').read_text(encoding='utf-8'))
            self.assertTrue(meta['no_event_time_shift'])
            self.assertEqual(meta['shadow_simulation']['verified_frame_positions'],8)
            self.assertEqual(meta['shadow_simulation']['omitted_stations'],['S1'])
            self.assertEqual(meta['stations'][0]['matched_images'],4)
            self.assertEqual(len(meta['timeline_plan']['skipped_gaps']),1)
            self.assertEqual(meta['outputs']['en']['mp4_shape'],[1920,1258])
            with (out/'shadow_frame_positions.csv').open(encoding='utf-8',newline='') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),8)
            self.assertEqual(rows[0]['curve_midpoint_utc'],'2026-09-12T09:54:30.000000000')
            self.assertTrue(rows[4]['curve_midpoint_utc'].startswith('2026-09-12T09:54:33.'))
            self.assertEqual(rows[4]['station_latitude_deg'],'')
            self.assertEqual(rows[0]['nominally_covered'],'True')
            for lang in ('en','zh'):
                with Image.open(meta['outputs'][lang]['preview']) as preview:
                    self.assertEqual(preview.size,(1920,1258))
                self.assertTrue(Path(meta['outputs'][lang]['gif']).is_file())
            run=json.loads((out/'run_metadata.json').read_text(encoding='utf-8'))
            self.assertTrue(any(i['path'].endswith('prediction.occelmnt') for i in run['input_files']))
            self.assertTrue(run['input_integrity_verified'])


if __name__=='__main__':unittest.main()
