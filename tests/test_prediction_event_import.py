"""Verify prediction imports fill event fields atomically without requiring a map."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch
from occultation_media.import_prediction_event import prediction_event_fields
from occultation_media.gui_shadow_simulation import PredictionDialog
from occultation_media.gui_config import build_config
from occultation_media.gui_observer import DEFAULTS

PREDICTION = Path(__file__).resolve().parents[1]/'examples/altona_20260912.occelmnt'


class Variable:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class PredictionEventImportTests(unittest.TestCase):
    def test_file_and_paste_fill_names_and_date_despite_stale_or_blank_form(self):
        expected = dict(event='Altona', target='UCAC4 336-171713', date_utc='2026-09-12')
        for date in ('', '2026-10-13'):
            for selected in (dict(shadow_xml=PREDICTION.read_text()),
                             dict(shadow_prediction_file=str(PREDICTION))):
                values = dict(event='',target='',date_utc=date,shadow_enabled='0',**selected)
                before = dict(values)
                self.assertEqual(prediction_event_fields(values), expected)
                self.assertEqual(values, before)

    def dialog(self, xml, enabled='0'):
        dialog = PredictionDialog.__new__(PredictionDialog)
        values = dict(event='Old',target='Old star',date_utc='2026-10-13',
            shadow_enabled=enabled,shadow_prediction_file='',shadow_xml='',
            step_s='.2',language='en',source='original recording')
        dialog.fields = {key:Variable(value) for key,value in values.items()}
        dialog.file = Variable('')
        dialog.xml = Mock(); dialog.xml.get.return_value = xml
        dialog.window = Mock()
        dialog.ui = SimpleNamespace(text=lambda key:key,language=Variable('English'))
        return dialog

    def test_dialog_import_preserves_map_choice_and_unrelated_inputs(self):
        for enabled in ('0','1'):
            dialog = self.dialog(PREDICTION.read_text(), enabled)
            PredictionDialog.save(dialog)
            values = {k:v.get() for k,v in dialog.fields.items()}
            self.assertEqual(values['event'], 'Altona')
            self.assertEqual(values['target'], 'UCAC4 336-171713')
            self.assertEqual(values['date_utc'], '2026-09-12')
            self.assertEqual(values['shadow_enabled'], enabled)
            self.assertEqual(values['source'], 'original recording')
            self.assertEqual(values['step_s'], '.2')
            dialog.window.destroy.assert_called_once()

    def test_invalid_or_ambiguous_import_leaves_all_fields_unchanged(self):
        xml = PREDICTION.read_text()
        for value in ('not XML', '<Occultations/>',
                      xml.replace('Altona,', ','),
                      xml.replace('UCAC4 336-171713,', ',')):
            dialog = self.dialog(value)
            before = {k:v.get() for k,v in dialog.fields.items()}
            with patch('occultation_media.gui_shadow_simulation.messagebox.showerror') as error:
                PredictionDialog.save(dialog)
            error.assert_called_once()
            dialog.window.destroy.assert_not_called()
            self.assertEqual({k:v.get() for k,v in dialog.fields.items()}, before)
        with self.assertRaisesRegex(ValueError, 'Choose a prediction file or paste XML'):
            prediction_event_fields(dict(shadow_xml=xml, shadow_prediction_file=str(PREDICTION)))

    def test_imported_fields_build_media_config_without_enabling_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            curve, source = root/'curve.csv', root/'source.ser'
            curve.touch(); source.touch()
            source.with_suffix('.CameraSettings.txt').write_text('Exposure=200ms\n')
            event = dict(event='',target='',date_utc='2026-10-13',shadow_enabled='0',
                shadow_xml=PREDICTION.read_text(),step_s='.2',language='en',
                output_root=tmp,window_mode='full')
            event.update(prediction_event_fields(event))
            cfg = build_config(event,[{**DEFAULTS,'curve':str(curve),'source':str(source)}])
            self.assertEqual(cfg['date_utc'], '2026-09-12')
            self.assertEqual(cfg['target'], 'UCAC4 336-171713')
            self.assertNotIn('shadow_simulation', cfg)
