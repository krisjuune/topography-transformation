import numpy as np
from math import pi, sin, cos, sqrt

def wgs84(): 
    """
    WGSS84 coordinate system with Greenwich as lon = 0.
    Define Earth's semi-major, semi-minor axes,  eccentricity, 
    and inverse flattening, in this order. 
    """
    # set semi-major axis of the oblate spheroid Earth, in m
    a = 6378137.0
    # set semi-minor axis of the oblate spheroid Earth, in m
    b = 6356752.314245
    # calculate inverse flattening f
    f = a/(a-b)
    # calculate squared eccentricity e
    e_2 = (a**2-b**2)/a**2
    return(a,b,e_2,f)

def geographic_to_geocentric(lat):
    """
    Calculate latitude defined in the wgs84 coordinate 
    system given the geographic latitude. Input and 
    output latitude in degrees. 
    """
    e_2 = wgs84()[2] # eccentricity as defined by wgs84 
    lat = np.rad2deg(np.arctan((1 - e_2) * np.tan(np.deg2rad(lat))))
    return lat

def radius_cnt(lat):
    """
    Get radius at latitude lat for the Earth as defined 
    by the wgs84 system. 
    """
    a = wgs84()[0]
    b = wgs84()[1]
    # Calculate radius for reference ellipsoid, in m 
    lat = pi/180*lat
    # for i in range(len(lat)): 
    r_cnt = np.sqrt((a**2*(np.cos(lat)**2)) + \
        (b**2*(np.sin(lat)**2)))
    return(r_cnt)

def get_cartesian_distance(lon, lat, \
    src_lat = 37.5, src_lon = -16.5):
    """
    Calculate distance of each point of lat and lon
    from the source location on a flat surface, 
    tangential to the source. Returns x (lon), y 
    (lat) in m for AxiSEMCartesian. 
    """
    # transform to geocentric
    lat = geographic_to_geocentric(lat)
    src_lat = geographic_to_geocentric(src_lat)

    # find radius at source
    r_greatcircle = radius_cnt(src_lat)
    # find radius of small circle at source lat
    r_smallcircle = r_greatcircle*np.cos(np.deg2rad(src_lat))
    # convert differences in angles to radians
    phi = pi/180*lon - pi/180*src_lon
    theta = pi/180*lat - pi/180*src_lat
    # explanation of the physical meaning of phi, theta
    # in notebook

    # preallocate output arrays
    x = np.zeros(len(phi), float)
    y = np.zeros(len(theta), float)
    # find distances
    x = r_smallcircle*np.tan(phi)
    y = r_greatcircle*np.tan(theta)

    return(x,y)

def cartesian_to_geographic(x, y, \
    src_lon = -16.5, src_lat = 37.5):
    """
    Calculate lat and lon (of stations), given the x and 
    y distances from source. Transformation first into 
    geocentric coordinates, and then geographic. 
    x, y in m, and lat, lon in degrees. 
    """
    # transform source to geocentric
    src_lat = geographic_to_geocentric(src_lat)

    # find radius of small and great circle at source
    r_greatcircle = radius_cnt(src_lat)
    r_smallcircle = r_greatcircle*np.cos(np.deg2rad(src_lat))

    # get phi and theta (in radians)
    phi = np.arctan(x/r_smallcircle)
    theta = np.arctan(y/r_greatcircle)

    # get lat, lon (in degrees) geocentric
    lon = np.rad2deg(phi) + src_lon
    lat = np.rad2deg(theta) + src_lat

    # get lat geographic
    a = wgs84() [0]
    b = wgs84() [1]
    c = (a/b)*(a/b)
    lat = np.rad2deg(np.arctan(c * np.tan(np.deg2rad(lat))))

    return(lat, lon)

def rotation_matrix(colat,phi): 
    """
    Colat - colatitude of source, phi - longitude of 
    source (both in radians). Function returns a 3-by-3
    rotation matrix. 
    """
    # Preallocate output array
    Q = np.zeros((3,3)) 
    # Fill in rotation matrix
    Q[0,0] = cos(colat)*cos(phi)
    Q[0,1] = -sin(phi)
    Q[0,2] = sin(colat)*cos(phi)
    Q[1,1] = cos(colat)*sin(phi)
    Q[1,1] = cos(phi)
    Q[1,2] = sin(colat)*sin(phi)
    Q[2,0] = -sin(colat)
    Q[2,1] = 0
    Q[2,2] = cos(colat)

    return(Q)

def rotate_N_pole(src_lat, src_lon, x, y, z): 
    """
    This function dodge, rewrite for just rotating source
    lat & lon. 
    Input source grographic latitude & longitude, and data file in 
    Cartesian coordinates. Rotates to N pole using rotation_matrix. 
    Returns the rotated data in Cartesian coordinates.
    """
    # To radians
    src_lat = pi/180*src_lat
    src_lon = pi/180*src_lon

    # Get geocentric latitude, in rad
    e_2 = wgs84()[2]
    src_colat = np.arctan((1 - e_2) * np.tan(src_lat))

    # Preallocate output arrays
    (m,n) = x.shape
    x_rot = np.zeros((m,n), float)
    y_rot = np.zeros((m,n), float)
    z_rot = np.zeros((m,n), float)

    # Compute rotated x, y, z, using matrix multiplication matmul
    Q = rotation_matrix(src_colat, src_lon).transpose()
    for i in range(m): 
        a = np.concatenate((x_rot[0,], y_rot[0,], z_rot[0,]), axis = 0)
        a = a.reshape(3,n)
        b = np.concatenate((x[0,], y[0,], z[0,]), axis = 0)
        b = b.reshape(3,n)
        a = np.matmul(Q, b)
        x_rot[i,] = a[0,]
        y_rot[i,] = a[1,]
        z_rot[i,] = a[2,]
    
    return(x_rot, y_rot, z_rot)