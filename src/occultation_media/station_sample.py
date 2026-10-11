"""Original target measurements used solely for timestamp-verified display."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class MediaSample:
    """Net ADU, midpoint UTC[ns], exposure seconds and zero-based target (x,y).

    Original integral frame IDs and invalid/negative counts are retained.
    tracking_flag >= 2 or nonfinite counts creates a plotted gap.
    """
    frame: int
    utc: np.datetime64
    exposure_s: float
    counts: float
    comparison_counts: tuple = ()
    shift_xy: tuple = (0., 0.)
    tracking_flag: int = 0
    saturated_pixels: int = 0
    target_xy: tuple | None = None

    @property
    def valid(self):
        return self.tracking_flag < 2 and np.isfinite(self.counts)
