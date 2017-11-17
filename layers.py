import os
import datetime
import calendar
import random
import tempfile

import requests

from netCDF4 import Dataset
import numpy as np
import pandas as pd
from shapely import geometry
import glob
from geoalchemy2.shape import to_shape

import config


def aggregate_wind(session, grid, target_dir=None):
    min_lon,min_lat,max_lon,max_lat = list(to_shape(grid.bounding_box).bounds)

    if target_dir is None:
        target_dir = config.WIND_FILE_DIR
    wind_files = glob.glob(os.path.join(target_dir, '*.nc'))
    file_count = 0
    aggregate_u = None
    aggregate_v = None

    all_u = []
    all_v = []
    for f in wind_files:
        dataset = Dataset(f, 'r')
        lon = np.array(dataset.variables['lon'][:]) - 180
        lon_filter = (lon >= min_lon) & (lon <= max_lon)
        filtered_lons = dataset.variables['lon'][lon_filter] - 180

        lat = dataset.variables['lat'][:]
        lat_filter = (lat >= min_lat) & (lat <= max_lat)
        filtered_lats = dataset.variables['lat'][lat_filter]

        u = pd.DataFrame.from_records(
            dataset.variables['u-component_of_wind_height_above_ground'][0, 0, lat_filter, lon_filter],
            index=filtered_lats,
            columns=filtered_lons
        )
        all_u.append(u)

        v = pd.DataFrame.from_records (
            dataset.variables['v-component_of_wind_height_above_ground'][0, 0, lat_filter, lon_filter],
            index=filtered_lats,
            columns=filtered_lons
        )
        all_v.append(v)

        file_count += 1
        if aggregate_u is None:
            aggregate_u = u
        else:
            aggregate_u.add(u)
        if aggregate_v is None:
            aggregate_v = v
        else:
            aggregate_v.add(v)
    mean_u = aggregate_u / file_count
    mean_v = aggregate_v / file_count

    stdev_u = compute_df_stdev(mean_v, all_v, file_count)
    stdev_v = compute_df_stdev(mean_v, all_v, file_count)
    stdev = (stdev_u + stdev_v) / 2

    direction = compute_wind_direction(u, v)
    speed = (mean_u ** 2 + mean_v ** 2) ** 0.5
    return speed, direction, stdev


def download_wind_files(target_dir=None):
    cycle_runtimes = ['0000', '0600', '1200', '1800']
    end_date = datetime.datetime.now()
    start_date = datetime.datetime(end_date.year-1, end_date.month, end_date.day)

    created_files = []
    for year, month in month_year_iter(start_date.month, start_date.year, end_date.month, end_date.year):
        c = calendar.Calendar(6)
        weeks =  c.monthdatescalendar(year, month)
        for w in weeks:
            target_day = w[random.randint(0, len(w) - 1)]
            while(target_day.month != month):
                target_day = w[random.randint(0, len(w) - 1)]
            for c in cycle_runtimes:
                hour = int(c)/100
                time = datetime.datetime(year, month, target_day.day, hour)
                url = config.WIND_THREDDS_URL % {
                    'yearmonth': '%04d%02d' % (year, month),
                    'day': '%02d' % target_day.day,
                    'cycle_runtime': c,
                    'start_time': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'end_time': time.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                r = requests.get(url, stream=True)
                r.raise_for_status()
                if target_dir is None:
                    target_dir = config.WIND_FILE_DIR
                with open(os.path.join(target_dir, '%s%s%s%s.nc' % (year, month, target_day.day, c)), 'wb') as tf:
                    for block in r.iter_content(1024):
                        tf.write(block)
    return created_files


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

    avg_depth = np.average(depth_values)
    if np.isnan(avg_depth):
        avg_depth = None
    return avg_depth


def month_year_iter( start_month, start_year, end_month, end_year ):
    ym_start= 12*start_year + start_month - 1
    ym_end= 12*end_year + end_month - 1
    for ym in range( ym_start, ym_end ):
        y, m = divmod( ym, 12 )
        yield y, m+1


def compute_df_stdev(mean, values, count):
    partial = None
    for df in values:
        part = (df - mean) ** 2
        if partial is None:
            partial = part
        else:
            partial.add(part)
    return (partial / count) ** 0.5


def compute_wind_direction(u, v):
    new_df = pd.DataFrame(index=u.index, columns=u.columns)
    degrees_per_radian = 57.29578

    for i, r in u.iterrows():
        for c, u_val in r.iteritems():
            v_val = v.loc[i, c]
            new_df.loc[i, c] = np.rad2deg(np.arctan2(-1 * v_val, -1 * u_val))
    return new_df

