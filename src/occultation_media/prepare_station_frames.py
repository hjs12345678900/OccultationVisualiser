"""Verify timed sources or map AVI by explicit curve-frame identity before display."""
from pathlib import Path
import numpy as np
from .read_frame_sources import open_source
from .read_source_timing import source_timing
from .resolve_image_stretch import image_limits, stretch_pixels


def nearest_sample(rows, utc):
    """Return nearest actual saved frame within sampling support, preserving gaps.

    Each image label retains its actual UTC. Support is 0.55 times the larger
    of recorded exposure and the median regular saved-sample cadence. Regular
    intervals are no longer than three times the shortest observed interval,
    a display-only guard against long gaps; the median tolerates short jitter.
    This cadence controls
    display selection only and is never substituted for shutter exposure.
    Outside recording coverage and beyond typical support, images stay blank.
    """
    if utc < rows[0].utc or utc > rows[-1].utc: return None
    times = np.array([r.utc for r in rows])
    index = int(np.searchsorted(times, utc))
    candidates = [i for i in (index-1, index) if 0 <= i < len(rows)]
    best = min(candidates, key=lambda i: abs(int((times[i]-utc)/np.timedelta64(1,'ns'))))
    intervals = np.diff(times)/np.timedelta64(1,'s')
    regular = intervals[intervals<=3*np.min(intervals)] if intervals.size else intervals
    cadence = float(np.median(regular)) if regular.size else 0
    support = max(rows[best].exposure_s,cadence)*.55
    return best if abs(float((times[best]-utc)/np.timedelta64(1,'s'))) <= support else None


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
        self.limits = None; self.stretch_info = None
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

        Levels/strength are fixed from the first visible frame or explicit settings.
        Auto AVI excludes the bottom caption area from level estimation only.
        Preserve full-field pixels, aspect and orientation; no interpolation.
        """
        wanted = sorted(set(i for i in indices if i is not None and i in self.mapping))
        if not wanted: return
        source_indices = [self.mapping[i] for i in wanted]
        pixels = self.reader.read_many(source_indices) if hasattr(self.reader,'read_many') else None
        for i in wanted:
            index = self.mapping[i]
            image = pixels.pop(index)[0] if pixels is not None else self.reader.read(index)[0]
            if self.limits is None:
                self.limits,self.stretch_info = image_limits(image,self.cfg,self.reader.metadata['format'])
            self.prepared[i] = stretch_pixels(image,self.limits,self.stretch_info)

    def close(self):
        """Release a source handle where provided; cached display pixels expire."""
        if hasattr(self.reader, 'close'): self.reader.close()
