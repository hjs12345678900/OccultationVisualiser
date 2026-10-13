"""Verify continuous transit, exact D/R margins and presentation-only speed."""
from types import SimpleNamespace
import unittest
import numpy as np
from occultation_media.plan_station_timeline import plan_timeline
from occultation_media.render_utc_axis import UtcAxis


class AcceleratedGapTests(unittest.TestCase):
    def stations(self):
        epoch=np.datetime64('2026-09-12T23:59:50','ns')
        return [dict(config=dict(name=str(k)),D=epoch+np.timedelta64(k*240,'s'),
                     R=epoch+np.timedelta64(k*240+2,'s'),rows=[SimpleNamespace(utc=epoch)]) for k in range(2)]

    def test_five_second_margins_and_smooth_midnight_transit(self):
        stations=self.stations()
        cfg=dict(window_mode='dr',step_s=.2,gap_mode='accelerate',gap_speed=50)
        times,holds,intervals,plan=plan_timeline(cfg,stations)
        self.assertEqual(times[0],stations[0]['D']-np.timedelta64(5,'s'))
        self.assertEqual(intervals[-1][1],stations[1]['R']+np.timedelta64(5,'s'))
        self.assertEqual(plan['skipped_gaps'],[])
        gap=plan['accelerated_gaps'][0]
        self.assertEqual(gap['duration_s'],228)
        self.assertAlmostEqual(gap['presentation_duration_s'],4.56)
        self.assertAlmostEqual(holds.sum(),24+4.56)
        self.assertTrue((np.diff(times)>np.timedelta64(0,'ns')).all())
        self.assertLessEqual(np.diff(times).max(),np.timedelta64(2,'s'))
        for sample,hold in zip(times,holds):
            rate=50 if intervals[1][0]<=sample<intervals[1][1] else 1
            self.assertLessEqual(hold,.04+1e-10 if rate==50 else .2+1e-10)
        axis=UtcAxis(intervals,durations=plan['axis_durations_s'])
        self.assertIsNotNone(axis.position(np.datetime64('2026-09-13T00:01:00','ns')))
        self.assertEqual(axis.segments[0][3],axis.segments[1][2])
        self.assertEqual(axis.segments[1][3],axis.segments[2][2])
        self.assertAlmostEqual((axis.segments[1][3]-axis.segments[1][2])/(axis.segments[0][3]-axis.segments[0][2]),4.56/12)
        fixed=plan_timeline({**cfg,'playback_mode':'fixed_duration','video_duration_s':10},stations)
        np.testing.assert_array_equal(times,fixed[0])
        self.assertAlmostEqual(fixed[1].sum(),10)
        self.assertAlmostEqual(sum(fixed[3]['axis_durations_s']),10)
        self.assertAlmostEqual(fixed[3]['accelerated_gaps'][0]['presentation_duration_s'],4.56*10/28.56)
        self.assertEqual(stations[0]['D'],np.datetime64('2026-09-12T23:59:50','ns'))

    def test_merged_windows_and_invalid_acceleration(self):
        stations=self.stations()
        cfg=dict(window_mode='dr',step_s=.2,gap_mode='accelerate')
        stations[1]['D']=stations[0]['D']+np.timedelta64(1,'s')
        stations[1]['R']=stations[0]['R']+np.timedelta64(1,'s')
        _,holds,intervals,info=plan_timeline(cfg,stations)
        self.assertEqual(len(intervals),1)
        self.assertEqual(info['accelerated_gaps'],[])
        self.assertAlmostEqual(holds.sum(),13)
        for speed in (1,0,-2,float('nan'),float('inf')):
            with self.assertRaises(ValueError):plan_timeline({**cfg,'gap_speed':speed},stations)
        with self.assertRaises(ValueError):plan_timeline({**cfg,'gap_mode':'unknown'},stations)
        with self.assertRaises(ValueError):plan_timeline({**cfg,'event_padding_s':1000,'step_s':.01},stations)
