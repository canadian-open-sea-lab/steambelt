DATABASE_CONNECTOR = 'postgresql://steambelt:opensealab@acdac.ca/steambelt'

# yearmonth example:    201710
# day example:          31
# start_time example:   2017-10-31T00%3A00%3A00Z
# end_time example:     2017-10-31T00%3A00%3A00Z
# hour example:         1800
WIND_THREDDS_URL = ('https://www.ncei.noaa.gov/thredds/ncss/gfs-004-files'
                    '/%(yearmonth)s/%(yearmonth)s%(day)s/gfs_4_%(yearmonth)s%(day)s_%(hour)s_000.grb2?'
                    'var=u-component_of_wind_height_above_ground&'
                    'var=v-component_of_wind_height_above_ground&horizStride=1&'
                    'time_start=%(start_time)s&time_end=%(end_time)s&timeStride=1&'
                    'vertCoord=15&addLatLon=true')
