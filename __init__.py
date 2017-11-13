from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon

import grid

def main():
    bounds = Polygon([
        (84, -34.5000000001998046),
        (84, 41.7812499296405804),
        (81.0000000000999876, 41.7812499296405804),
        (81.0000000000999876, -34.5000000001998046)
    ])
    
    print(grid.create_grid('Emodnet', from_shape(bounds, srid=4326), 0.002))
    return

if __name__ == '__main__':
    main()