import datetime
from geoalchemy2.shape import to_shape
import numpy as np

import requests
import geojson
from geopandas import GeoSeries, GeoDataFrame

import config
import models
from layers import aggregate_depth, aggregate_wind


def generate_decision_layer(session, grid):
    """Generate a new decision layer and a set of decision layer cells.

    Parameters
    ----------
    grid(Grid): an sqlalchemy ORM entity for the target grid

    Returns
    -------
    decision_layer(DecisionLayer): an sqlalchemy ORM entity for the created decision layer
    """
    decision_layer = models.DecisionLayer(
        grid_id=grid.id,
        creation_time=datetime.datetime.now()
    )
    session.add(decision_layer)
    session.commit()
    return decision_layer


def generate_decision_layer_cells(session, decision_layer):
    """Generate the cells that make up a decision layer.

    Parameters
    ----------
    session: sqlalchemy session
    decision_layer: the sqlalchemy ORM entity for the target decision layer
    """
    grid_cells = session.query(models.GridCell).filter(models.GridCell.grid_id == decision_layer.grid_id).all()

    decision_cells = []
    for c in grid_cells:
        decision_cells.append(dict(
            decision_layer_id=decision_layer.id,
            grid_cell_id=c.id
        ))
    session.bulk_insert_mappings(models.DecisionLayerCell, decision_cells)
    session.commit()


def generate_decision_layer_cell_depth(session,path,grid):
    grid_cells = session.query(models.DecisionLayerCell, models.GridCell).join(models.GridCell).filter(models.GridCell.grid_id == grid.id).all()
    depth_list = []
    for cell in grid_cells:
        grid_box = to_shape(cell.GridCell.bounding_box)
        cell.DecisionLayerCell.depth = aggregate_depth(grid_box, path)
    session.commit()


def generate_decision_layer_cell_seabed(session, grid):
    grid_cells = session.query(models.DecisionLayerCell, models.GridCell).join(models.GridCell).filter(models.GridCell.grid_id == grid.id).order_by(models.GridCell.id).all()

    for cell in grid_cells:
        grid_box = to_shape(cell.GridCell.bounding_box)
       
        lonmin,lonmax,latmin,latmax = grid_box.bounds
        bbox_string = ",".join(map(str, [latmin,lonmin,latmax,lonmax]))
        wfs_url = "http://drive.emodnet-geology.eu/geoserver/EMODnetGeology/ows?service=WFS&version=1.1.0&request=GetFeature&typeName=EMODnetGeology:seabed_substrate250k_eu_sbss250k_seabed_substrate_eu&bbox="+bbox_string+"&outputFormat=application%2Fjson"
     
        try:
            r = requests.get(wfs_url)
            wfs_geo = geojson.loads(r.content)
     
            wfs_gdf = GeoDataFrame.from_features(wfs_geo)
            if len(wfs_gdf) > 0:
                if len(wfs_gdf[wfs_gdf.folk_5_substrate_class.str.contains('2. Sand')]) > 0:
                    cell.DecisionLayerCell.seabed = wfs_gdf[wfs_gdf.folk_5_substrate_class.str.contains('2. Sand')].shape_area.sum()/grid_box.area * 100
                else:
                    cell.DecisionLayerCell.seabed = 0
        except ValueError:
            pass
    session.commit()


def generate_decision_layer_cell_wind(session, grid, target_dir=None):
    if target_dir is None:
        target_dir = config.WIND_FILE_DIR
    speed, direction, stdev = aggregate_wind(session, grid, absolute=True)
    grid_cells = session.query(models.DecisionLayerCell, models.GridCell).join(models.GridCell).filter(models.GridCell.grid_id == grid.id).all()
    for cell in grid_cells:
        grid_box = to_shape(cell.GridCell.bounding_box)
        min_lon,min_lat,max_lon,max_lat = grid_box.bounds
        lon_filter = (speed.columns.values >= min_lon) & (speed.columns.values <= max_lon)
        lat_filter = (speed.index.values >= min_lat) & (speed.index.values <= max_lat)

        try:
            cell_speed = speed.loc[lat_filter, lon_filter].mean().values[0]
            if np.isnan(cell_speed):
                cell_speed = None
            cell_direction = direction.loc[lat_filter, lon_filter].mean().values[0]
            if np.isnan(cell_direction):
                cell_direction = None
            cell_stdev = stdev.loc[lat_filter, lon_filter].mean().values[0]
            if np.isnan(cell_stdev):
                cell_stdev = None
            cell.DecisionLayerCell.wind_speed = cell_speed
            cell.DecisionLayerCell.wind_direction = cell_direction
            cell.DecisionLayerCell.wind_std_dev = cell_stdev
        except IndexError:
            pass
    session.commit()
