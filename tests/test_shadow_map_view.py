"""Verify map-camera choices independently of physical geometry and clocks."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
from occultation_media.read_occult_prediction import parse_prediction, form_settings, load_prediction
from occultation_media.plan_shadow_simulation import ShadowSimulation
from occultation_media.render_shadow_map import ShadowMapPanel
from occultation_media.plan_shadow_map_view import ShadowMapView
from occultation_media.migrate_desktop_project import migrate_project
from occultation_media.gui_observer import DEFAULTS

PREDICTION=Path(__file__).resolve().parents[1]/'examples/altona_20260912.occelmnt'


class MapViewTests(unittest.TestCase):
    def setUp(self):
        self.geometry=parse_prediction(PREDICTION.read_text(encoding='utf-8'))
        self.times=np.array(['2026-09-12T09:54:20','2026-09-12T09:58:20'],dtype='datetime64[ns]')
        self.stations=[dict(config=dict(name='A',color='#E65A8D',latitude_deg=-37.8,longitude_deg=145.2))]

    def panel(self,mode=None):
        evidence={} if mode is None else {'view_mode':mode}
        return ShadowMapPanel(ShadowSimulation(self.geometry,evidence,self.stations,self.times),'en')

    def test_default_overview_and_explicit_overview_match(self):
        default,explicit=self.panel(),self.panel('full_path')
        original=explicit.midpoint.copy()
        for utc in self.times:
            np.testing.assert_array_equal(default.render(utc,[None]),explicit.render(utc,[None]))
            np.testing.assert_array_equal(explicit.midpoint,original)

    def test_follow_centers_shadow_with_fixed_scale_and_shared_translation(self):
        panel=self.panel('follow_shadow');overview=self.panel('full_path')
        np.testing.assert_array_equal(panel.projection.basis,overview.projection.basis)
        scale=panel.scale;center=np.array([960,273])
        station=panel.station_points[0][1];coast=panel.background.coasts[0][0]
        before=panel.map_pixels([station,coast])
        for utc in self.times:
            panel.render(utc,[None]);p=panel.simulation.position(utc)
            np.testing.assert_allclose(panel.screen(p['latitude_deg'],p['longitude_deg']),center)
            self.assertEqual(panel.scale,scale)
            reference=panel.landmarks.reference
            north=np.diff(panel.map_pixels(panel.projection.project([reference,reference+[.001,0]])),axis=0)[0]
            np.testing.assert_allclose(panel.landmarks.north,north/np.linalg.norm(north),atol=1e-9)
            # Instantaneous footprint stays inside the fixed following viewport.
            rim=panel.map_pixels(panel.projection.project(self.geometry.footprint(utc)))
            self.assertTrue((rim.min(axis=0)>[36,58]).all())
            self.assertTrue((rim.max(axis=0)<[1884,488]).all())
        delta=panel.map_pixels([station,coast])-before
        np.testing.assert_allclose(delta[0],delta[1],atol=1e-9)
        self.assertGreater(np.linalg.norm(delta[0]),100)
        self.assertEqual(tuple(panel.colors[0]),(230,90,141))

    def test_follow_out_of_order_and_off_earth_are_deterministic(self):
        panel=self.panel('follow_shadow')
        first=np.array(panel.render(self.times[0],[None]))
        panel.render(self.times[-1],[None])
        np.testing.assert_array_equal(first,panel.render(self.times[0],[None]))
        off=self.geometry.epoch+np.timedelta64(45,'m')
        self.assertIsNone(panel.simulation.position(off))
        panel.render(off,[None])
        np.testing.assert_array_equal(panel.midpoint,panel.camera.centers[-1])
        simulation=ShadowSimulation(self.geometry,{'view_mode':'follow_shadow'},self.stations,np.array([off,off+np.timedelta64(1,'s')]))
        missing=ShadowMapPanel(simulation,'en')
        self.assertFalse(missing.has_shadow_path)
        self.assertTrue(np.isfinite(missing.midpoint).all())
        self.assertEqual(missing.render(off,[None]).size,(1920,540))

    def test_mode_validation_form_and_old_project_migration(self):
        event=dict(shadow_enabled='1',shadow_prediction_file=str(PREDICTION),date_utc='2026-09-12')
        self.assertEqual(form_settings(event)['view_mode'],'full_path')
        settings=form_settings({**event,'shadow_view_mode':'follow_shadow'})
        self.assertEqual(load_prediction(settings)[1]['view_mode'],'follow_shadow')
        with self.assertRaises(ValueError):form_settings({**event,'shadow_view_mode':'invalid'})
        with self.assertRaises(ValueError):load_prediction({**settings,'view_mode':'invalid'})
        old,_=migrate_project(dict(gui_version=1,event={},observers=[]),DEFAULTS)
        self.assertEqual(old['shadow_view_mode'],'full_path')
        saved,_=migrate_project(dict(gui_version=1,event={'shadow_view_mode':'follow_shadow'},observers=[]),DEFAULTS)
        self.assertEqual(saved['shadow_view_mode'],'follow_shadow')


if __name__=='__main__':unittest.main()
