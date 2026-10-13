"""Exercise native PyOTE text imports without fitting or camera correction."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
from occultation_media.read_pyote_result import read_pyote_result
from occultation_media.inspect_observer_metadata import resolve_native_mode
from occultation_media.read_saved_transitions import saved_transitions
from occultation_media.read_saved_snr import station_snr, snr_label
from occultation_media.station_sample import MediaSample
from test_utf8_saved_results import ansi_default

HEADER = 'aperture name,time err +/-secs,DNR,FP metric,magDrop,percent drop,duration (secs),D time,R time,D frame,R frame,B,A,sigmaB,sigmaA,observed drop,FP drop,FP margin\n'
ROW = 'signal-star,.2,6,1,.3,60,.6,[09:54:00.3000],[09:54:00.9000],11.5,14.5,100,40,10,5,60,20,40\n'
LOG = r"""#################### PYOTE 5.4.2 session started: test ####################
filename: C:\obs\curve.csv
timeDelta: 0.4 seconds per block
Timestamps appear valid @ D and R
Block integration of size 2 has been applied to this light curve.
All times are calculated/reported based on the assumption that timestamps are start-of-exposure times.
D: 0.9500 containment intervals:  {+/- 0.2} seconds
R: 0.9500 containment intervals:  {+/- 0.3} seconds
fit metrics for signal-star
fit metrics === B: 100.00  A: 40.00 sigmaB: 10.00  sigmaA: 5.00
fit metrics === D frame number: 11.5000
fit metrics === R frame number: 14.5000
fit metrics === D time: [09:54:00.3000]
fit metrics === R time: [09:54:00.9000]
"""


class NativePyoteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'fit_metrics.txt'
        self.cfg = dict(name='Test', curve='curve.csv', target_column='signal-star',
                        pyote_result=str(self.path), native_mode='raw')
        self.epoch = np.datetime64('2026-09-12T09:54:00', 'ns')
        self.rows = [MediaSample(10+i,self.epoch+np.timedelta64(i*200,'ms'),.2,100) for i in range(8)]

    def write_metrics(self, row=ROW):
        self.path.write_text(HEADER+'\nSource file is '+r'C:\obs\curve.csv'+'\n\n'+row,encoding='utf-8-sig')

    def test_native_metrics_frame_utc_snr_under_cp1252_default(self):
        self.write_metrics()
        with ansi_default():
            self.assertEqual(resolve_native_mode(dict(self.cfg,native_mode='auto')),'raw')
            d,r,info = saved_transitions(self.cfg,self.rows)
            self.assertEqual(d,self.epoch+np.timedelta64(300,'ms'))
            self.assertEqual(r,self.epoch+np.timedelta64(900,'ms'))
            self.assertEqual(info['result_format'],'pyote_fit_metrics')
            self.assertIsNone(info['errors95_s']['D'])
            snr=station_snr(self.cfg,self.rows,d,r)
            self.assertEqual(snr['snr'],10)
            self.assertEqual(snr['dnr'],6)
            self.assertIn('PyOTE fit',snr_label(snr))
            self.assertFalse(info['camera_corrections_applied_by_importer'])

    def test_log_retains_sampling_and_95_errors_without_exposure_inference(self):
        self.path.write_text(LOG,encoding='utf-8')
        d,r,info=saved_transitions(self.cfg,self.rows)
        self.assertEqual(info['errors95_s'],{'D':.2,'R':.3})
        self.assertEqual(info['timestamp_assumption'],'start')
        snr=station_snr(self.cfg,self.rows,d,r)
        self.assertEqual(snr['integration_readings'],2)
        self.assertEqual(snr['fitted_cadence_s'],.4)
        self.assertEqual(snr_label(snr),'SNR 10.00 (PyOTE 2 readings)')

    def test_matching_target_and_source_is_required(self):
        self.write_metrics()
        for fields in (dict(target_column='signal-other'),dict(curve='unrelated.csv')):
            with self.subTest(fields=fields),self.assertRaisesRegex(ValueError,'no fit matches'):
                read_pyote_result(dict(self.cfg,**fields))
        self.assertEqual(read_pyote_result(dict(self.cfg,curve='curve.pyote.csv'))['B'],100)

    def test_multiple_apertures_and_explicit_repeated_fit_choice(self):
        self.write_metrics(ROW.replace('signal-star','signal-reference')+ROW+ROW.replace(',100,40,10,',',120,40,10,'))
        with self.assertRaisesRegex(ValueError,'matching fits'):
            read_pyote_result(self.cfg)
        self.assertEqual(read_pyote_result(dict(self.cfg,pyote_fit_index=2))['B'],120)
        with self.assertRaisesRegex(ValueError,'outside'):
            read_pyote_result(dict(self.cfg,pyote_fit_index=3))

    def test_duplicate_identical_reports_are_safe(self):
        self.write_metrics(ROW+ROW)
        self.assertEqual(read_pyote_result(self.cfg)['B'],100)

    def test_corrupt_utc_and_missing_pair_rejected(self):
        for row in (ROW.replace('[09:54:00.3000]','[29:54:00.3]'),ROW.replace('[09:54:00.3000]','[09:55:00.3]')):
            self.write_metrics(row)
            with self.assertRaises(ValueError):saved_transitions(self.cfg,self.rows)
        self.path.write_text(LOG.replace('fit metrics === R time: [09:54:00.9000]',''),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'incomplete D/R'):read_pyote_result(self.cfg)

    def test_invalid_log_timestamps_rejected(self):
        for log in (LOG.replace('Timestamps appear valid @ D and R','Times are invalid due to corrupted timestamps!'),LOG.replace('Timestamps appear valid @ D and R','')):
            self.path.write_text(log,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'times are invalid'):saved_transitions(self.cfg,self.rows)

    def test_later_incomplete_fit_does_not_fall_back(self):
        self.path.write_text(LOG+'\nfit metrics for signal-star\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'matching fits'):read_pyote_result(self.cfg)
        with self.assertRaisesRegex(ValueError,'incomplete'):read_pyote_result(dict(self.cfg,pyote_fit_index=2))

    def test_windows_cp1252_native_text_and_bom_unicode(self):
        for encoding,source in (('cp1252',r'C:\café\curve.csv'),('utf-8-sig',r'C:\运行\curve.csv')):
            self.path.write_bytes((HEADER+'Source file is '+source+'\n'+ROW).encode(encoding))
            with ansi_default():self.assertEqual(read_pyote_result(self.cfg)['sigmaB'],10)

    def test_wrong_text_binary_and_csv_have_useful_errors(self):
        for data in (b'not a fit result',b'RIFF\x00\x90bad'):
            self.path.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'PyOTE:'):read_pyote_result(self.cfg)
        with self.assertRaisesRegex(ValueError,'Light curve'):
            read_pyote_result(dict(self.cfg,pyote_result='wrong.pyote.csv'))

    def test_processed_curve_uses_exact_sparse_raw_tracking(self):
        from occultation_media.read_station_curves import read_station_curve
        raw,processed=Path(self.temp.name)/'curve.csv',Path(self.temp.name)/'curve.pyote.csv'
        raw.write_text('FrameNum,timeInfo,signal-star,xcentroid-star,ycentroid-star\n'
            '0,[09:54:00.0],100,10,20\n1,[09:54:00.2],100,11,21\n2,[09:54:00.4],40,12,22\n'
            '3,[09:54:00.6],40,13,23\n4,[09:54:00.8],100,14,24\n',encoding='utf-8')
        processed.write_text('FrameNum,timeInfo,signal-star\n0,[09:54:00.0],99\n2,[09:54:00.4],39\n4,[09:54:00.8],101\n',encoding='utf-8')
        cfg=dict(curve=str(processed),tracking_csv=str(raw),curve_format='pymovie_csv',
                 target_column='signal-star',exposure_s=.2,timestamp_reference='start')
        rows,_,_,_=read_station_curve(cfg,'2026-09-12')
        self.assertEqual([r.target_xy for r in rows],[(10,20),(12,22),(14,24)])
        self.assertEqual([r.counts for r in rows],[99,39,101])
        processed.write_text(processed.read_text(encoding='utf-8').replace('09:54:00.4','09:54:00.41'),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Tracking CSV'):read_station_curve(cfg,'2026-09-12')
        cfg.pop('tracking_csv');cfg['target_xy']=[30,40]
        rows,_,_,_=read_station_curve(cfg,'2026-09-12')
        self.assertEqual(rows[0].target_xy,(30,40))

    def test_log_selection_scopes_new_sessions_and_timestamp_failures(self):
        second=LOG.replace('session started: test','session started: second').replace('B: 100.00','B: 120.00')
        self.path.write_text(LOG+second,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'matching fits'):read_pyote_result(self.cfg)
        self.assertEqual(read_pyote_result(dict(self.cfg,pyote_fit_index=2))['B'],120)
        self.path.write_text(LOG+second.replace('Timestamps appear valid @ D and R','Times are invalid due to corrupted timestamps!'),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'times are invalid'):
            saved_transitions(dict(self.cfg,pyote_fit_index=2),self.rows)

    def test_midnight_keeps_dates_and_fractional_frame_identity(self):
        self.write_metrics(ROW.replace('[09:54:00.3000]','[23:59:59.9000]').replace('[09:54:00.9000]','[00:00:00.5000]'))
        epoch=np.datetime64('2026-09-12T23:59:59.600','ns')
        rows=[MediaSample(10+i,epoch+np.timedelta64(i*200,'ms'),.2,100) for i in range(8)]
        d,r,_=saved_transitions(self.cfg,rows)
        self.assertEqual(str(d),'2026-09-12T23:59:59.900000000')
        self.assertEqual(str(r),'2026-09-13T00:00:00.500000000')


if __name__=='__main__':unittest.main()
