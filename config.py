# DATABASE_CONNECTOR = 'postgresql://steambelt:opensealab@acdac.ca/steambelt'
DATABASE_CONNECTOR = 'postgresql://postgres:winner@localhost/steambelt'

# yearmonth example:    201710
# day example:          31
# cycle_runtime example:1800
# start_time example:   2017-10-31T00%3A00%3A00Z
# end_time example:     2017-10-31T00:00:00Z
WIND_THREDDS_URL = ('https://www.ncei.noaa.gov/thredds/ncss/gfs-004-files'
                    '/%(yearmonth)s/%(yearmonth)s%(day)s/gfs_4_%(yearmonth)s%(day)s_%(cycle_runtime)s_000.grb2?'
                    'var=u-component_of_wind_height_above_ground&'
                    'var=v-component_of_wind_height_above_ground&horizStride=1&'
                    'time_start=%(start_time)s&time_end=%(end_time)s&timeStride=1&'
                    'vertCoord=15&addLatLon=true')

WIND_FILE_DIR = '/Users/brad/Documents/open_sea_lab/data/wind'
