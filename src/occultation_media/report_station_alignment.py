"""Expose original UTC coverage even when no real image matches a saved curve."""


NO_MATCH = ('No source images match the curve UTC; check Observation date UTC '
            'and that the curve and recording belong together / '
            '原始影像与曲线 UTC 无匹配；请检查观测 UTC 日期以及曲线和录像是否对应')


def alignment_evidence(station):
    """Return JSON-ready frame counts, midpoint UTC bounds and timing evidence.

    ``station`` contains saved MediaSample rows and their prepared frame source.
    UTC bounds are ISO nanosecond strings; offsets and signed nearest residuals
    are seconds. Expected source UTC is curve UTC plus the declared saved clock
    correction. Source bounds cover inspected frames, including unmatched ones.
    AVI has no independent source UTC. LC bounds cover its matched stamps only.
    No date, frame identity or photometry is inferred or changed.
    """
    rows, frames = station['rows'], station['frames']
    evidence = dict(name=station['config']['name'], samples=len(rows),
        matched_images=len(frames.mapping), curve_start_utc=str(rows[0].utc),
        curve_end_utc=str(rows[-1].utc))
    summary = getattr(frames, 'alignment_summary', None)
    if summary is not None:
        evidence.update(summary)
    else:
        records = list(frames.records.values())
        stamps = [r['source_midpoint_utc'] for r in records if r['source_midpoint_utc'] is not None]
        evidence.update(source_start_utc=min(stamps) if stamps else None,
                        source_end_utc=max(stamps) if stamps else None)
    return evidence


def alignment_text(evidence):
    """Format station UTC evidence for logs/errors, retaining exact timestamps.

    Labels are bilingual and localized at the existing GUI display boundary.
    The source range remains explicit when image matching produces zero records.
    """
    text = (f'{evidence["name"]}: Curve UTC / 曲线 UTC: '
            f'{evidence["curve_start_utc"]} .. {evidence["curve_end_utc"]}')
    if evidence['source_start_utc'] is not None:
        text += (f'\nSource UTC / 原始影像 UTC: {evidence["source_start_utc"]} .. '
                 f'{evidence["source_end_utc"]}')
    residual = evidence.get('closest_residual_s')
    if residual is not None:
        text += f'\nClosest UTC residual (s) / 最近 UTC 偏差（秒）: {residual:g}'
    return text
