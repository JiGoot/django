import json
import os
# from turfpy.transformation import get_points
# from turfpy.measurement import boolean_point_in_polygon, points_within_polygon, center
# from geojson import Point, MultiPolygon, Feature, load, Polygon, FeatureCollection
''' load ML models. this file will be run automatically once
(regadless of number of place it imported ) if imported in files such as views, models'''

_modelML = None
try:
    _zpath = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'core/zones/kinshasa.json')
    with open(_zpath) as f:
        # gj = load(f)
        # for ft in gj['features']:
        #     geom_str = ft['geometry']
        #     geom = GEOSGeometry(geom_str)
        # polygon = Feature(geometry=MultiPolygon([
        #     ft['geometry'] for ft in gj['features']
        # ]))
        pass
except:
    # TODO log error
    pass
