"""Check signed chord ordering against analytic motion and the Altona prediction."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
from occultation_media.compute_shadow_geometry import EARTH_A_KM
from occultation_media.compute_station_path_offset import station_path_offset
from occultation_media.plan_station_timeline import order_stations
from occultation_media.read_occult_prediction import parse_prediction
from occultation_media.gui_config import build_config
from occultation_media.gui_observer import DEFAULTS

PREDICTION=Path(__file__).resolve().parents[1]/'examples/altona_20260912.occelmnt'


class LinearGeometry:
    """Analytic rotating-site analogue; positions in radii and time in seconds."""
    epoch=np.datetime64('2026-09-12T23:59:50','ns')
    def __init__(self,velocity=(.005,-.002),site_speed=.0001,visible=True):
        self.velocity=np.array(velocity);self.site_speed=site_speed;self.visible=visible
    def seconds(self,utc):return float((utc-self.epoch)/np.timedelta64(1,'s'))
    def center_xy(self,utc):return self.velocity*self.seconds(utc)
    def site_star_sine(self,lat,lon,utc):return 1 if self.visible else -1
    def site_xyz(self,lat,lon,utc,altitude=0):
        return np.array([lon/1000+self.site_speed*self.seconds(utc),(lat+.2*lon)/1000,1 if self.visible else -1])


class StationPathOrderTests(unittest.TestCase):
    def test_closest_approach_and_signed_offset_match_linear_solution(self):
        station=dict(name='A',latitude_deg=-37,longitude_deg=145)
        q=np.array([.145,-.008])
        for velocity in ((.005,-.002),(-.005,.002)):
            geometry=LinearGeometry(velocity)
            v=geometry.velocity-[geometry.site_speed,0]
            t=float(q@v/(v@v))
            # For this affine model d(site_xy)/d(latitude) is (0, 0.001).
            normal=np.array([-v[1],v[0]])/np.linalg.norm(v)
            if normal[1]<0:normal=-normal
            result=station_path_offset(geometry,station)
            self.assertEqual(result['status'],'computed')
            found=float((np.datetime64(result['closest_approach_utc'])-geometry.epoch)/np.timedelta64(1,'s'))
            self.assertAlmostEqual(found,t,delta=.0001)
            self.assertAlmostEqual(result['cross_track_km'],float(q@normal*EARTH_A_KM),delta=.002)
            self.assertLess(abs(result['along_track_residual_km']),.002)

    def test_path_order_can_reverse_latitude_order_and_unknowns_stay_last(self):
        stations=[dict(config=dict(name='Higher latitude',latitude_deg=-37,longitude_deg=145)),
                  dict(config=dict(name='Lower latitude',latitude_deg=-45,longitude_deg=169)),
                  dict(config=dict(name='Unknown 1')),dict(config=dict(name='Unknown 2'))]
        ordered=order_stations(stations,'path_north_to_south',LinearGeometry())
        self.assertEqual([s['config']['name'] for s in ordered],['Lower latitude','Higher latitude','Unknown 1','Unknown 2'])
        self.assertEqual(ordered[-1]['path_offset']['reason'],'missing_coordinates')
        with self.assertRaises(ValueError):order_stations(stations,'path_north_to_south')
        self.assertEqual(station_path_offset(LinearGeometry(visible=False),stations[0]['config'])['status'],'unavailable')
        meridional=LinearGeometry((0,.005),site_speed=0)
        self.assertEqual(station_path_offset(meridional,stations[0]['config'])['reason'],'geographic_north_side_undefined')

    def test_real_altona_path_order_includes_different_longitudes_and_times(self):
        geometry=parse_prediction(PREDICTION.read_text(encoding='utf-8'))
        coordinates=[('Unimelb 2',-37.7833333,145.2427778),('Unimelb 1',-37.8269444,145.2080556),
                     ('Peter Shottle',-37.9255142,145.2671051),('R. Paine',-45.0458333,169.2102778)]
        stations=[dict(config=dict(name=n,latitude_deg=lat,longitude_deg=lon),D=None,R=None) for n,lat,lon in coordinates]
        ordered=order_stations(stations,'path_north_to_south',geometry)
        self.assertEqual([s['config']['name'] for s in ordered],['R. Paine','Unimelb 2','Unimelb 1','Peter Shottle'])
        self.assertGreater(ordered[0]['path_offset']['cross_track_km'],0)
        self.assertLess(ordered[1]['path_offset']['cross_track_km'],0)
        for s in ordered:
            self.assertLess(abs(s['path_offset']['along_track_residual_km']),.002)
            self.assertIsNone(s['D']);self.assertIsNone(s['R'])
        times=[np.datetime64(s['path_offset']['closest_approach_utc']) for s in ordered]
        self.assertGreater(float((times[0]-times[1])/np.timedelta64(1,'s')),200)

    def test_desktop_path_order_uses_prediction_even_without_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);curve=root/'curve.csv';source=root/'source.ser';curve.touch();source.touch()
            source.with_suffix('.CameraSettings.txt').write_text('Exposure=200ms\n')
            event=dict(event='Altona',target='Star',date_utc='2026-09-12',window_mode='full',step_s='.2',
                       language='en',output_root=tmp,station_order='path_north_to_south',
                       shadow_enabled='0',shadow_prediction_file=str(PREDICTION))
            observer={**DEFAULTS,'curve':str(curve),'source':str(source),'latitude_deg':'-37.78','longitude_deg':'145.24'}
            cfg=build_config(event,[{**observer,'name':'Melbourne'},
                                  {**observer,'name':'NZ','latitude_deg':'-45.0458333','longitude_deg':'169.2102778'}])
            self.assertEqual([s['name'] for s in cfg['stations']],['NZ','Melbourne'])
            self.assertFalse(cfg['shadow_simulation']['enabled'])
            with self.assertRaises(ValueError):build_config({**event,'shadow_prediction_file':''},[observer])
