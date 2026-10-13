"""Regression checks for sample-cadence selection and caption-safe display."""
import unittest
import numpy as np
from occultation_media.station_sample import MediaSample
from occultation_media.prepare_station_frames import nearest_sample
from occultation_media.resolve_image_stretch import image_limits,stretch_pixels


class AviDisplayTests(unittest.TestCase):
    def test_sparse_pyote_samples_do_not_go_blank_between_shutter_intervals(self):
        start=np.datetime64('2024-05-16T14:17:23.020','ns')
        rows=[MediaSample(2*i,start+np.timedelta64(80*i,'ms'),.04,100) for i in range(8)]
        for offset in (40,120,200,280,360,440,520):
            self.assertIsNotNone(nearest_sample(rows,start+np.timedelta64(offset,'ms')))
        self.assertTrue(all(r.exposure_s==.04 for r in rows))
        self.assertIsNone(nearest_sample(rows,start-np.timedelta64(1,'ms')))
        self.assertIsNone(nearest_sample(rows,start+np.timedelta64(561,'ms')))

    def test_long_gaps_stay_blank_with_sparse_curve(self):
        start=np.datetime64('2024-05-16','ns')
        rows=[MediaSample(i,start+np.timedelta64(t,'ms'),.04,100) for i,t in enumerate((0,80,160,10000,10080))]
        self.assertIsNone(nearest_sample(rows,start+np.timedelta64(5000,'ms')))
        self.assertIsNotNone(nearest_sample(rows,start+np.timedelta64(120,'ms')))

    def test_only_three_samples_do_not_inflate_support_across_a_gap(self):
        start=np.datetime64('2024-05-16','ns')
        rows=[MediaSample(i,start+np.timedelta64(t,'ms'),.04,100) for i,t in enumerate((0,80,100000))]
        self.assertIsNone(nearest_sample(rows,start+np.timedelta64(90000,'ms')))

    def test_short_timestamp_jitter_does_not_blank_regular_sampling(self):
        start=np.datetime64('2024-05-16','ns')
        rows=[MediaSample(2*i,start+np.timedelta64(t,'ms'),.04,100) for i,t in enumerate((0,80,160,222,320,400,480,560))]
        for offset in (40,120,360,440,520):
            self.assertIsNotNone(nearest_sample(rows,start+np.timedelta64(offset,'ms')))

    def test_caption_pixels_do_not_set_avi_auto_white_point(self):
        pixels=np.tile(np.arange(100)%20,(100,1)).astype(np.uint8)
        pixels[85:]=250
        before=pixels.copy()
        auto,evidence=image_limits(pixels,{},'AVI')
        old,_=image_limits(pixels,dict(image_stretch={'mode':'full'}),'AVI')
        self.assertLess(auto[1],old[1])
        self.assertEqual(evidence['level_region_xyxy'],[0,0,100,85])
        bright=stretch_pixels(pixels,auto,evidence)
        self.assertEqual(bright.shape,pixels.shape)
        np.testing.assert_array_equal(pixels,before)
        self.assertGreater(bright[50,10],stretch_pixels(pixels,old,evidence)[50,10])
        fits,_=image_limits(pixels,{},'FITS')
        self.assertEqual(fits,old)

    def test_manual_linear_display_is_fixed_and_does_not_measure_flux(self):
        cfg=dict(image_stretch=dict(mode='manual',black=10,white=110,strength=0))
        levels,evidence=image_limits(np.array([[10,60,110]]),cfg,'AVI')
        np.testing.assert_array_equal(stretch_pixels(np.array([[10,60,110]]),levels,evidence),[[0,128,255]])
        for settings in ({'mode':'manual','black':20,'white':10},{'mode':'auto','strength':-1}):
            with self.assertRaises(ValueError):image_limits(np.ones((10,10)),dict(image_stretch=settings),'AVI')


if __name__=='__main__':unittest.main()
