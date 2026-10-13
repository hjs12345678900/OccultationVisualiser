"""Resolve fixed display-only image levels independently of saved photometry."""
import numpy as np
from .render_detector_field import first_frame_limits, display_pixels


def stretch_settings(cfg):
    """Validate auto/full/manual levels, with dimensionless asinh strength.

    Manual black/white use decoded pixel units, not photometric ADU. Auto AVI
    estimates sky levels above the bottom 15% to exclude typical VTI captions;
    the complete original field remains displayed. Other auto sources retain
    the existing whole-field percentiles. Strength zero selects linear display.
    """
    settings = dict(cfg.get('image_stretch') or {})
    mode = settings.get('mode', 'auto')
    strength = float(settings.get('strength', 8))
    if mode not in ('auto', 'full', 'manual') or not np.isfinite(strength) or not 0 <= strength <= 100:
        raise ValueError('Image stretch: choose auto/full/manual and strength 0–100 / 检查影像拉伸设置')
    result = dict(mode=mode, strength=strength)
    if mode == 'manual':
        black, white = float(settings['black']), float(settings['white'])
        if not np.isfinite([black, white]).all() or white <= black:
            raise ValueError('Image stretch: white must exceed black / 白点须大于黑点')
        result.update(black=black, white=white)
    return result


def image_limits(pixels, cfg, source_format):
    """Return fixed (black,white) decoded levels and exact estimator evidence."""
    settings = stretch_settings(cfg)
    if settings['mode'] == 'manual':
        limits = settings['black'], settings['white']
        evidence = dict(settings, estimator='explicit decoded pixel levels')
    else:
        field = np.asarray(pixels)
        sky = settings['mode'] == 'auto' and source_format == 'AVI'
        bottom = max(1, int(field.shape[0]*.85)) if sky else field.shape[0]
        if sky:
            finite=np.asarray(field[:bottom],dtype=float)
            finite=finite[np.isfinite(finite)]
            if not finite.size:raise ValueError('Initial sky region contains no finite pixels')
            black,white=np.percentile(finite,[.5,99.99])
            limits=float(black),float(max(white,black+1))
        else:limits = first_frame_limits(field)
        evidence = dict(settings, estimator='first displayed frame percentiles',
                        percentiles=[.5,99.99] if sky else [.5,99.95],
                        level_region_xyxy=[0,0,field.shape[1],bottom], full_field_displayed=True)
    return limits, evidence


def stretch_pixels(pixels, limits, evidence):
    """Transform pixels using the same resolved levels/strength for the clip."""
    return display_pixels(pixels, *limits, strength=evidence['strength'])
