import models


def generate_dicision_layer(grid):
    """Generate a new decision layer and a set of decision layer cells.

    Parameters
    ----------
    grid(Grid): an sqlalchemy ORM entity for the target grid

    Returns
    -------
    decision_layer(DecisionLayer): an sqlalchemy ORM entity for the created decision layer
    """
    return