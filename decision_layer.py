import datetime
from geoalchemy2.shape import to_shape
import models
from layers import aggregate_depth


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
