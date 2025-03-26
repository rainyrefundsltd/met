
"""Quick file to read an NC file. Initally created to determine the naming convention of the ASDI files"""

import netCDF4 as nc
import numpy as np
import pyproj
import logging
import sys
import os
import argparse

# Set logging to INFO if ran on the cmd
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

def get_rainfall_m(fn, lat, lon):
    
    """
    Convert the coordinates to Lambert Azimuthal Equal Area and query the NetCDF file 
    for the precipitation amount (m).
    """

    logger.info(f"Opening NetCDF file: {fn}")
    dataset = nc.Dataset(fn)
    
    logger.info("Reading coordinate variables: 'projection_x_coordinate' and 'projection_y_coordinate'")
    x = dataset.variables["projection_x_coordinate"][:]
    y = dataset.variables["projection_y_coordinate"][:]
    
    logger.info("Setting up the Lambert Azimuthal Equal Area projection")
    proj = pyproj.Proj("+proj=laea +lat_0=54.9 +lon_0=-2.5 +x_0=0 +y_0=0 +datum=WGS84")
    # proj = pyproj.Proj("+proj=laea +lat_0=49.0 +lon_0=-2.0 +datum=WGS84")
    
    def find_nearest(array, value):
        idx = np.abs(array - value).argmin()
        logger.debug(f"find_nearest: Searching for {value} in array; nearest index is {idx}")
        return idx

    logger.info(f"Converting latitude/longitude ({lat}, {lon}) to projected coordinates")
    x_target, y_target = proj(lon, lat)
    logger.info(f"Projected coordinates: x_target={x_target}, y_target={y_target}")
    
    logger.info("Finding the nearest grid point indices")
    x_idx = find_nearest(x, x_target)
    y_idx = find_nearest(y, y_target)
    logger.info(f"Nearest grid indices: x_idx={x_idx}, y_idx={y_idx}")
    
    logger.info("Extracting rainfall forecast from the dataset")
    rainfall = dataset.variables["thickness_of_rainfall_amount"][y_idx, x_idx]
    logger.info(f"Rainfall forecast at ({lat}, {lon}): {rainfall} m")
    
    logger.info("Closing the NetCDF dataset")
    dataset.close()
    
    return rainfall



if __name__ == "__main__":

    logger.info("Starting the rainfall data query application.")

    # # Parse command-line arguments
    # parser = argparse.ArgumentParser(
    #     description="Input coordinates and file name for data pull."
    # )
    # parser.add_argument(
    #     "--fn", required=True, help="Add the filename in the data/asdi folder."
    # )
    # parser.add_argument(
    #     "--lat", required=True, help="Latitude: within UK bounds [49.9, 60.9]."
    # )
    # parser.add_argument(
    #     "--long", required=True, help="Longitude: within UK bounds [-8.2, 1.7]."
    # )
    # args = parser.parse_args()

    # Parse the input arguments
    # try:
    #     FILENAME = os.path.join("data/asdi", args.fn)
    #     LAT = float(args.lat)
    #     LONG = float(args.long)
    #     logger.info("Parsed input arguments successfully: filename=%s, lat=%.4f, long=%.4f",
    #                 FILENAME, LAT, LONG)
    # except ValueError as e:
    #     logger.error("Error parsing input arguments: %s", e)
    #     sys.exit(1)
    
    # --------------- DEBUG---------------
    FILENAME = "data/asdi/20241222T0600Z/20241222T0800Z-PT0002H00M-rainfall_accumulation-PT01H.nc"
    LAT = 50
    LONG = 2

    # Query rainfall data
    logger.info("Querying rainfall data...")
    get_rainfall_m(FILENAME, LAT, LONG)
    logger.info("Completed rainfall data query.")

