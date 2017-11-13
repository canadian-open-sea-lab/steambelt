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
    return