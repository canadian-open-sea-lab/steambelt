from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon

import models

import grid
import decision_layer
import layers


def main():
    bounds = Polygon([
        (-35.9948, 25.0052),
        (-35.9948, 84.9926),
        (41.7718, 84.9926),
        (41.7718, 25.0052)
    ])

    session = models.Session()

    g = grid.create_grid('Emodnet', from_shape(bounds, srid=4326), 0.5)
    grid.generate_grid_cells(g)

    # dl = decision_layer.generate_decision_layer(session, g)
    # decision_layer.generate_decision_layer_cells(session, dl)

    # decision_layer.generate_decision_layer_cell_depth(session, '/Users/alexnunes/Desktop/osl_bathymetry/bathymetry/', g)
    # decision_layer.generate_decision_layer_cell_seabed(session,g)
    

    wind_files = layers.download_wind_files()
    decision_layer.generate_decision_layer_cell_wind(session, g)


    session.close()
    return

if __name__ == '__main__':
    main()
