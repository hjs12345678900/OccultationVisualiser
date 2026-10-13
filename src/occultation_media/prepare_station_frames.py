"""Verify timed sources or map AVI by explicit curve-frame identity before display."""
from pathlib import Path
import numpy as np
from .read_frame_sources import open_source
from .read_source_timing import source_timing
from .render_detector_field import first_frame_limits, display_pixels


def nearest_sample(rows, utc):
    """Return nearest actual exposure within coverage, without filling long gaps.

    Each image label retains that sample's own UTC. A <=0.55-exposure distance
    tolerates midpoint sampling/rounding only; images beyond coverage are blank.
    """
    if utc < rows[0].utc or utc > rows[-1].utc: return None
    times = np.array([r.utc for r in rows])
    index = int(np.searchsorted(times, utc))
    candidates = [i for i in (index-1, index) if 0 <= i < len(rows)]
    best = min(candidates, key=lambda i: abs(int((times[i]-utc)/np.timedelta64(1,'ns'))))
    return best if abs(float((times[best]-utc)/np.timedelta64(1,'s'))) <= rows[best].exposure_s*.55 else None


class StationFrames:
    """Map real images to curve midpoint UTC, preserving explicit clock offsets.

    source_minus_curve_s verifies an already-applied CSV clock correction;
    it is never added to the curve a second time. Non-FITS sources require
    one-to-one UTC agreement in automatic mode, or explicit frame identity and
    UTC agreement when an offset is supplied. Partial FITS maps by header UTC.
    A finite nonnegative tolerance is mandatory and every residual is recorded.
    """
    def __init__(self, cfg, rows, native_times=None):
        self.cfg, self.rows = cfg, rows
        self.mapping, self.records, self.prepared = {}, {}, {}
        self.limits = None
        path = Path(cfg['source']).expanduser().resolve()
        self.reader = open_source(path, ser_byte_order=cfg.get('ser_byte_order','header'),
                                  fits_hdu=cfg.get('fits_hdu'), adv_python=cfg.get('adv_python'))
        kind = self.reader.metadata['format']
        self.paths = self.reader.files if kind == 'FITS' else [path]
        if kind == 'AVI':
            from .prepare_avi_frames import map_avi_frames
            map_avi_frames(self, cfg, rows)
            return
        tolerance = float(cfg['mapping_tolerance_s'])
        offset_s = float(cfg.get('source_minus_curve_s', 0.))
        if not np.isfinite([tolerance, offset_s]).all() or tolerance < 0:
            raise ValueError('Timing tolerance and saved clock correction must be finite')
        offset = np.timedelta64(round(offset_s*1e9), 'ns')
        automatic=kind=='FITS' or cfg.get('source_first_frame','auto')=='auto'
        indices = list(range(self.reader.count)) if automatic else [r.frame-cfg['source_first_frame'] for r in rows]
        if any(i<0 or i>=self.reader.count for i in indices): raise ValueError('Source frame mapping out of range')
        timing = source_timing(self.reader, cfg, indices)
        times = np.array([timing[i][0] for i in indices])
        if any(b<=a for a,b in zip(times,times[1:])): raise ValueError('Source UTC must strictly increase')
        used = set()
        for i, row in enumerate(rows):
            expected = row.utc+offset
            if automatic:
                source_index = int(np.argmin(abs(times-expected)))
            else: source_index = indices[i]
            time, record = timing[source_index]
            residual = float((time-expected)/np.timedelta64(1,'s'))
            if abs(residual) > tolerance:
                if automatic and (kind=='FITS' or expected<times[0] or expected>times[-1]): continue
                raise ValueError(f'{cfg["name"]}: UTC mismatch at frame {row.frame}: {residual:g} s')
            if source_index in used: raise ValueError('Two curve samples map to the same source image')
            used.add(source_index)
            self.mapping[i] = source_index
            self.records[i] = dict(frame=row.frame, source_index=source_index,
                mapping_method='absolute_utc_auto' if automatic else 'explicit_frame_offset',
                source_midpoint_utc=str(time), curve_midpoint_utc=str(row.utc),
                applied_source_minus_curve_s=offset_s, residual_s=residual, native=record)

    def prepare(self, indices):
        """Cache requested real uint8 frames with one fixed whole-field stretch.

        Limits are first displayed frame's 0.5/99.95 percentiles, asinh factor8.
        Preserve full-field pixels, aspect and orientation; no interpolation.
        """
        wanted = sorted(set(i for i in indices if i is not None and i in self.mapping))
        if not wanted: return
        source_indices = [self.mapping[i] for i in wanted]
        pixels = self.reader.read_many(source_indices) if hasattr(self.reader,'read_many') else None
        for i in wanted:
            index = self.mapping[i]
            image = pixels.pop(index)[0] if pixels is not None else self.reader.read(index)[0]
            if self.limits is None: self.limits = first_frame_limits(image)
            self.prepared[i] = display_pixels(image, *self.limits)

    def close(self):
        """Release a source handle where provided; cached display pixels expire."""
        if hasattr(self.reader, 'close'): self.reader.close()
