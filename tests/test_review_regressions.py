"""Scientific and timing counterexamples found during the v1.16.0 review."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
import numpy as np
from occultation_media.read_occult_prediction import parse_prediction
from occultation_media.project_shadow_path_map import PathMapProjection
from occultation_media.compute_shadow_geometry import EARTH_A_KM
from occultation_media.read_tangra_photometry import parse_tangra_csv
from occultation_media.render_shadow_map import ShadowMapPanel
from occultation_media.plan_shadow_simulation import ShadowSimulation

PREDICTION=Path(__file__).resolve().parents[1]/'examples/altona_20260912.occelmnt'


class ReviewRegressions(unittest.TestCase):
    def test_geodetic_horizon_disagrees_with_geocentric_z(self):
        geometry=replace(parse_prediction(PREDICTION.read_text()),dec_rad=np.radians(-30),substar_lon_rad=0)
        lat=45.;lon=np.degrees(np.arccos(-np.tan(np.radians(lat))*np.tan(geometry.dec_rad)))+.05
        xyz=geometry.site_xyz(lat,lon,geometry.epoch)
        self.assertGreater(xyz[2],0)  # Old code falsely reported a visible star.
        normal=np.array([np.cos(np.radians(lat))*np.cos(np.radians(lon)),
                         np.cos(np.radians(lat))*np.sin(np.radians(lon)),np.sin(np.radians(lat))])
        star=np.array([np.cos(geometry.dec_rad),0,np.sin(geometry.dec_rad)])
        self.assertLess(normal@star,0)
        self.assertAlmostEqual(geometry.site_star_sine(lat,lon,geometry.epoch),normal@star)
        state=geometry.site_state(dict(latitude_deg=lat,longitude_deg=lon),geometry.epoch)
        self.assertFalse(state['star_above_horizon']);self.assertFalse(state['nominally_covered'])

    def test_altona_shape_is_fixed_in_fp_but_stretches_on_surface(self):
        geometry=parse_prediction(PREDICTION.read_text())
        times=np.array(['2026-09-12T09:54:23.412583057','2026-09-12T09:58:18'],dtype='datetime64[ns]')
        centers=[geometry.project_surface(geometry.center_xy(t),t) for t in times]
        projection=PathMapProjection(*centers)
        ratios=[]
        for utc in times:
            rim=geometry.footprint(utc,512)
            fp=np.array([geometry.site_xyz(*p,utc)[:2] for p in rim])
            np.testing.assert_allclose(np.linalg.norm(fp-geometry.center_xy(utc),axis=1)*EARTH_A_KM,38.1,atol=1e-8)
            xy=projection.project(rim)
            singular=np.linalg.svd(xy-xy.mean(axis=0),compute_uv=False)
            ratios.append(singular[0]/singular[1])
        np.testing.assert_allclose(ratios,[1.03890643,1.19177997],atol=1e-7)

    def test_legacy_tangra_midnight_and_whole_seconds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'curve.csv'
            path.write_text('FrameNo,Time (UT),Signal (1),Background (1)\n'
                            '100,23:59:59.800,110,10\n101,00:00:00,110,10\n102,00:00:00.300,20,10')
            rows,_=parse_tangra_csv(path,'2026-09-12')
            self.assertAlmostEqual((rows[1].time_utc-rows[0].time_utc).total_seconds(),.2)
            self.assertEqual(rows[1].time_utc.day,13)
            self.assertEqual(rows[2].net_flux_adu(1),10)

    def test_limb_rim_has_missing_vertices_documented_limitation(self):
        geometry=parse_prediction(PREDICTION.read_text())
        # A disk centered near the projected limb intersects Earth only partially.
        geometry=replace(geometry,coefficients=np.array([[.998,0],[0,0],[0,0],[0,0]]))
        rim=geometry.footprint(geometry.epoch)
        valid=np.isfinite(rim).all(axis=1)
        self.assertTrue(valid.any());self.assertFalse(valid.all())
        times=np.array([geometry.epoch,geometry.epoch+np.timedelta64(1,'s')])
        panel=ShadowMapPanel(ShadowSimulation(geometry,{},[],times),'en')
        self.assertEqual(panel.render(times[0],[]).size,(1920,540))
