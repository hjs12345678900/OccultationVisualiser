"""Read native B/sigmaB for labels, with an explicit saved-curve fallback."""
from pathlib import Path
import json
import math
from .measure_baseline_snr import baseline_snr


def station_snr(cfg, rows, disappearance, reappearance):
    """Return baseline SNR and its provenance, preserving saved native noise.

    Native PyOTE B/sigmaB is preferred when both fields are available. Require
    finite positive mean and single-exposure scatter. Read A only to record
    DNR=(B-A)/sigmaB separately; DNR is never labelled baseline SNR. Otherwise
    use descriptive saved-curve baseline statistics with ``estimated=True``. Unknown
    baseline or zero noise remains unavailable. No model or D/R is refitted.
    """
    if cfg.get('pyote_result'):
        path = Path(cfg['pyote_result'])
        result = json.loads(path.read_text())
        if 'B' in result and 'sigmaB' in result:
            mean, scatter = float(result['B']), float(result['sigmaB'])
            if not all(math.isfinite(v) and v > 0 for v in (mean, scatter)):
                raise ValueError(f'{cfg["name"]}: invalid saved baseline mean/noise')
            info = dict(snr=mean/scatter, B=mean, sigmaB=scatter, formula='B/sigmaB',
                        method='saved native PyOTE baseline parameters', estimated=False,
                        source=str(path), native_mode=cfg.get('native_mode', 'raw'))
            if result.get('A') is not None:
                low = float(result['A'])
                if not math.isfinite(low): raise ValueError('Nonfinite saved event level')
                info.update(A=low, dnr=(mean-low)/scatter, dnr_formula='(B-A)/sigmaB')
            return info
    info=baseline_snr(rows, disappearance, reappearance)
    info.update(source=cfg.get('curve'),source_format=cfg.get('curve_format'))
    return info


def snr_label(metric, language='en'):
    """Format two-decimal baseline SNR, explicitly marking curve estimates."""
    if metric.get('snr') is None:
        return 'SNR —'
    value=f'{metric["snr"]:.2f}'
    if metric.get('estimated'):
        if metric.get('source_format')=='tangra_lc':
            return f'SNR {value} '+('（LC 基线）' if language=='zh' else '(LC baseline)')
        return f'SNR ≈ {value} '+('（估算）' if language=='zh' else '(estimated)')
    return f'SNR {value}'
