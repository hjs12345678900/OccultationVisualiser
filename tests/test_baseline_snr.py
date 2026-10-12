"""Check quality labels against saved parameters and whole-exposure selection."""
from pathlib import Path
import json
import tempfile
import unittest
import numpy as np
from occultation_media.station_sample import MediaSample
from occultation_media.measure_baseline_snr import baseline_snr
from occultation_media.read_saved_snr import station_snr, snr_label


class BaselineSnrTests(unittest.TestCase):
    def test_native_snr_separates_drop_ratio_and_rejects_bad_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'result.json'
            path.write_text(json.dumps(dict(B=100,A=40,sigmaB=10)))
            info=station_snr(dict(name='Native',pyote_result=str(path)),[],None,None)
            self.assertEqual(info['snr'],10)
            self.assertEqual(info['dnr'],6)
            self.assertFalse(info['estimated'])
            self.assertEqual(snr_label(info),'SNR 10.00')
            path.write_text(json.dumps(dict(B=100,sigmaB=0)))
            with self.assertRaises(ValueError):station_snr(dict(name='Native',pyote_result=str(path)),[],None,None)

    def test_whole_exposures_exclude_transition_and_bad_measurements(self):
        epoch=np.datetime64('2026-09-12T23:59:58','ns')
        # Frames 2/4 straddle D/R; 3 is low; 6 is a flagged outlier.
        values=[90,110,70,0,70,100,9999]
        rows=[MediaSample(i,epoch+np.timedelta64(i*500,'ms'),.5,v,tracking_flag=2 if i==6 else 0)
              for i,v in enumerate(values)]
        d=epoch+np.timedelta64(900,'ms');r=epoch+np.timedelta64(2100,'ms')
        info=baseline_snr(rows,d,r)
        self.assertEqual(info['baseline_frame_ids'],[0,1,5])
        self.assertEqual(info['B'],100)
        self.assertAlmostEqual(info['sigmaB'],np.std([90,110,100],ddof=0))
        self.assertAlmostEqual(info['snr'],12.2474487139)
        self.assertIn('估算',snr_label(info,'zh'))
        self.assertIn('estimated',snr_label(info,'en'))
        lc=station_snr(dict(curve='original.lc',curve_format='tangra_lc'),rows,d,r)
        self.assertEqual(lc['snr'],info['snr'])
        self.assertIn('LC 基线',snr_label(lc,'zh'))
        self.assertIn('LC baseline',snr_label(lc,'en'))
        self.assertFalse(info['detrended'])
        self.assertEqual([row.counts for row in rows],values)

    def test_unknown_baseline_and_zero_scatter_stay_unavailable(self):
        epoch=np.datetime64('2026-09-12','ns')
        rows=[MediaSample(i,epoch+np.timedelta64(i,'s'),.2,10) for i in range(6)]
        self.assertIsNone(baseline_snr(rows,None,None)['snr'])
        self.assertIsNone(baseline_snr(rows,epoch+np.timedelta64(2,'s'),epoch+np.timedelta64(3,'s'))['snr'])
        self.assertEqual(snr_label({'snr':None}),'SNR —')


if __name__=='__main__': unittest.main()
