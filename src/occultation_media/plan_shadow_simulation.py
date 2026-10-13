"""Pipeline/I/O: attach a prediction to actual image UTC and export audit tables."""
from pathlib import Path
import csv
import numpy as np
from .read_occult_prediction import load_prediction
from .record_media_run import write_json


class ShadowSimulation:
    """Resolved optional prediction, independent of presentation speed and cuts.

    geometry is a validated ShadowGeometry; stations are the original pipeline
    station dictionaries with verified frame records. UTC inputs use corrected
    curve midpoints as already established by the media alignment pipeline.
    Source midpoint labels and clock-offset evidence remain separate.
    """
    def __init__(self, geometry, evidence, stations, timeline):
        self.geometry, self.evidence, self.stations = geometry, evidence, stations
        self.timeline = timeline
        for utc in (timeline[0], timeline[-1]):
            geometry.hours(utc)
        known = [s['config']['name'] for s in stations if 'latitude_deg' in s['config']]
        evidence.update(mapped_stations=known,
                        omitted_stations=[s['config']['name'] for s in stations if s['config']['name'] not in known])

    def position(self, utc):
        """Return JSON-safe center degrees, or None when it misses the Earth."""
        point = self.geometry.project_surface(self.geometry.center_xy(utc), utc)
        return dict(latitude_deg=float(point[0]), longitude_deg=float(point[1])) if np.isfinite(point).all() else None

    def frame_state(self, station, index):
        """Return frame identity, corrected/source UTC and predicted station state.

        index is an original station-row index, not an output-video frame ID.
        Only verified image mappings contribute. No matching image returns None.
        The original source timestamp may differ by an already-applied offset;
        position uses curve UTC and never adds that offset a second time.
        """
        frames = station['frames']
        if index is None or index not in frames.mapping:
            return None
        record, row = frames.records[index], station['rows'][index]
        utc = row.utc
        return dict(station=station['config']['name'], frame=row.frame,
                    mapping_method=record.get('mapping_method','recorded_frame_identity'),
                    independent_source_utc_verified=record.get('independent_source_utc_verified',True),
                    curve_midpoint_utc=str(utc), source_midpoint_utc=record['source_midpoint_utc'],
                    applied_source_minus_curve_s=record['applied_source_minus_curve_s'],
                    center=self.position(utc), site=self.geometry.site_state(station['config'], utc))

    def export(self, out):
        """Write all verified source-frame positions and display-step positions.

        CSV coordinates are geodetic degrees, north/east positive. FP distances
        are km; coverage is a circular-model prediction, not observed D/R.
        Off-Earth positions and unavailable coordinates remain empty CSV cells.
        """
        columns = ['station','frame','curve_midpoint_utc','source_midpoint_utc',
                   'applied_source_minus_curve_s','shadow_latitude_deg','shadow_longitude_deg',
                   'station_latitude_deg','station_longitude_deg','station_altitude_m',
                   'distance_fp_km','star_above_horizon','nominally_covered',
                   'mapping_method','independent_source_utc_verified']
        count = 0
        verified_count = 0
        with (out/'shadow_frame_positions.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            for station in self.stations:
                c = station['config']
                for index in sorted(station['frames'].mapping):
                    state = self.frame_state(station, index)
                    row = {k: state[k] for k in columns[:5]}
                    row.update({k:state[k] for k in columns[-2:]})
                    verified_count += int(state['independent_source_utc_verified'])
                    if state['center']:
                        row.update(shadow_latitude_deg=state['center']['latitude_deg'],
                                   shadow_longitude_deg=state['center']['longitude_deg'])
                    row.update({f'station_{k}': c[k] for k in ('latitude_deg','longitude_deg','altitude_m') if k in c})
                    if state['site']:
                        row.update(state['site'])
                    writer.writerow(row)
                    count += 1
        with (out/'shadow_display_positions.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['utc','shadow_latitude_deg','shadow_longitude_deg'])
            writer.writeheader()
            for utc in self.timeline:
                center = self.position(utc)
                writer.writerow(dict(utc=str(utc),shadow_latitude_deg=center['latitude_deg'] if center else '',
                                     shadow_longitude_deg=center['longitude_deg'] if center else ''))
        self.evidence.update(verified_frame_positions=verified_count,mapped_frame_positions=count,
                             frame_positions='shadow_frame_positions.csv',
                             display_positions='shadow_display_positions.csv')
        write_json(out/'shadow_simulation.json', self.evidence)


def prepare_simulation(cfg, stations, timeline, out):
    """Return (optional simulation,input paths), saving its prediction snapshot."""
    settings = cfg.get('shadow_simulation', {'enabled': False})
    geometry, evidence, paths = load_prediction(settings, cfg['date_utc'])
    if geometry is None:
        return None, []
    simulation = ShadowSimulation(geometry, evidence, stations, timeline)
    raw = Path(paths[0]).read_bytes().decode('utf-8-sig') if paths else settings['xml']
    (out/'shadow_prediction.occelmnt').write_text(raw, encoding='utf-8')
    simulation.export(out)
    map_asset=Path(__file__).parent/'assets/maps/countries.geojson'
    return simulation, [*paths,map_asset,map_asset.with_name('cities.json')]
