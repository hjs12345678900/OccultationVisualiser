"""Validate bundled ADV decoding against known detector values and UTC ns."""
from pathlib import Path
import numpy as np
from .read_adv_frames import AdvSource


def verify():
    """Exercise the isolated worker, native decoder and frame metadata contract."""
    fixture = Path(__file__).parent / 'assets/verification/adv2_fixture.adv'
    source = AdvSource(fixture)
    if (source.count, source.metadata['width'], source.metadata['height']) != (3, 8, 4):
        raise AssertionError('ADV fixture dimensions/count differ')
    frames = source.read_many([0, 1, 2])
    for index, (pixels, timing) in frames.items():
        np.testing.assert_array_equal(pixels, np.arange(32).reshape(4, 8) + 1000 + index)
        expected = 1_100_000_123 + index * 300_000_000
        if timing['midpoint_timestamp_ns'] != expected or timing['exposure_ns'] != 200_000_000:
            raise AssertionError('ADV native midpoint/exposure ns differ')
    return {'native_decode': True, 'frames': 3, 'pixels_exact': True, 'utc_and_exposure_ns_exact': True}
