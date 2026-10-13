"""Use recorded Tangra target stamps in a multi-observer display."""
from pathlib import Path
import numpy as np
from .read_station_curves import read_lc_curve
from .read_tangra_stamps import extract_target_stamps
from .resolve_image_stretch import image_limits, stretch_pixels


class LCFrames:
    """Map LC target-0 stamps by original frame and corrected midpoint UTC.

    LC times include its saved digital correction, applied once by the reader.
    CSV/stamp disagreement is rejected with the same explicit tolerance as full
    fields. These are 35x35 cutouts, never reconstructed full detector images.
    """
    def __init__(self,cfg,rows,native_times=None):
        self.cfg,self.rows=cfg,rows
        self.paths=[Path(cfg['source'])]
        self.mapping={};self.records={};self.prepared={};self.limits=None;self.stretch_info=None
        samples,_,_=read_lc_curve(self.paths[0]);by_frame={r.frame:r for r in samples}
        tolerance=float(cfg['mapping_tolerance_s'])
        offset=float(cfg.get('source_minus_curve_s',0))
        if not np.isfinite([tolerance,offset]).all() or tolerance<0: raise ValueError('Invalid LC tolerance/offset')
        for i,row in enumerate(rows):
            source=by_frame.get(row.frame)
            if source is None: raise ValueError(f'LC missing frame {row.frame}')
            residual=float((source.utc-row.utc)/np.timedelta64(1,'s'))-offset
            if abs(residual)>tolerance: raise ValueError(f'LC UTC mismatch at frame {row.frame}: {residual} s')
            self.mapping[i]=row.frame
            self.records[i]=dict(frame=row.frame,source_index=row.frame,source_midpoint_utc=str(source.utc),
                curve_midpoint_utc=str(row.utc),applied_source_minus_curve_s=offset,residual_s=residual,
                native=dict(format='Tangra LC target cutout',timestamp_reference='midpoint'))

    def prepare(self,indices):
        """Decode selected stamps with a fixed first-visible-frame stretch."""
        wanted=sorted(set(i for i in indices if i is not None and i in self.mapping))
        if not wanted:return
        stamps=extract_target_stamps(self.paths[0],{self.rows[i].frame for i in wanted},1)
        for i in wanted:
            pixels=stamps[self.rows[i].frame]
            if self.limits is None:self.limits,self.stretch_info=image_limits(pixels,self.cfg,'LC')
            self.prepared[i]=stretch_pixels(pixels,self.limits,self.stretch_info)

    def close(self):
        """LC decoding uses bounded file reads and retains no open handles."""
