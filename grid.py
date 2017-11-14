import numpy as np
import pandas as pd

from shapely.geometry import Polygon
from geoalchemy2.shape import to_shape, from_shape

import progressbar

import models


def create_grid(name, bounding_box, cell_size=None, cell_width=None, cell_height=None):
    """Create an entry in the grid table.

    Returns
    -------
    grid(Grid): an sqlalchemy ORM entity for the created grid
    """

    if cell_size is not None and (cell_width is not None or cell_height is not None):
        raise Exception()
    elif cell_size is not None:
        cell_width = cell_size
        cell_height = cell_size

    grid = models.Grid(
        name=name,
        bounding_box=bounding_box,
        cell_width=cell_width,
        cell_height=cell_height
    )

    session = models.Session()
    loaded_grid = session.query(models.Grid).filter(models.Grid.name == name).one_or_none()
    if loaded_grid is not None:
        session.close()
        return loaded_grid
    session.add(grid)
    session.commit()
    session.close()
    return grid


def generate_grid_cells(grid):
    """Autogenerate a set of grid cells based on the grid specification.

    Parameters
    ----------
    grid(Grid): an sqlalchemy orm entity for the target grid

    """
    bbox_shape = to_shape(grid.bounding_box)
    min_x, min_y, max_x, max_y = bbox_shape.bounds

    x_range = np.arange(min_x, max_x, grid.cell_width)
    y_range = np.arange(min_y, max_y, grid.cell_height)

    grid_cells = pd.DataFrame(index=y_range, columns=x_range)

    session = models.Session()
    cell_mappings = []
    i = 0
    for y, r in grid_cells.iterrows():
        for x, v in r.iteritems():
            bounding_box = Polygon([
                (x, y),
                (x + grid.cell_width, y),
                (x + grid.cell_width, y + grid.cell_height),
                (x, y + grid.cell_height)
            ])

            cell_mappings.append(dict(
                grid_id=grid.id,
                bounding_box=from_shape(bounding_box)
            ))
        i += 1
        print("%s/%s" % (i, len(grid_cells)))
    print("Generates %s cells, inserting" % (len(cell_mappings)))
    session.bulk_insert_mappings(models.GridCell, cell_mappings)
    session.commit()
    session.close()