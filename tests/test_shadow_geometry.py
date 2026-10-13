"""Numerical and input-contract checks for the supplied Altona prediction."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import numpy as np
from occultation_media.read_occult_prediction import parse_prediction,load_prediction,form_settings

XML='''<Occultations><Event>
<Elements>JPL#79,8.17,2026,9,12,9.8753005,-0.0949742,-0.1689929,4.5924730,-2.5776256,0.0053027,0.0003957,0.0000005,0.0000001</Elements>
<Earth>141.4193,-22.8036,30.95,4.09,False</Earth>
<Star>UCAC4 336-171713,18.70423466,-22.8294285,14.36,13.95,13.37,0,0,,18.73146372,-22.8036164,1.11,0.93,0,0,0</Star>
<Object>850,Altona,14.55,76.200,2.1756</Object>
</Event></Occultations>'''


class GeometryTests(unittest.TestCase):
    def test_known_center_and_inverse_projection(self):
        geometry=parse_prediction(XML)
        self.assertEqual(str(geometry.epoch),'2026-09-12T09:52:31.081800000')
        center=geometry.project_surface(geometry.center_xy(geometry.epoch),geometry.epoch)
        # Independently computed ray/ellipsoid baseline from the original map.
        np.testing.assert_allclose(center,[-32.5958,134.9529],atol=.0001)
        for seconds in range(-500,501,50):
            t=geometry.epoch+np.timedelta64(seconds,'s')
            xy=geometry.center_xy(t)
            point=geometry.project_surface(xy,t)
            np.testing.assert_allclose(geometry.site_xyz(*point,t)[:2],xy,atol=1e-12)
            rim=geometry.footprint(t)
            fp=np.array([geometry.site_xyz(*point,t)[:2] for point in rim])
            radius=np.linalg.norm(fp-xy,axis=1)*6378.14
            np.testing.assert_allclose(radius,38.1,atol=1e-8)

    def test_observer_coverage_and_no_extrapolation(self):
        geometry=parse_prediction(XML)
        t=np.datetime64('2026-09-12T09:54:30.161069','ns')
        state=geometry.site_state(dict(latitude_deg=-37.8136,longitude_deg=144.9631),t)
        self.assertTrue(state['nominally_covered'])
        self.assertAlmostEqual(state['distance_fp_km'],15.03739178,places=5)
        self.assertIsNone(geometry.site_state({},t))
        self.assertTrue(np.isnan(geometry.project_surface([2,2],t)).all())
        with self.assertRaisesRegex(ValueError,'one hour'):geometry.center_xy(t+np.timedelta64(1,'D'))
        with self.assertRaises(ValueError):geometry.center_xy(np.datetime64('NaT','ns'))

    def test_inputs_disabled_file_bom_and_date_validation(self):
        self.assertEqual(load_prediction({'enabled':False,'prediction_file':'missing'}),(None,None,[]))
        self.assertEqual(form_settings({'shadow_enabled':'0'}),{'enabled':False})
        self.assertEqual(form_settings({'shadow_enabled':'1'},quality_only=True),{'enabled':False})
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'预测.occelmnt';path.write_text(XML,encoding='utf-8-sig')
            geometry,evidence,paths=load_prediction({'enabled':True,'prediction_file':str(path)},'2026-09-12')
            self.assertEqual(geometry.object_name,'Altona');self.assertEqual(paths,[path.resolve()])
            self.assertFalse(evidence['uncertainty_included'])
            with self.assertRaisesRegex(ValueError,'date differs'):
                load_prediction({'enabled':True,'xml':XML},'2026-09-13')
        for settings in ({'enabled':True},{'enabled':True,'xml':XML,'prediction_file':'anything'},
                         {'enabled':'yes'},{'enabled':True,'xml':'bad'}):
            with self.assertRaises(ValueError):load_prediction(settings)
        with self.assertRaises(ValueError):parse_prediction(XML.replace('76.200','nan'))
        with self.assertRaises(ValueError):parse_prediction(XML.replace('76.200','-1'))
        with self.assertRaises(ValueError):parse_prediction(XML.replace('</Event>','</Event><Event/>'))


if __name__=='__main__':unittest.main()
