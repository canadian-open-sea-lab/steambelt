import requests
from netCDF4 import Dataset
import numpy as np
import pandas as pd
import os
from shapely import geometry

def aggregate_wind():
    return


def aggregate_depth(grid_cell, path):
    depth_values = []
    for filename in os.listdir(path):
        if filename.endswith(".nc"):
            cell = Dataset(path+filename)
            bounds = geometry.Polygon([
                        [cell.Longitude_BL, cell.Latitude_BL],
                        [cell.Longitude_TL, cell.Latitude_TL],
                        [cell.Longitude_TR, cell.Latitude_TR],
                        [cell.Longitude_BR, cell.Latitude_BR]
                    ])

            if bounds.contains(grid_cell) or grid_cell.contains(bounds) or grid_cell.overlaps(bounds):
                min_lon,min_lat,max_lon,max_lat = list(grid_cell.intersection(bounds).bounds)
                lons = cell.variables['COLUMNS'][:]
                lats = cell.variables['LINES'][:]
                lo = cell.variables['COLUMNS'][((lons >= min_lon) & (lons <= max_lon ))]
                la = cell.variables['LINES'][((lats >=  min_lat) & (lats <= max_lat))]
                depths = cell.variables['DEPTH'][((lats >=  min_lat) & (lats <= max_lat)), ((lons >= min_lon) & (lons <= max_lon))]
                depth_matrix = pd.DataFrame(depths, index=la, columns=lo)
                if len(depth_values) > 0:
                    depth_values = np.concatenate((depth_values, depth_matrix.values.flatten()[~np.isnan(depth_matrix.values.flatten())]))
                else:
                    depth_values = depth_matrix.values.flatten()[~np.isnan(depth_matrix.values.flatten())]
            cell.close()
    return np.average(depth_values)
