"""Check optional color persistence and shared station/map export identity."""
from pathlib import Path
import tempfile
import unittest
from occultation_media.resolve_station_colors import station_colors, normalize_color, color_hex, PALETTE
from occultation_media.migrate_desktop_project import migrate_project
from occultation_media.gui_observer import DEFAULTS
from occultation_media.self_test_shadow import verify


class StationColorTests(unittest.TestCase):
    def test_auto_eight_colors_reserve_manual_and_preserve_old_four(self):
        self.assertEqual([color_hex(c) for c in station_colors([{}]*4)],list(PALETTE[:4]))
        configs=[{},dict(color=PALETTE[0]),{},dict(color='#123abc'),{},{},{},{}]
        colors=[color_hex(c) for c in station_colors(configs)]
        self.assertEqual(len(set(colors)),8)
        self.assertEqual(colors[1],PALETTE[0]);self.assertEqual(colors[3],'#123ABC')
        self.assertEqual(configs[0],{})
        self.assertEqual(len(set(station_colors([{}]*8))),8)
        self.assertEqual(station_colors([{'color':'#FFFFFF'}]*2),[(255,255,255)]*2)
        for bad in ('red','#123','#aabbccff','123456',123):
            with self.assertRaises(ValueError):normalize_color(bad)

    def test_saved_and_old_projects_keep_custom_or_automatic(self):
        data=dict(gui_version=1,event={},observers=[dict(DEFAULTS,color='#12ab34'),dict(name='Old')])
        _,obs=migrate_project(data,DEFAULTS)
        self.assertEqual(obs[0]['color'],'#12ab34');self.assertEqual(obs[1]['color'],'')
        self.assertEqual(normalize_color('  '),'');self.assertEqual(normalize_color(None),'')

    def test_sorted_bilingual_export_colors_match_map_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(verify(Path(tmp))['custom_station_colors'])
