"""Map explicitly identified AVI frames to saved curve exposure midpoints."""
import numpy as np


def map_avi_frames(frames, cfg, rows):
    """Populate StationFrames mapping/records using declared frame identity.

    source_first_frame is the nonnegative integer curve frame ID at AVI index
    zero. This supports contiguous original/cropped recordings and sparse curve
    rows. It cannot verify an edited, integrated, duplicated or dropped-frame
    recording. UTC is inherited from the saved curve, never container FPS/OCR.
    Missing AVI coverage stays blank; source UTC and residual remain null.
    """
    first = cfg.get('source_first_frame')
    if isinstance(first, bool) or not isinstance(first, int) or first < 0:
        raise ValueError('AVI requires explicit source_first_frame >= 0 / AVI 须填写第 0 帧对应的曲线帧号')
    reference = 'midpoint' if cfg.get('curve_format')=='tangra_lc' else cfg.get('timestamp_reference')
    if reference not in ('start', 'midpoint', 'end'):
        raise ValueError('AVI requires an explicit curve timestamp_reference')
    offset = float(cfg.get('source_minus_curve_s', 0))
    if not np.isfinite(offset) or offset != 0:
        raise ValueError('AVI has no independent UTC to verify source_minus_curve_s; use corrected curve UTC and zero offset')
    for i, row in enumerate(rows):
        index = row.frame - first
        if not 0 <= index < frames.reader.count:
            continue
        frames.mapping[i] = index
        frames.records[i] = dict(frame=row.frame, source_index=index,
            mapping_method='explicit_avi_frame_identity', source_midpoint_utc=None,
            curve_midpoint_utc=str(row.utc), applied_source_minus_curve_s=0.,
            residual_s=None, independent_source_utc_verified=False,
            native=dict(format='AVI', source_utc_available=False,
                        timestamp_basis='saved curve midpoint UTC', source_first_frame=first))
    if not frames.mapping:
        raise ValueError('No curve frames overlap the declared AVI frame range')
