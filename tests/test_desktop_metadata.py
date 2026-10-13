"""Verify exposure evidence, automatic UTC mapping and project compatibility."""
from pathlib import Path
import json
import struct
import tempfile
import unittest
from unittest.mock import Mock
import tkinter as tk
import numpy as np
from astropy.io import fits
from occultation_media.inspect_observer_metadata import inspect_exposure,resolve_exposure,resolve_native_mode
from occultation_media.gui_config import build_config
from occultation_media.gui_observer import DEFAULTS
from occultation_media.migrate_desktop_project import migrate_project
from occultation_media.gui_localization import Localizer,translate
from occultation_media.plan_station_timeline import order_stations,plan_timeline
from occultation_media.prepare_station_frames import StationFrames
from occultation_media.station_sample import MediaSample


def make_ser(path,epoch,count=5):
    """Write a tiny SER with 200-ms cadence and exact original UTC trailer."""
    h=bytearray(178);h[:14]=b'LUCAM-RECORDER';struct.pack_into('<7I',h,14,0,0,1,2,2,16,count)
    ticks=int(epoch.astype('int64'))//100+621355968000000000
    path.write_bytes(h+np.zeros((count,2,2),dtype='<u2').tobytes()+struct.pack(f'<{count}Q',*(ticks+i*2000000 for i in range(count))))


