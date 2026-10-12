"""Verify UTC-preserving cuts, southern latitude order and real playback codecs."""
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
import numpy as np
from astropy.io import fits
from PIL import Image
from occultation_media.plan_station_timeline import plan_timeline, order_stations
from occultation_media.render_utc_axis import UtcAxis, coordinate_label
from occultation_media.make_station_media import make_station_media


def station(name, start, latitude=-37):
    epoch=np.datetime64(start,'ns')
    return dict(config=dict(name=name,latitude_deg=latitude,longitude_deg=145),
                D=epoch+np.timedelta64(400,'ms'),R=epoch+np.timedelta64(600,'ms'),
                rows=[SimpleNamespace(utc=epoch),SimpleNamespace(utc=epoch+np.timedelta64(1,'s'))])


class TimelineTests(unittest.TestCase):
    def test_disjoint_dr_windows_keep_absolute_utc_and_exact_holds(self):
        stations=[station('Melbourne','2026-09-12T23:59:58'),station('Later','2026-09-13T00:04:00')]
        cfg=dict(step_s=.2,window_mode='dr',event_padding_s=.3,skip_gaps=True)
        times,holds,windows,info=plan_timeline(cfg,stations)
        self.assertEqual(str(times[0]),'2026-09-12T23:59:58.100000000')
        self.assertEqual(str(windows[1][0]),'2026-09-13T00:04:00.100000000')
        self.assertAlmostEqual(holds.sum(),1.6)
        self.assertEqual(len(info['skipped_gaps']),1)
        self.assertGreater(float((times[4]-times[3])/np.timedelta64(1,'s')),240)
        original=times.copy()
        fixed=plan_timeline({**cfg,'playback_mode':'fixed_duration','video_duration_s':3},stations)
        np.testing.assert_array_equal(original,fixed[0])
        self.assertAlmostEqual(fixed[1].sum(),3)
        self.assertEqual(fixed[3]['intervals'],info['intervals'])
        axis=UtcAxis(windows)
        self.assertIsNone(axis.position(np.datetime64('2026-09-13T00:01:00','ns')))
        self.assertEqual(len(list(axis.spans(windows[0][0],windows[-1][1]))),2)

    def test_keep_gaps_missing_frames_and_invalid_settings(self):
        stations=[station('A','2026-09-12T10:00:00'),station('B','2026-09-12T10:00:03')]
        cfg=dict(step_s=.2,window_mode='dr',event_padding_s=.25,skip_gaps=True)
        _,holds,_,_=plan_timeline(cfg,stations)
        self.assertAlmostEqual(holds.sum(),1.4)
        _,continuous,intervals,_=plan_timeline({**cfg,'skip_gaps':False},stations)
        self.assertEqual(len(intervals),1)
        self.assertAlmostEqual(continuous.sum(),3.7)
        manual=dict(step_s=.2,start_utc='2026-09-12T10:00:00',end_utc='2026-09-12T10:00:04',skip_gaps=True)
        _,_,intervals,_=plan_timeline(manual,stations)
        self.assertEqual(len(intervals),2)
        for patch in ({'event_padding_s':float('nan')},{'skip_gaps':'yes'},
                      {'playback_mode':'fixed_duration','video_duration_s':0}, {'step_s':0}):
            with self.assertRaises(ValueError):plan_timeline({**cfg,**patch},stations)
        stations[0]['D']=None
        with self.assertRaisesRegex(ValueError,'A.*D/R'):plan_timeline(cfg,stations)

    def test_north_to_south_requires_geographic_coordinates(self):
        stations=[station('South','2026-09-12',-45),station('North','2026-09-12',-37.78),station('Middle','2026-09-12',-37.92)]
        ordered=order_stations(stations,'north_to_south')
        self.assertEqual([s['config']['name'] for s in ordered],['North','Middle','South'])
        self.assertEqual(coordinate_label(ordered[0]['config']),'37.78000° S · 145.00000° E')
        del stations[0]['config']['latitude_deg']
        with self.assertRaises(ValueError):order_stations(stations,'north_to_south')
        stations[0]['config']['latitude_deg']=91
        with self.assertRaises(ValueError):order_stations(stations,'north_to_south')

    def test_bilingual_fixed_duration_export_with_utc_jump(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stations=[]
            for k in range(2):
                epoch=np.datetime64('2026-09-12T10:00:00','ns')+np.timedelta64(k*3,'s')
                source=root/f'fits{k}';source.mkdir()
                lines=['FrameNum,timeInfo,signal-target,xcentroid-target,ycentroid-target']
                for i in range(6):
                    stamp=epoch+np.timedelta64(i*200,'ms')
                    lines.append(f'{i},[{str(stamp).split("T")[1]}],{20 if i==2 else 100},8,8')
                    fits.writeto(source/f'{i}.fits',np.arange(256,dtype=np.uint16).reshape(16,16),fits.Header({'DATE-OBS':str(stamp),'EXPTIME':.2}))
                curve=root/f'curve{k}.csv';curve.write_text('\n'.join(lines))
                stations.append(dict(name=f'S{k}',curve_format='pymovie_csv',curve=str(curve),source=str(source),
                    target_column='signal-target',exposure_s=.2,timestamp_reference='start',source_timestamp_reference='start',
                    mapping_tolerance_s=1e-9,latitude_deg=-45 if k==0 else -37,longitude_deg=145,
                    D_utc=str(epoch+np.timedelta64(400,'ms')),R_utc=str(epoch+np.timedelta64(600,'ms'))))
            cfg=dict(event='Cuts',target='Star',date_utc='2026-09-12',alignment='absolute_utc',language='both',stations=stations,
                     step_s=.2,window_mode='dr',event_padding_s=.25,skip_gaps=True,
                     station_order='north_to_south',playback_mode='fixed_duration',video_duration_s=2)
            path=root/'cfg.json';path.write_text(json.dumps(cfg))
            out=make_station_media(path,root/'out')
            meta=json.loads((out/'media_metadata.json').read_text())
            self.assertEqual([s['name'] for s in meta['stations']],['S1','S0'])
            self.assertTrue(all(s['baseline_snr']['snr'] is None for s in meta['stations']))
            self.assertEqual(len(meta['timeline_plan']['skipped_gaps']),1)
            for lang in ('en','zh'):
                output=meta['outputs'][lang]
                self.assertEqual(output['mp4_frames'],50)
                self.assertEqual(output['mp4_duration_s'],2)
                with Image.open(output['gif']) as gif:
                    duration=0
                    for i in range(gif.n_frames):gif.seek(i);duration+=gif.info['duration']
                    self.assertAlmostEqual(duration/1000,2,delta=.06)
            for sample in meta['display_selection']:
                # Output is north first, even though the southern event occurs first.
                self.assertIsNone(sample['frames'][0] if sample['utc']<'2026-09-12T10:00:02' else sample['frames'][1])


if __name__=='__main__': unittest.main()
