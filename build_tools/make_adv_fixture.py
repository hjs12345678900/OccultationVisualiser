"""Regenerate a synthetic ADV2 fixture, containing no observation data.

Use the pinned ADVCore library's public C writer API. Pixel values are a known
8x4 ramp plus frame index; UTC starts at 2010-01-01 + 1 second + 123 ns, and
each exposure lasts 200 ms with 300 ms cadence. This is a decoder regression
fixture, not a photometric measurement or a camera timing calibration.
"""
import ctypes as c
from pathlib import Path
import sys


def generate(library, output):
    """Write three uncompressed, unsigned 16-bit main-stream detector frames."""
    lib = c.CDLL(str(library))
    signatures = {
        'NewFile': [c.c_char_p, c.c_bool],
        'DefineImageSection': [c.c_ushort, c.c_ushort, c.c_ubyte],
        'DefineImageLayout': [c.c_ubyte, c.c_char_p, c.c_char_p, c.c_ubyte],
        'DefineStatusSection': [c.c_int64],
        'BeginFrame': [c.c_uint, c.c_int64, c.c_uint],
        'FrameAddImage': [c.c_ubyte, c.POINTER(c.c_ushort), c.c_ubyte],
        'EndFrame': [], 'EndFile': [],
    }
    def call(name, *args):
        function = getattr(lib, 'AdvVer2_' + name)
        function.argtypes = signatures[name]
        function.restype = c.c_uint
        result = function(*args)
        if result != 0:
            raise RuntimeError(f'{name} failed: {result:#x}')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    call('NewFile', str(output).encode(), True)
    call('DefineImageSection', 8, 4, 16)
    call('DefineImageLayout', 1, b'FULL-IMAGE-RAW', b'UNCOMPRESSED', 16)
    call('DefineStatusSection', 1)
    for index in range(3):
        call('BeginFrame', 0, 1_000_000_123 + index * 300_000_000, 200_000_000)
        pixels = (c.c_ushort * 32)(*(1000 + index + n for n in range(32)))
        call('FrameAddImage', 1, pixels, 16)
        call('EndFrame')
    call('EndFile')


if __name__ == '__main__':
    generate(*sys.argv[1:3])
