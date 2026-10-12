"""Exercise GUI contracts independently of desktop interaction."""
from pathlib import Path
import tempfile
import unittest
from occultation_media.gui_config import build_config
from occultation_media.gui_observer import DEFAULTS


class GuiConfigTests(unittest.TestCase):
    def test_timeline_controls_and_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);curve=root/'curve.csv';source=root/'source.ser'
            curve.touch();source.touch()
            event=dict(event='Asteroid',target='Star',date_utc='2026-09-12',start_utc='',end_utc='',
                       step_s='.1',language='both',output_root=tmp,window_mode='D/R 周围',event_padding_s='10',
                       skip_gaps='跳过',playback_mode='指定时长',video_duration_s='30',station_order='北 → 南')
            obs={**DEFAULTS,'curve':str(curve),'source':str(source),'exposure_ms':'200',
                 'D_utc':'10:00:00','R_utc':'10:00:01','latitude_deg':'-45','longitude_deg':'169'}
            cfg=build_config(event,[{**obs,'name':'South'},{**obs,'name':'North','latitude_deg':'-37'}])
            self.assertTrue(cfg['skip_gaps']);self.assertEqual(cfg['window_mode'],'dr')
            self.assertEqual(cfg['video_duration_s'],30)
            self.assertEqual([s['name'] for s in cfg['stations']],['North','South'])
            with self.assertRaises(ValueError):build_config(event,[{**obs,'D_utc':'','R_utc':''}])
            with self.assertRaises(ValueError):build_config(event,[{**obs,'longitude_deg':''}])

    def test_shared_event_independent_prediction_and_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);curve=root/'curve.csv';source=root/'source.ser'
            curve.touch();source.touch()
            event=dict(event='Asteroid',target='Star',date_utc='2026-09-12',start_utc='23:59:59',
                       end_utc='2026-09-13T00:00:01',step_s='.2',language='both',output_root=tmp)
            a={**DEFAULTS,'name':'A','curve':str(curve),'source':str(source),'exposure_ms':'200','predicted_utc':'23:59:59.5'}
            b={**a,'name':'B','mode':'Tangra','predicted_utc':'2026-09-13T00:00:00.1'}
            cfg=build_config(event,[a,b])
            self.assertEqual(len(cfg['stations']),2)
            self.assertEqual(cfg['stations'][0]['exposure_s'],.2)
            self.assertEqual(cfg['stations'][0]['timestamp_reference'],'start')
            self.assertEqual(cfg['stations'][1]['timestamp_reference'],'midpoint')
            self.assertNotEqual(cfg['stations'][0]['predicted_utc'],cfg['stations'][1]['predicted_utc'])
            self.assertNotIn('predicted_utc',cfg)
            self.assertEqual(a['exposure_ms'],'200')
            with self.assertRaises(ValueError):build_config({**event,'step_s':'0'},[a])
            with self.assertRaises(ValueError):build_config(event,[{**a,'R_utc':'00:00:01'}])
            with self.assertRaises(ValueError):build_config(event,[{**a,'curve':str(root/'missing.csv')}])

    def test_multi_observer_real_encoding(self):
        import json
        import numpy as np
        from astropy.io import fits
        from occultation_media.make_station_media import make_station_media
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'fits';source.mkdir()
            lines=['FrameNum,timeInfo,signal-target,xcentroid-target,ycentroid-target']
            for i in range(3):
                stamp=f'2026-09-12T10:00:00.{i*200:03d}'
                fits.writeto(source/f'{i}.fits',np.arange(256,dtype=np.uint16).reshape(16,16),
                             fits.Header({'DATE-OBS':stamp,'EXPTIME':.2}))
                lines.append(f'{i},[{stamp.split("T")[1]}],100,8,8')
            curve=root/'curve.csv';curve.write_text('\n'.join(lines))
            obs={**DEFAULTS,'curve':str(curve),'source':str(source),'exposure_ms':'200'}
            event=dict(event='Test',target='Star',date_utc='2026-09-12',start_utc='10:00:00.1',end_utc='10:00:00.5',
                       step_s='.2',language='en',output_root=tmp)
            for count in (2,3):
                cfg=build_config(event,[{**obs,'name':str(k)} for k in range(count)])
                path=root/f'config{count}.json';path.write_text(json.dumps(cfg))
                output=make_station_media(path,root/f'out{count}')
                meta=json.loads((output/'media_metadata.json').read_text())
                self.assertEqual(len(meta['stations']),count)
                self.assertEqual(meta['outputs']['en']['mp4_shape'][1]%2,0)
                self.assertTrue(Path(meta['outputs']['en']['mp4']).is_file())
