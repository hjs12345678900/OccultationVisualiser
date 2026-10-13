"""Check path-aligned geography and measurable silhouette motion on the map."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np
from occultation_media.project_shadow_path_map import PathMapProjection
from occultation_media.read_occult_prediction import parse_prediction
from occultation_media.plan_shadow_simulation import ShadowSimulation
from occultation_media.render_shadow_map import ShadowMapPanel

PREDICTION=Path(__file__).resolve().parents[1]/'examples/altona_20260912.occelmnt'


class MapProjectionTests(unittest.TestCase):
    def test_oblique_grid_puts_path_left_to_right_and_handles_dateline(self):
        for start,end in [([-37.8,145],[-45,169]),([10,179],[10,-179])]:
            projection=PathMapProjection(start,end)
            xy=projection.project([start,end])
            self.assertLess(xy[0,0],xy[1,0])
            np.testing.assert_allclose(xy[:,1],0,atol=1e-8)
            np.testing.assert_allclose(projection.basis@projection.basis.T,np.eye(3),atol=1e-12)
        fallback=PathMapProjection([90,0],[90,0])
        self.assertTrue(np.isfinite(fallback.project([90,0])).all())

    def test_off_earth_center_never_draws_a_path_between_stations(self):
        geometry=parse_prediction(PREDICTION.read_text(encoding='utf-8'))
        start=geometry.epoch+np.timedelta64(45,'m')
        times=np.array([start,start+np.timedelta64(1,'s')])
        stations=[dict(config=dict(name='A',latitude_deg=-37,longitude_deg=145)),
                  dict(config=dict(name='B',latitude_deg=-45,longitude_deg=169))]
        simulation=ShadowSimulation(geometry,{},stations,times)
        panel=ShadowMapPanel(simulation,'en')
        self.assertFalse(panel.has_shadow_path)
        self.assertIsNone(simulation.position(start))
        self.assertEqual(panel.render(start,[None,None]).size,(1920,540))

    def test_full_width_map_scale_colors_and_moving_silhouette(self):
        geometry=parse_prediction(PREDICTION.read_text(encoding='utf-8'))
        start=np.datetime64('2026-09-12T09:54:20','ns')
        times=start+np.arange(61)*np.timedelta64(400,'ms')
        stations=[dict(config=dict(name='Station',latitude_deg=-37.8136,longitude_deg=144.9631))]
        simulation=ShadowSimulation(geometry,{},stations,times)
        panel=ShadowMapPanel(simulation,'en')
        self.assertEqual(panel.rect[2],1884)
        self.assertGreater(panel.rect[2]-panel.rect[0],1800)
        a,b=panel.map_pixels(panel.path[[0,-1]])
        self.assertGreater(b[0]-a[0],300)
        self.assertLess(abs(b[1]-a[1]),1e-6)
        # Equal projected-km scales: geography is not stretched into a strip.
        p=panel.map_pixels([[0,0],[10,0],[0,10]])
        self.assertAlmostEqual(p[1,0]-p[0,0],p[0,1]-p[2,1])
        first=np.array(panel.render(times[0],[None]));last=np.array(panel.render(times[-1],[None]))
        dark=lambda image: (image[58:488,36:1884,:].max(axis=2)<26)
        def center(mask):
            y,x=np.nonzero(mask);return x.mean(),y.mean()
        self.assertGreater(center(dark(last))[0]-center(dark(first))[0],300)
        color=np.array([92,170,255])
        self.assertTrue((first==color).all(axis=2).any())
        self.assertTrue((last==color).all(axis=2).any())

    def test_city_labels_and_compass_follow_rotated_geography(self):
        geometry=parse_prediction(PREDICTION.read_text(encoding='utf-8'))
        times=np.array(['2026-09-12T09:54:20','2026-09-12T09:58:20'],dtype='datetime64[ns]')
        stations=[dict(config=dict(name='A',latitude_deg=-37.8,longitude_deg=145.2)),
                  dict(config=dict(name='B',latitude_deg=-45.05,longitude_deg=169.21))]
        panel=ShadowMapPanel(ShadowSimulation(geometry,{},stations,times),'en')
        cities=[label[0] for label in panel.landmarks.labels]
        self.assertIn('Melbourne',cities)
        self.assertIn('Dunedin',cities)
        reference=panel.landmarks.reference
        p=panel.map_pixels(panel.projection.project([reference,reference+[.001,0]]))
        north=p[1]-p[0];north/=np.linalg.norm(north)
        np.testing.assert_allclose(panel.landmarks.north,north,atol=1e-9)
        self.assertGreater(abs(north[0]),.1)  # Geographic north is rotated too.
        points=np.array([[-37.8,145],[-45,169],[10,179]])
        np.testing.assert_allclose(panel.projection.inverse(panel.projection.project(points)),points,atol=1e-9)


if __name__=='__main__':unittest.main()
