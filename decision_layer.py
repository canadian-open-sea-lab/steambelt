import datetime
from geoalchemy2.shape import to_shape
import models
from layers import aggregate_depth
import requests
import geojson
from geopandas import GeoSeries, GeoDataFrame


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

        wfs_url = "http://drive.emodnet-geology.eu/geoserver/EMODnetGeology/ows?service=WFS&version=1.1.0&request=GetFeature&typeName=EMODnetGeology:seabed_substrate250k_eu_sbss250k_seabed_substrate_eu&bbox="+str(grid_box.bounds).strip("(").strip(")")+"&outputFormat=application%2Fjson"
        r = requests.get(wfs_url)
        wfs_geo = geojson.loads(r.content)

        wfs_gdf = GeoDataFrame.from_features(wfs_geo)

        if len(wfs_gdf) > 0:
            if len(wfs_gdf[wfs_gdf.folk_5_substrate_class.str.contains('Rock & Boulders')]) > 0:
                cell.DecisionLayerCell.seabed = wfs_gdf[wfs_gdf.folk_5_substrate_class.str.contains('Rock & Boulders')].shape_area.sum()/grid_box.area * 100
            else:
                cell.DecisionLayerCell.seabed = 0
    session.commit()
