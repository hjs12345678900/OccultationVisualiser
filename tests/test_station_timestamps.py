"""Independent native-clock fixtures verify precision, correction and gaps."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from astropy.io import fits
from occultation_media.station_sample import MediaSample
from occultation_media.read_station_curves import read_station_curve
from occultation_media.read_saved_transitions import saved_transitions
from occultation_media.prepare_station_frames import StationFrames, nearest_sample
from occultation_media.utc_conventions import clock_sequence, midpoint, utc_ns


class TimestampTests(unittest.TestCase):
    def test_native_clock_precision_midnight_and_invalid_reordering(self):
        stamps = clock_sequence('2026-09-12', ['[23:59:59.9234567]','[00:00:00.1234567]'])
        self.assertEqual(stamps[1],np.datetime64('2026-09-13T00:00:00.123456700','ns'))
        self.assertEqual(midpoint(stamps[0],.2,'start'),np.datetime64('2026-09-13T00:00:00.023456700','ns'))
        self.assertEqual(midpoint(stamps[1],.2,'end'),stamps[0]+np.timedelta64(100,'ms'))
        with self.assertRaises(ValueError):clock_sequence('2026-09-12',['09:54:20.2','09:54:20.1'])
        with self.assertRaises(ValueError):utc_ns('2026-09-12T19:54:20+10:00')
        self.assertEqual(utc_ns('2026-09-12T09:54:20Z'),utc_ns('2026-09-12T09:54:20+00:00'))

    def test_nearest_exposure_never_extends_recording_or_fills_gap(self):
        base=utc_ns('2026-09-12T09:54:20')
        rows=[MediaSample(i,base+np.timedelta64(t,'ms'),.2,100.) for i,t in enumerate([0,200,1000,1200])]
        self.assertEqual(nearest_sample(rows,base+np.timedelta64(200,'ms')),1)
        for time in (-1,600,1300):self.assertIsNone(nearest_sample(rows,base+np.timedelta64(time,'ms')))

    def test_ser_exact_ticks_and_already_applied_delay_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'frames.ser';pixels=np.arange(12,dtype='<u2').reshape(3,2,2)
            base=utc_ns('2026-09-12T09:54:20.123456700')
            ticks=int(base.astype('int64'))//100+621355968000000000
            h=bytearray(178);h[:14]=b'LUCAM-RECORDER';struct.pack_into('<7I',h,14,0,0,1,2,2,16,3)
            path.write_bytes(h+pixels.tobytes()+struct.pack('<3Q',ticks,ticks+2000000,ticks+4000000))
            # Source start -> midpoint (+100ms); CSV already subtracts 32.2ms.
            rows=[MediaSample(i,base+np.timedelta64(i*200+100,'ms')-np.timedelta64(32200000,'ns'),.2,100.) for i in range(3)]
            cfg=dict(name='test',source=str(path),exposure_s=.2,source_timestamp_reference='start',
                     source_first_frame=0,source_minus_curve_s=.0322,mapping_tolerance_s=1e-9)
            f=StationFrames(cfg,rows)
            self.assertEqual(f.mapping,{0:0,1:1,2:2})
            self.assertEqual(f.records[0]['source_midpoint_utc'],'2026-09-12T09:54:20.223456700')
            self.assertEqual(f.records[0]['residual_s'],0.)
            f.prepare([0,2]);self.assertEqual(set(f.prepared),{0,2})
            cfg['source_minus_curve_s']=0
            with self.assertRaisesRegex(ValueError,'UTC mismatch'):StationFrames(cfg,rows)
            cfg['source_minus_curve_s']=.0644
            with self.assertRaisesRegex(ValueError,'UTC mismatch'):StationFrames(cfg,rows)

    def test_partial_fits_date_avg_is_midpoint_without_date_obs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=utc_ns('2026-09-12T09:54:20.1234567')
            rows=[MediaSample(50+i,base+np.timedelta64(i*200,'ms'),.2,100.) for i in range(5)]
            for k,i in enumerate([1,3]):
                fits.writeto(root/f'frame{k}.fits',np.arange(100,dtype=np.uint16).reshape(10,10),
                             fits.Header({'DATE-AVG':str(rows[i].utc),'EXPTIME':.2,'TIMESYS':'UTC'}))
            cfg=dict(name='test',source=str(root),source_timestamp_reference='start',mapping_tolerance_s=1e-9)
            f=StationFrames(cfg,rows)
            self.assertEqual(f.mapping,{1:0,3:1})
            self.assertEqual(f.records[1]['source_midpoint_utc'],str(rows[1].utc))
            cfg['mapping_tolerance_s']=float('nan')
            with self.assertRaises(ValueError):StationFrames(cfg,rows)

    def test_reject_non_utc_fits_and_ambiguous_duplicate_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=utc_ns('2026-09-12T09:54:20')
            fits.writeto(root/'one.fits',np.ones((3,3)),fits.Header({'DATE-OBS':str(base),'EXPTIME':.2,'TIMESYS':'TAI'}))
            rows=[MediaSample(i,base+np.timedelta64(i*10,'ms'),.2,100.) for i in range(3)]
            cfg=dict(name='test',source=str(root),source_timestamp_reference='midpoint',mapping_tolerance_s=.1)
            with self.assertRaisesRegex(ValueError,'TIMESYS'):StationFrames(cfg,rows)
            with fits.open(root/'one.fits',mode='update') as hdus:hdus[0].header['TIMESYS']='UTC'
            with self.assertRaisesRegex(ValueError,'same source image'):StationFrames(cfg,rows)

    def test_saved_pyote_midnight_and_no_half_exposure_shift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'native_results.json'
            base=utc_ns('2026-09-12T23:59:59.6')
            rows=[MediaSample(i,base+np.timedelta64(i*200,'ms'),.2,100.) for i in range(8)]
            result=dict(timesAreValid=True,Dframe=1.5,Rframe=4.5,Dtime=86399.9,Rtime=.5,mode='raw')
            path.write_text(json.dumps(result))
            d,r,_=saved_transitions(dict(pyote_result=str(path)),rows)
            self.assertEqual(d,utc_ns('2026-09-12T23:59:59.9'))
            self.assertEqual(r,utc_ns('2026-09-13T00:00:00.5'))
            result['Rtime']=240.5;path.write_text(json.dumps(result))
            with self.assertRaises(ValueError):saved_transitions(dict(pyote_result=str(path)),rows)

    def test_native_normalized_counts_use_matching_raw_tracking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw.csv';norm=root/'native_analysis.csv'
            raw.write_text('# PyMovie\nFrameNum,timeInfo,signal-target,xcentroid-target,ycentroid-target,hit-defect-target\n'
                '0,[09:54:20.1234567],100,4,5,0\n1,[09:54:20.3234567],-12,6,7,1\n2,[09:54:20.5234567],100,8,9,0\n')
            norm.write_text('FrameNum,timeInfo,signal-target\n0,[09:54:20.1234567],99.5\n1,[09:54:20.3234567],-11.7\n2,[09:54:20.5234567],101.8\n')
            cfg=dict(curve_format='pymovie_csv',curve=str(norm),tracking_csv=str(raw),target_column='signal-target',timestamp_reference='start',exposure_s=.2)
            rows,native,_,_=read_station_curve(cfg,'2026-09-12')
            self.assertEqual(rows[0].utc,utc_ns('2026-09-12T09:54:20.2234567'))
            self.assertEqual(rows[1].counts,-11.7);self.assertEqual(rows[1].target_xy,(6.,7.));self.assertFalse(rows[1].valid)
            norm.write_text(norm.read_text().replace('09:54:20.3234567','09:54:20.3234568'))
            with self.assertRaisesRegex(ValueError,'Tracking CSV'):read_station_curve(cfg,'2026-09-12')


if __name__=='__main__':unittest.main()
