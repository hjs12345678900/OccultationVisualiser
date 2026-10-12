"""Check shared-UTC statistics, mask budgets and curve-only source evidence."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from occultation_media.station_sample import MediaSample
from occultation_media.measure_noise_profile import baseline_indices,noise_profile
from occultation_media.diagnose_noise_quality import diagnose_stations,pixel_noise_budget
from occultation_media.read_quality_context import read_quality_context
from occultation_media.station_cli import main
from occultation_media.gui_config import build_config
from occultation_media.gui_observer import DEFAULTS


class NoiseDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.epoch=np.datetime64('2026-09-12T09:54:00','ns')
        self.rows=[MediaSample(i,self.epoch+np.timedelta64(i,'s'),.4,100+i*2+(i%2)*3) for i in range(12)]

    def test_exposure_guards_and_shared_window(self):
        excluded=[(self.epoch+np.timedelta64(1800,'ms'),self.epoch+np.timedelta64(4200,'ms'))]
        self.assertEqual(baseline_indices(self.rows,excluded,(self.epoch,self.rows[7].utc)),[1,5,6])
        p=noise_profile(self.rows,[1,5,6])
        expected=[self.rows[i].counts for i in [1,5,6]]
        self.assertAlmostEqual(p['sigmaB'],np.std(expected,ddof=0))
        self.assertEqual(p['adjacent_pairs'],1)
        self.assertIsNone(p['adjacent_difference_sigma'])

    def test_diagnostic_detrending_does_not_replace_raw_noise(self):
        p=noise_profile(self.rows,list(range(12)))
        self.assertGreater(p['sigmaB'],p['linear_residual_sigma']*3)
        self.assertAlmostEqual(p['snr'],np.mean([r.counts for r in self.rows])/np.std([r.counts for r in self.rows]))
        self.assertEqual(self.rows[-1].counts,125)

    def test_background_mask_budget_and_normalized_unit_guard(self):
        aux={r.frame:dict(mask_pixels=-4 if r.frame<8 else 2,background_std=5) for r in self.rows}
        b=pixel_noise_budget(self.rows,list(range(12)),aux)
        self.assertEqual(b['aperture_sigma_estimate'],10)
        self.assertEqual(b['default_mask_samples'],8)
        self.assertEqual(b['other_mask_samples'],4)
        self.assertEqual(b['default_mask_profile']['samples'],8)
        self.assertFalse(pixel_noise_budget(self.rows,list(range(12)),aux,raw=False)['available'])

    def test_pairwise_utc_exclusion_and_unavailable_overlap(self):
        d=self.rows[4].utc;r=self.rows[6].utc
        configs=[dict(name=n,curve='unused.csv',curve_format='pymovie_csv') for n in ('A','B','C')]
        shifted=[MediaSample(x.frame,x.utc+np.timedelta64(1,'h'),x.exposure_s,x.counts) for x in self.rows]
        stations=[dict(config=c,rows=rows,D=rows[4].utc,R=rows[6].utc) for c,rows in zip(configs,[self.rows,self.rows,shifted])]
        with patch('occultation_media.diagnose_noise_quality.read_quality_context',return_value=({}, {}, [])):
            report,_=diagnose_stations(stations,1)
        pair=report['pairs'][0]
        self.assertTrue(pair['available']);self.assertAlmostEqual(pair['snr_ratio'],1)
        self.assertEqual(pair['profiles'][0]['frame_ids'],[1,2,8,9,10])
        self.assertFalse(report['pairs'][1]['available'])
        self.assertIn('No shared',report['pairs'][1]['reason'])
        self.assertEqual((stations[0]['D'],stations[0]['R']),(d,r))

    def test_pymovie_context_and_camera_settings_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'curve.csv';settings=path.with_suffix('.CameraSettings.txt')
            path.write_text('# aperture name: star\n# ____ def mask radius: 3.2\n#INSTRUMENT-SENSOR: imx296\n#IMAGE-BINNING-X: 1\n#IMAGE-BINNING-Y: 1\nFrameNum,timeInfo,signal-star,stdbkg-star,nmaskpx-star\n0,[09:54:00],100,5,-37\n')
            cfg=dict(curve=str(path),curve_format='pymovie_csv',target_column='signal-star')
            c,aux,paths=read_quality_context(cfg)
            self.assertEqual(c['camera'],'imx296');self.assertEqual(c['binning'],'1x1')
            self.assertEqual(aux[0]['mask_pixels'],-37)
            settings.write_text('[Recorded camera]\nBinning=2x2\nGain=200\n')
            c,_,paths=read_quality_context(cfg)
            self.assertEqual(c['camera'],'Recorded camera');self.assertIn(settings,paths)

    def test_curve_only_cli_and_gui_need_no_images_or_manual_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);curve=root/'native.csv'
            curve.write_text('FrameNum,timeInfo,signal-target\n'+'\n'.join(f'{r.frame},[{str(r.utc).split("T")[1]}],{r.counts}' for r in self.rows))
            obs=dict(DEFAULTS,curve=str(curve),exposure_ms='400',D_utc='09:54:04',R_utc='09:54:06')
            cfg=build_config(dict(event='Test',target='Star',date_utc='2026-09-12',step_s='0.1',language='both',output_root=str(root),start_utc='',end_utc=''),[obs],quality_only=True)
            self.assertNotIn('source',cfg['stations'][0])
            config=root/'config.json';config.write_text(json.dumps(cfg))
            out=main([str(config),'--quality-only','--output-dir',str(root/'report')])
            report=json.loads((out/'quality_report.json').read_text())
            self.assertTrue(report['stations'][0]['baseline']['available'])
            record=json.loads((out/'run_metadata.json').read_text())
            self.assertTrue(record['input_integrity_verified'])
            self.assertTrue((out/'quality_summary.csv').is_file())
            self.assertFalse((out/'media_metadata.json').exists())


if __name__=='__main__': unittest.main()
