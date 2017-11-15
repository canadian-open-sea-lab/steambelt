import time

import threading
import Queue

import numpy as np
import pandas as pd

from shapely.geometry import Polygon
from geoalchemy2.shape import to_shape, from_shape

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


def generate_grid_cell(grid, x, y):
    bounding_box = Polygon([
        (x, y),
        (x + grid.cell_width, y),
        (x + grid.cell_width, y + grid.cell_height),
        (x, y + grid.cell_height)
    ])

    return dict(
        grid_id=grid.id,
        bounding_box=from_shape(bounding_box)
    )

def dump_queue(queue):
    """
    Empties all pending items in a queue and returns them in a list.
    """
    result = []

    for i in iter(queue.get, 'STOP'):
        result.append(i)
    time.sleep(.1)
    return result


def generate_grid_cell(grid, x, y, queue):
    bounding_box = Polygon([
        (x, y),
        (x + grid.cell_width, y),
        (x + grid.cell_width, y + grid.cell_height),
        (x, y + grid.cell_height)
    ])

    queue.put(models.GridCell(
        grid_id=grid.id,
        bounding_box=from_shape(bounding_box, srid=4326)
    ))


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

    cell_queue = Queue.Queue()
    threads = []
    i = 0
    for y, r in grid_cells.iterrows():
        for x, v in r.iteritems():
            t = threading.Thread(target=generate_grid_cell, args=(grid, x, y, cell_queue))
            t.start()
            threads.append(t)
        i += 1
        if i % 1000 == 0:
            print("Initializing threads: %s%%" % (i / len(grid_cells) * 100))
            for t in threads:
                t.join()
            cell_queue.put('STOP')
            cell_mappings = dump_queue(cell_queue)
            print("Generated %s cells, inserting" % (len(cell_mappings)))
            for c in cell_mappings:
                session.add(c)
            session.flush()
            cell_queue = Queue.Queue()
            threads = []
    for t in threads:
        t.join()
    cell_queue.put('STOP')
    cell_mappings = dump_queue(cell_queue)
    print(cell_mappings[0])
    print("Generated %s cells, inserting" % (len(cell_mappings)))
    for c in cell_mappings:
        session.add(c)
    session.commit()
    session.close()