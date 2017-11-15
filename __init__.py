from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon

import grid


def main():
    bounds = Polygon([
        (-35.9948, 25.0052),
        (-35.9948, 84.9926),
        (41.7718, 84.9926),
        (41.7718, 25.0052)
    ])

    g = grid.create_grid('Emodnet', from_shape(bounds, srid=4326), 0.5)
    grid.generate_grid_cells(g)
    return

if __name__ == '__main__':
    main()