class DesktopMetadataTests(unittest.TestCase):
    def test_ser_exposure_comes_from_settings_not_cadence(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'frames.ser';make_ser(source,np.datetime64('2026-09-12','ns'))
            obs=dict(DEFAULTS,source=str(source),curve=str(Path(tmp)/'curve.csv'))
            self.assertIsNone(inspect_exposure(obs))
            source.with_suffix('.CameraSettings.txt').write_text('Exposure=10.000ms\n')
            info=resolve_exposure(obs)
            self.assertEqual(info['exposure_s'],.01)
            self.assertIn('CameraSettings',info['path'])

    def test_fits_actual_exposure_overrides_command_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'0.fits';fits.writeto(source,np.zeros((2,2)),fits.Header({'EXPTIME':.24994}))
            curve=Path(tmp)/'curve.csv';curve.write_text('#INSTRUMENT-SHUTTER: 250000000\nFrameNum,timeInfo,signal-target\n')
            info=resolve_exposure(dict(DEFAULTS,source=str(source),curve=str(curve)))
            self.assertEqual(info['exposure_s'],.24994);self.assertEqual(info['method'],'FITS EXPTIME')

    def test_pymovie_shutter_and_manual_missing_metadata_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            curve=Path(tmp)/'curve.csv';curve.write_text('#INSTRUMENT-SHUTTER: 250000000\nFrameNum,timeInfo,signal-target\n')
            obs=dict(DEFAULTS,curve=str(curve))
            self.assertEqual(resolve_exposure(obs)['exposure_s'],.25)
            curve.write_text('FrameNum,timeInfo,signal-target\n')
            with self.assertRaisesRegex(ValueError,'No recorded exposure'):resolve_exposure(obs)
            self.assertEqual(resolve_exposure(dict(obs,exposure_mode='manual',exposure_ms='12'))['exposure_s'],.012)

    def test_automatic_mode_and_old_project_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=Path(tmp)/'results.json';result.write_text(json.dumps({'mode':'C3'}))
            self.assertEqual(resolve_native_mode(dict(DEFAULTS,pyote_result=str(result))),'C3')
            self.assertEqual(resolve_native_mode(DEFAULTS),'raw')
        event,obs=migrate_project(dict(gui_version=1,event=dict(window_mode='D/R 周围',skip_gaps='跳过',playback_mode='指定时长',station_order='北 → 南'),observers=[dict(name='Old',exposure_ms='300.0711',source_first_frame='7')]),DEFAULTS)
        self.assertEqual(event['window_mode'],'dr');self.assertEqual(event['skip_gaps'],'skip')
        self.assertEqual(obs[0]['exposure_mode'],'manual');self.assertEqual(obs[0]['exposure_ms'],'300.0711')
        self.assertEqual(obs[0]['source_first_frame'],'7')
        self.assertEqual(obs[0]['observer'],'')
        obs[0]['observer']='示例观测者 / Example Observer'
        _,reopened=migrate_project(dict(gui_version=1,event=event,observers=obs),DEFAULTS)
        self.assertEqual(reopened[0]['observer'],obs[0]['observer'])
        self.assertEqual(reopened[0]['name'],'Old')

    def test_live_caption_translation_preserves_model_values(self):
        interpreter=tk.Tcl();language=tk.StringVar(master=interpreter,value='中文')
        export=tk.StringVar(master=interpreter,value='zh');model=tk.StringVar(master=interpreter,value='manual')
        window=Mock();label=Mock();ui=Localizer(window,language);ui.bind(label,'window_manual')
        language.set('English');label.configure.assert_called_with(text='Custom start/end UTC')
        self.assertEqual(export.get(),'zh');self.assertEqual(model.get(),'manual')
        self.assertIn('not fitting algorithms',translate('mode_help','en'))
        ui.destroy(Mock(widget=window))

    def test_auto_mapping_uses_utc_instead_of_first_csv_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            epoch=np.datetime64('2026-09-12T09:54:00','ns');source=Path(tmp)/'frames.ser';make_ser(source,epoch)
            rows=[MediaSample(1500+i,epoch+np.timedelta64((i+1)*200+100,'ms'),.2,100) for i in range(3)]
            cfg=dict(name='Clipped',source=str(source),source_first_frame='auto',exposure_s=.2,source_timestamp_reference='start',mapping_tolerance_s=1e-9)
            frames=StationFrames(cfg,rows)
            self.assertEqual(frames.mapping,{0:1,1:2,2:3})
            self.assertEqual(frames.records[0]['frame'],1500)
            self.assertEqual(frames.records[0]['mapping_method'],'absolute_utc_auto')
            self.assertEqual(frames.records[0]['residual_s'],0)
            frames.close()
            with self.assertRaisesRegex(ValueError,'UTC mismatch'):StationFrames(dict(cfg,source_minus_curve_s=.03),rows)

    def test_full_coverage_and_unknown_coordinates_need_no_dr(self):
        epoch=np.datetime64('2026-09-12','ns')
        rows=[MediaSample(i,epoch+np.timedelta64(i*200,'ms'),.2,100) for i in range(3)]
        stations=[dict(config=dict(name='Unknown'),rows=rows,D=None,R=None),dict(config=dict(name='Known',latitude_deg=-37,longitude_deg=145),rows=rows,D=None,R=None)]
        self.assertEqual([s['config']['name'] for s in order_stations(stations,'north_to_south')],['Known','Unknown'])
        times,_,_,_=plan_timeline(dict(window_mode='full',step_s=.2,skip_gaps=True),stations)
        self.assertEqual(len(times),3);self.assertEqual(times[0],epoch)

    def test_new_gui_configuration_has_no_manual_required_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'frames.ser';make_ser(source,np.datetime64('2026-09-12','ns'))
            source.with_suffix('.CameraSettings.txt').write_text('Exposure=200ms\n');curve=root/'curve.csv';curve.touch()
            obs=dict(DEFAULTS,curve=str(curve),source=str(source))
            cfg=build_config(dict(event='Test',target='Star',date_utc='2026-09-12',window_mode='full',skip_gaps='skip',step_s='.2',language='en',output_root=tmp),[obs])
            self.assertEqual(cfg['stations'][0]['exposure_s'],.2)
            self.assertEqual(cfg['stations'][0]['source_first_frame'],'auto')
            self.assertNotIn('latitude_deg',cfg['stations'][0]);self.assertEqual(cfg['start_utc'],'')


if __name__=='__main__':unittest.main()
