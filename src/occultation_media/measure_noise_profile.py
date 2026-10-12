"""Measure descriptive baseline noise without changing counts or event timing."""
import numpy as np


def baseline_indices(rows, exclusions, span=None):
    """Return indices of valid exposures wholly outside excluded UTC intervals.

    rows hold midpoint UTC[ns] and exposure seconds. exclusions is a list of
    increasing (start,stop) UTC[ns] pairs. Optional span restricts exposures to
    shared coverage. Exposure intervals crossing an excluded edge are rejected.
    """
    selected=[]
    for i,row in enumerate(rows):
        if not row.valid: continue
        half=np.timedelta64(round(row.exposure_s*.5e9),'ns')
        if span and not (span[0]<=row.utc-half and row.utc+half<=span[1]): continue
        if all(row.utc+half<=a or row.utc-half>=b for a,b in exclusions): selected.append(i)
    return selected


def noise_profile(rows, indices):
    """Return full-cadence sample statistics and distinct diagnostic residuals.

    Counts keep their saved units. B=mean(y), sigma=population std(y), and
    SNR=B/sigma. Linear-residual scatter is a separate diagnostic, never a
    replacement light curve/SNR. Adjacent-difference scatter is std(diff)/sqrt2
    over consecutive original frames only; correlated noise can bias it.
    Return unavailable for <3 points or nonpositive mean/variance. UTC, original
    frame IDs and normalized raw counts are retained for plotting/auditing.
    """
    empty=dict(available=False,samples=len(indices),frame_ids=[rows[i].frame for i in indices])
    if len(indices)<3: return dict(empty,reason='Fewer than three baseline exposures')
    y=np.array([rows[i].counts for i in indices],dtype=float)
    mean,sigma=float(y.mean()),float(y.std(ddof=0))
    if not np.isfinite([mean,sigma]).all() or mean<=0 or sigma<=0:
        return dict(empty,reason='Nonpositive baseline mean or scatter')
    t=np.array([float((rows[i].utc-rows[indices[0]].utc)/np.timedelta64(1,'s')) for i in indices])
    trend=np.polyval(np.polyfit(t,y,1),t)
    adjacent=np.array([b==a+1 and rows[b].frame==rows[a].frame+1 for a,b in zip(indices,indices[1:])])
    differences=np.diff(y)[adjacent]
    pair_sigma=float(differences.std(ddof=0)/np.sqrt(2)) if len(differences)>=2 else None
    return dict(available=True,samples=len(indices),frame_ids=[rows[i].frame for i in indices],
                B=mean,sigmaB=sigma,snr=mean/sigma,scatter_percent=100*sigma/mean,ddof=0,
                linear_residual_sigma=float(np.std(y-trend)),
                adjacent_difference_sigma=pair_sigma,adjacent_pairs=len(differences),
                utc=[str(rows[i].utc) for i in indices],normalized_counts=(y/mean).tolist())


def excluded_events(stations, margin_s=1):
    """Return supplied D/R windows expanded by the explicit diagnostic margin."""
    pad=np.timedelta64(round(margin_s*1e9),'ns')
    return [(s['D']-pad,s['R']+pad) for s in stations if s['D'] is not None and s['R'] is not None]
