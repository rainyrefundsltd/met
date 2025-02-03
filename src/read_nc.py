
"""Quick file to read an NC file. Initally created to determine the naming convention of the ASDI files"""

import netCDF4 as nc
import numpy as np
import pyproj

# Load the NetCDF file
dataset = nc.Dataset("data/asdi/20240202T0000Z-20240203T0100Z-PT0025H00M-rainfall_accumulation-PT01H.nc")

# Read the coordinate variables
x = dataset.variables["projection_x_coordinate"][:]
y = dataset.variables["projection_y_coordinate"][:]

# Define the projection from Lambert Azimuthal Equal Area to lat/lon
proj = pyproj.Proj("+proj=laea +lat_0=49.0 +lon_0=-2.0 +datum=WGS84")

# Function to find the nearest index
def find_nearest(array, value):
    return np.abs(array - value).argmin()

# Convert lat/lon to projected coordinates
lat, lon = 52.5, -1.5  # Replace with your desired location
x_target, y_target = proj(lon, lat)

# Find nearest grid point
x_idx = find_nearest(x, x_target)
y_idx = find_nearest(y, y_target)

# Extract the rainfall forecast
rainfall = dataset.variables["thickness_of_rainfall_amount"][y_idx, x_idx]

print(f"Rainfall forecast at ({lat}, {lon}): {rainfall} mm")

# Close the dataset
dataset.close()