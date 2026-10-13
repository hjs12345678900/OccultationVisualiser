"""Display errors in the UI language without corrupting diagnostic values."""
import unittest
from occultation_media.gui_error_text import error_text
from occultation_media.gui_error_catalog import ERRORS


class ErrorLanguageTests(unittest.TestCase):
    def test_catalog_selects_each_language(self):
        for original, zh, en in ERRORS:
            if '{value}' in original:continue
            with self.subTest(error=original):
                self.assertEqual(error_text(original,'English'),en)
                self.assertEqual(error_text(original,'中文'),zh)

    def test_dynamic_field_and_count_survive(self):
        self.assertEqual(error_text('exposure_ms: requires a finite number / 需要有限数值','中文'),'exposure_ms: 需要有限数值')
        self.assertEqual(error_text('PyOTE: 3 matching fits; choose Fit record in Advanced / 多条结果，请在高级设置选拟合记录','English'),'PyOTE: 3 matching fits; choose Fit record in Advanced')

    def test_external_text_and_paths_are_not_split(self):
        original='Cannot read /Users/中文数据/AVI / result.csv; value 3 / 4'
        self.assertEqual(error_text(original,'English'),original)
        self.assertEqual(error_text(original,'中文'),original)
