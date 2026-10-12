"""Compare actual observation noise, retaining UTC and explicit assumptions."""
import numpy as np
from .measure_noise_profile import baseline_indices,noise_profile,excluded_events
from .read_quality_context import read_quality_context
from .read_saved_snr import station_snr


def pixel_noise_budget(rows,indices,aux,raw=True):
    """Estimate sigma_ap=median(sigma_pixel*sqrt(N)) in saved raw-count units.

    CSV sigma_pixel is spatial background scatter, not separately measured
    detector read noise. Independence, background representativeness and no
    rescaling are assumptions. Do not present this as a variance decomposition.
    Negative PyMovie N indicates default-mask use; mask changes are described
    separately. Missing columns/normalized counts leave the budget unavailable.
    """
    values=[];default=[];other=[]
    for i in indices:
        record=aux.get(rows[i].frame,{})
        n=record.get('mask_pixels');sigma=record.get('background_std')
        if n is not None and np.isfinite(n) and n!=0:
            (default if n<0 else other).append(i)
        if n is not None and sigma is not None and np.isfinite([n,sigma]).all() and n!=0 and sigma>0:
            values.append((sigma,abs(n),sigma*np.sqrt(abs(n))))
    info=dict(available=False,default_mask_samples=len(default),other_mask_samples=len(other),
              default_mask_profile=noise_profile(rows,default) if default else None)
    if not raw: return dict(info,reason='Normalized count units cannot be compared with raw pixel background')
    if not values: return dict(info,reason='No recorded per-pixel background noise/mask columns')
    array=np.array(values)
    return dict(info,available=True,pixel_sigma_median=float(np.median(array[:,0])),
                mask_pixels_median=float(np.median(array[:,1])),aperture_sigma_estimate=float(np.median(array[:,2])),
                samples=len(values),formula='sigma_pixel*sqrt(N_mask)',
                assumptions='Independent representative background pixels; omits source shot noise and background-estimator uncertainty',
                attribution='Combined spatial pixel noise; sky and detector read noise are not separated')


def diagnose_stations(stations,margin_s=1):
    """Return a JSON-safe station report, pairwise UTC comparisons and inputs.

    Each station carries config, rows, saved D/R and optionally native SNR.
    Use one-second diagnostic guards by default, independently of media trims.
    Pairwise comparisons use shared absolute UTC coverage and exclude the union
    of both guarded events. No overlap is explicitly unavailable, never shifted.
    Exposure-only ratios assume photon-noise dominance and equal photon rates;
    the output never assigns a measured SNR difference to camera hardware alone.
    """
    if not np.isfinite(margin_s) or margin_s<0: raise ValueError('Diagnostic margin must be finite and nonnegative')
    output=[];inputs=[]
    for i,s in enumerate(stations):
        cfg,rows=s['config'],s['rows']
        context,aux,paths=read_quality_context(cfg);inputs+=paths
        exposure=float(np.median([r.exposure_s for r in rows]))
        idx=baseline_indices(rows,excluded_events([s],margin_s)) if s['D'] is not None else []
        profile=noise_profile(rows,idx)
        budget=pixel_noise_budget(rows,idx,aux,cfg.get('native_mode','raw')=='raw')
        if budget['available'] and profile['available']:
            budget['sigma_ratio_to_measured']=budget['aperture_sigma_estimate']/profile['sigmaB']
        output.append(dict(index=i,name=cfg['name'],context=context,exposure_s=exposure,
                           saved_snr=s.get('snr') or station_snr(cfg,rows,s['D'],s['R']),
                           separately_reported_snr=cfg.get('reported_snr'),
                           baseline=profile,pixel_budget=budget))
    pairs=[]
    for i,a in enumerate(stations):
        for j in range(i+1,len(stations)):
            b=stations[j];start=max(a['rows'][0].utc,b['rows'][0].utc);stop=min(a['rows'][-1].utc,b['rows'][-1].utc)
            pair=dict(station_indices=[i,j],names=[a['config']['name'],b['config']['name']],available=False)
            if start>=stop: pairs.append(dict(pair,reason='No shared absolute UTC coverage'));continue
            if a['D'] is None or b['D'] is None: pairs.append(dict(pair,reason='D/R needed to identify both baselines'));continue
            cuts=excluded_events([a,b],margin_s)
            profiles=[noise_profile(s['rows'],baseline_indices(s['rows'],cuts,(start,stop))) for s in (a,b)]
            pair.update(start_utc=str(start),end_utc=str(stop),excluded_intervals=[dict(start_utc=str(x),end_utc=str(y)) for x,y in cuts],profiles=profiles)
            if all(p['available'] for p in profiles):
                t1,t2=output[i]['exposure_s'],output[j]['exposure_s']
                pair.update(available=True,snr_ratio=profiles[0]['snr']/profiles[1]['snr'],
                            exposure_only_photon_noise_ratio=float(np.sqrt(t1/t2)))
            else: pair['reason']='Insufficient or zero-scatter shared baseline'
            pairs.append(pair)
    report=dict(definition='Baseline SNR=B/population std; per-exposure scatter, not error of mean',
                diagnostic_margin_s=margin_s,stations=output,pairs=pairs,
                comparison_note='Observation and photometry comparison; detector performance needs matched conditions and electron calibration',
                original_counts_and_utc_unchanged=True)
    return report,inputs
