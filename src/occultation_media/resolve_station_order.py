"""Pipeline/I/O: resolve prediction-based station order and record its evidence."""
from .plan_station_timeline import order_stations
from .read_occult_prediction import load_prediction
from .record_media_run import write_json


def resolve_station_order(cfg, stations, out):
    """Return ordered stations and prediction inputs; save cross-track evidence.

    Path sorting needs prediction elements even if the optional map is disabled.
    Latitude/input order retains its legacy meaning. Unknown path offsets remain
    last in input order, with an explicit reason; no geographic-order fallback.
    """
    mode=cfg.get('station_order','input')
    geometry=None;paths=[];evidence=None
    if mode=='path_north_to_south':
        settings={**cfg.get('shadow_simulation',{}),'enabled':True}
        if not settings.get('prediction_file') and not settings.get('xml'):
            raise ValueError('Path station order requires prediction elements / 路径北南排序需要导入预测元素')
        geometry,evidence,paths=load_prediction(settings,cfg['date_utc'])
    ordered=order_stations(stations,mode,geometry)
    if geometry is not None:
        write_json(out/'station_path_order.json',dict(mode=mode,
            coordinate='signed fundamental-plane impact parameter; north positive; km',
            timing='individual predicted closest approach; no measured D/R used',
            prediction=evidence,
            stations=[dict(name=s['config']['name'],**s['path_offset']) for s in ordered]))
    return ordered,paths
