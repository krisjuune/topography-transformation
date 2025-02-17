# %%
import numpy as np
import numpy.ma as ma
from math import pi, sin, cos, sqrt
from pathlib import Path
import netCDF4 as nc4
import datetime as dt
from coordinate_transformation.functions.transform import \
    get_cartesian_distance, cartesian_to_geographic, geographic_to_geocentric, radius_cnt, wgs84
from coordinate_transformation.functions.domain import \
    truncate_domain
from benchmark.functions import get_curvature_wgs84, get_nc_curvature, check_nc, plot_curvature

# %% Define function

# TODO: add option for stations_loc already in lat, lon and not Cartesian

##### Define get .nc files ######
def get_relabelling_files(stations_loc, bathymetry, lat, lon, geo = False,  
                          src_lat = 37.5, src_lon = -16.5):
    """
    Stations_loc has two rows, first for x and second for y coordinates of stations. 
    Here the src_lat and _lon refer to the source location of the stations file, i.e. the lat and 
    lon of 0,0 in the cartesian coordinate system. 
    """
    # get latitude and longitude of stations relative to src_lat, src_lon (0,0)
    lat_stations, lon_stations = cartesian_to_geographic(stations_loc[0], \
    stations_loc[1], src_lon=src_lon, src_lat=src_lat)
    rel_bathy = (2000.0*(-1) - bathy)*(-1) # relative to seafloor in flat model in m, 
    # change to 2000m as OBS depth changing for runs with bathymetry and only pressure source in fluid
    rel_bathy = np.transpose(rel_bathy)

    # loop over each 'station' location
    for i in range(len(stations_loc[0])): 
        # get properties for the i-th station locality, all in m
        x_i, y_i = get_cartesian_distance(lon, lat, src_lat=lat_stations[i], src_lon=lon_stations[i])
        radius_i = radius_cnt(geographic_to_geocentric(lat_stations[i]))
        radius_i = radius_cnt(geographic_to_geocentric(lat_stations[i]))
        # the next line is the bottle neck, can take hours (double for loop in function)
        # curvature_i = get_curvature_wgs84(lat, lon, radius=radius_i, theta=lat_stations[i], phi=lon_stations[i])
        
        # # save datasets for the i-th station
        # filename_curvature = 'outputs/' + 'curvature_' + str(abs(int(round(lat_stations[i]*10)))) + '_' \
        #     + str(abs(int(round(lon_stations[i]*10))))
        filename_bathymetry = 'outputs/' + 'bathymetry_' + str(abs(int(round(lat_stations[i]*10)))) + '_' \
            + str(abs(int(round(lon_stations[i]*10))))
        # get_nc_curvature(filename_curvature, curvature_i, x_i, y_i)
        # print('Got'+str(i)+'curvature')
        get_nc_curvature(filename_bathymetry, rel_bathy, x_i, y_i)
        print('Got'+str(i)+'bathymetry')

def get_moho_relabelling(moho, lat, lon, stations_loc, src_lat=37.5, src_lon=-16.5): 
    """
    Stations_loc has two rows, first for x and second for y coordinates of stations. 
    Here the src_lat and _lon refer to the source location of the stations file, i.e. the lat and 
    lon of 0,0 in the cartesian coordinate system. 
    """
    # get latitude and longitude of stations relative to src_lat, src_lon (0,0)
    lat_stations, lon_stations = cartesian_to_geographic(stations_loc[0], \
    stations_loc[1], src_lon=src_lon, src_lat=src_lat)
    rel_moho = rel_moho = (-12170 - moho)*(-1)  
    rel_moho = np.transpose(rel_moho) 
    # reverse the order of lat & moho along lat (-90 to 90 N) for axisem3d
    lat = lat[::-1]
    rel_moho = rel_moho[:, ::-1] # reverse it for all rows, orig moho[lat, lon] but transposed

    # loop over each 'station' location
    for i in range(len(stations_loc[0])): 
        # get properties for the i-th station locality, all in m
        # TODO should x and y really be in m? in stations in km, for sure, in relabelling I think in m 
        x_i, y_i = get_cartesian_distance(lon, lat, src_lat=lat_stations[i], src_lon=lon_stations[i])
        
        # save datasets for the i-th station
        filename_moho = 'outputs/' + 'moho_' + str(abs(int(round(lat_stations[i]*10)))) + '_' \
        + str(abs(int(round(lon_stations[i]*10))))
        get_nc_curvature(filename_moho, rel_moho, x_i, y_i)
        if i % 3 == 0: 
            print('Got'+str(i)+'moho')

