"""Describe saved curve noise outside an event; do not fit or change photometry."""
import numpy as np


def baseline_snr(rows, disappearance, reappearance):
    """Estimate dimensionless per-exposure baseline SNR from original samples.

    ``rows`` contains net-count MediaSamples with midpoint UTC[ns], exposure
    seconds and validity flags. D/R are absolute UTC[ns]. Use valid exposures
    wholly outside [D,R], so partially occulted transition frames cannot
    contaminate the baseline. No smoothing, detrending, clipping or integration
    is performed; statistics use the full recording, independent of media cuts.

    B = mean(y), sigmaB = sqrt(mean((y-B)**2)), SNR = B/sigmaB.
    y, B and sigmaB retain the input count units. sigmaB is single-exposure
    scatter (population ddof=0), never the mean's uncertainty sigmaB/sqrt(N).
    Return a provenance dict with selected frame IDs and numerical parameters.
    Fewer than three valid baseline exposures, nonpositive B/variance or absent
    D/R return an unavailable metric rather than an invented ratio.
    """
    missing = dict(snr=None, method='unavailable', estimated=False)
    if disappearance is None or reappearance is None:
        return dict(missing, reason='No saved D/R to identify baseline exposures')
    baseline = []
    for row in rows:
        half = np.timedelta64(round(row.exposure_s*.5e9), 'ns')
        if row.valid and (row.utc+half <= disappearance or row.utc-half >= reappearance):
            baseline.append(row)
    if len(baseline) < 3:
        return dict(missing, reason='Fewer than three valid baseline exposures')
    counts = np.array([r.counts for r in baseline], dtype=np.float64)
    mean, scatter = float(counts.mean()), float(counts.std(ddof=0))
    if not np.isfinite([mean, scatter]).all() or mean <= 0 or scatter <= 0:
        return dict(missing, reason='Nonpositive or nonfinite baseline mean/scatter')
    return dict(snr=mean/scatter, B=mean, sigmaB=scatter, method='saved curve baseline mean/population std',
                estimated=True, baseline_samples=len(baseline), baseline_frame_ids=[r.frame for r in baseline],
                ddof=0, formula='B/sigmaB', selection='Valid exposures wholly outside saved D/R',
                data_scope='Full saved curve, independent of display window', detrended=False)
