"""Data I/O: decode AVI presentation frames, without deriving UTC from FPS.

The bundled FFmpeg decodes the first video stream sequentially, with frame
duplication/dropping and autorotation disabled. RGB8 is a display conversion,
not calibrated detector ADU. Photometry always comes from the saved curve.
"""
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from .platform_runtime import ffmpeg_executable, hidden_process_options


class AviSource:
    """Index decoded frames from zero; retain no open decoder between calls.

Construction scans the entire stream to establish an actual decoded count and
reject decoder errors. Neither duration nor container FPS defines frame count
or absolute time. Reads also start at frame zero to avoid keyframe-seek errors.
Only requested RGB uint8 (height,width,3) arrays are retained in memory.
"""
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open('rb') as stream:
            header = stream.read(12)
        if header[:4] != b'RIFF' or header[8:12] != b'AVI ':
            raise ValueError('Expected a RIFF AVI recording')
        if int.from_bytes(header[4:8], 'little')+8 > self.path.stat().st_size:
            raise ValueError('Truncated AVI RIFF container')
        self.count, self.shape = 0, None
        for pixels in self._frames():
            if self.shape is None:
                self.shape = pixels.shape
            if pixels.shape != self.shape:
                raise ValueError('AVI changes image dimensions within the recording')
            self.count += 1
        if not self.count:
            raise ValueError('AVI contains no decodable video frames')
        self.metadata = dict(format='AVI', count=self.count, width=self.shape[1],
            height=self.shape[0], pixel_representation='FFmpeg RGB8 display conversion',
            timestamp_convention='No independent UTC; explicit curve-frame identity',
            decoder='bundled FFmpeg', video_stream=0, sequential_decode=True)

    def _frames(self):
        """Yield RGB8 arrays; reject truncated frames and nonzero decoder exits.

        PPM headers carry exact dimensions without a separate probe executable.
        Stderr goes to disk so large decoder diagnostics cannot block stdout.
        """
        command = [ffmpeg_executable(), '-hide_banner', '-loglevel', 'error',
            '-nostdin', '-xerror', '-err_detect', 'explode', '-noautorotate',
            '-i', str(self.path), '-map', '0:v:0', '-an', '-sn', '-dn',
            '-fps_mode', 'passthrough', '-c:v', 'ppm', '-pix_fmt', 'rgb24',
            '-f', 'image2pipe', 'pipe:1']
        with tempfile.TemporaryFile() as log:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log,
                                       **hidden_process_options())
            try:
                stream = process.stdout
                while True:
                    magic = stream.readline()
                    if not magic:
                        break
                    if magic != b'P6\n':
                        raise ValueError('Invalid AVI decoded frame header')
                    width, height = map(int, stream.readline().split())
                    if width <= 0 or height <= 0 or stream.readline() != b'255\n':
                        raise ValueError('Unsupported AVI decoded image layout')
                    size = width * height * 3
                    data = stream.read(size)
                    if len(data) != size:
                        raise ValueError('Truncated AVI decoded frame')
                    yield np.frombuffer(data, np.uint8).reshape(height, width, 3).copy()
                if process.wait():
                    log.seek(0)
                    raise ValueError('AVI decoding failed: ' + log.read(4096).decode('utf-8', 'replace'))
            finally:
                if process.poll() is None:
                    process.terminate()
                process.stdout.close()
                process.wait()

    def read_many(self, indices):
        """Return index -> (RGB8 pixels, identity), without source UTC claims."""
        wanted = set(indices)
        if any(not isinstance(i, (int, np.integer)) or not 0 <= i < self.count for i in wanted):
            raise IndexError('AVI source index out of range')
        result = {}
        for index, pixels in enumerate(self._frames()):
            if index in wanted:
                result[index] = (pixels, dict(source_index=index, source_utc_available=False))
        if len(result) != len(wanted):
            raise ValueError('AVI decoded frame count changed since validation')
        return result

    def read(self, index):
        """Return a single decoded display frame and zero-based identity."""
        return self.read_many([index])[index]
