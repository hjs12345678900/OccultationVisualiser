"""Protect exact detector values and sub-microsecond timing across architectures."""
import unittest
from pathlib import Path
from unittest.mock import patch
from build_tools.prepare_adv_bundle import validate_architecture
from occultation_media.verify_adv_fixture import verify


class NativeAdvTests(unittest.TestCase):
    def test_detector_and_native_nanosecond_metadata(self):
        self.assertTrue(verify()['utc_and_exposure_ns_exact'])

    def test_reject_incompatible_native_library(self):
        with patch('build_tools.prepare_adv_bundle.subprocess.check_output', return_value='x86_64\n'):
            with self.assertRaises(RuntimeError):
                validate_architecture(Path('wrong.dylib'), 'arm64')


if __name__ == '__main__':
    unittest.main()