# %% Load all data

##### Get input files for .nc ######
# stations in cartesian for getting source coordinates in lat,lon
# bathymetry with lat, lon in geographic for getting 
# radius? 

# Get data
data_folder = Path('coordinate_transformation/raw_data/GEBCO_2019')
file2open = data_folder / 'GEBCO_2019.nc' #file with location
nc_GEBCO = nc4.Dataset(file2open, 'r')
raw_lat = nc_GEBCO.variables['lat'][:] # in degrees N
raw_lon = nc_GEBCO.variables['lon'] [:]# in degrees E 
raw_elevation = nc_GEBCO.variables['elevation'] [:] 
# in m as height above reference ellipsoid

data_folder = Path('coordinate_transformation/raw_data/crust1.0/')
file2open = data_folder / 'depthtomoho.xyz' #file with location
# lon (deg E), lat (deg N), depth (km, negative down)
f = open(file2open, 'r')
contents = np.loadtxt(f, usecols=[0,1,2])
lon_moho = contents[:360,0]
lat_moho = contents[0::360,1]
moho = contents[:,2]*1000 # in m as height above reference ellipsoid
moho = moho.reshape((180,360))

# Unmask arrays
raw_lat = np.ma.getdata(raw_lat)
raw_lon = np.ma.getdata(raw_lon)
raw_elevation = np.ma.getdata(raw_elevation)

# Truncate arrays to slightly smaller 
lat_max = 50
lat_min = 24
lon_max = 1
lon_min = -35 
bounds = np.array([lat_max, lat_min, lon_max, lon_min])
lat, lon, bathy = truncate_domain(raw_lat, raw_lon, raw_elevation, bounds)
lat_moho, lon_moho, moho = truncate_domain(lat_moho, lon_moho, moho, bounds)

# Set station locations as [[x_locations],[y_locations]] in m
stations_loc = np.array([[0.0, 28.3, 60.1, 91.9, 120.2, 149.5, -28.3, -60.1, -91.9, -120.2, -149.5, \
    -28.3, -60.1, -91.9, -120.2, -149.5, 28.3, 60.1, 91.9, 120.2, 149.5], \
    [0.0, 28.3, 60.1, 91.9, 120.2, 149.5, 28.3, 60.1, 91.9, 120.2, 149.5, \
    -28.3, -60.1, -91.9, -120.2, -149.5, -28.3, -60.1, -91.9, -120.2, -149.5]]) * 1000

#%% Call the function -- NB! Takes a long while...

##### Get .nc files ######
# call the function for src_lat 37.5 and src_lon -16.5
get_relabelling_files(stations_loc, bathy, lat, lon)

# get_moho_relabelling(moho, lat_moho, lon_moho, stations_loc)

# %%plot curvature
data_folder = Path('outputs/')
file2open = data_folder / 'curvature_362_148.nc' #file with location
nc_GEBCO = nc4.Dataset(file2open, 'r')
x = nc_GEBCO.variables['x'][:] # in m
y = nc_GEBCO.variables['y'] [:] # in m
z = nc_GEBCO.variables['z'] [:] # in m
x = np.ma.getdata(x)
y = np.ma.getdata(y)
z = np.ma.getdata(z)

lat_y, lon_x = cartesian_to_geographic(x,y,src_lon=-14.8, src_lat=36.2)
plot_curvature(lat_y, lon_x, z, src_lat=36.2, src_lon=-14.8, filename='test')
