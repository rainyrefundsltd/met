
"""Read an NC file easily using this script"""


import logging
import numpy as np
import xarray as xr
import pyproj
from typing import Union, Tuple, List

logger = logging.getLogger(__name__)

def find_nearest(array: np.ndarray, values: Union[float, np.ndarray]) -> Union[int, np.ndarray]:
    """
    Find the index of the nearest value(s) in an array.
    
    Args:
        array: 1D array to search in
        values: Value(s) to find (can be scalar or array)
        
    Returns:
        Index or array of indices of nearest values
    """
    array = np.asarray(array)
    values = np.asarray(values)
    # Reshape array for broadcasting (add new axis for values)
    array = array.reshape(-1, 1) if values.ndim > 0 else array
    idx = np.abs(array - values).argmin(axis=0)
    logger.debug(f"Found nearest indices {idx} for values {values}")
    return idx


def ensure_float(value: Union[np.ndarray, np.generic, float]) -> Union[float, np.ndarray]:
    """
    Ensure the value is returned as a Python float or numpy array of floats.
    
    Args:
        value: Input value which might be numpy numeric type
        
    Returns:
        Python float or numpy array of floats
    """
    if isinstance(value, (np.ndarray, np.generic)):
        return value.astype(float)
    return float(value)


def latlon_to_rainfall(nc_file_path: str, 
                      latitude: Union[float, List[float]], 
                      longitude: Union[float, List[float]],
                      return_indices: bool = False) -> Union[float, Tuple]:
    """
    Get rainfall forecast at nearest grid point to given latitude/longitude coordinates.
    
    Args:
        nc_file_path: Path to the netCDF file
        latitude: Latitude(s) to convert (degrees)
        longitude: Longitude(s) to convert (degrees)
        return_indices: Whether to return grid indices along with rainfall value
        
    Returns:
        Rainfall value(s) as float(s) or tuple of (rainfall, x_idx, y_idx) if return_indices=True
        For single points: returns Python float
        For multiple points: returns numpy array of floats
        
    Raises:
        ValueError: If input coordinates are outside grid bounds or shapes don't match
        KeyError: If required variables are missing from netCDF file
        RuntimeError: If there are problems with the NetCDF file
    """
    # Convert inputs to numpy arrays
    lat_arr = np.atleast_1d(np.asarray(latitude, dtype=float))
    lon_arr = np.atleast_1d(np.asarray(longitude, dtype=float))
    
    # Validate input shapes
    if lat_arr.shape != lon_arr.shape:
        raise ValueError("Latitude and longitude arrays must have the same shape")
    
    logger.info(f"Processing {lat_arr.size} coordinate(s): lat={lat_arr}, lon={lon_arr}")
    
    try:
        with xr.open_dataset(nc_file_path, decode_timedelta=False) as ds:
            # Validate required variables exist
            required_vars = ['lambert_azimuthal_equal_area', 
                           'projection_x_coordinate',
                           'projection_y_coordinate',
                           'thickness_of_rainfall_amount']
            for var in required_vars:
                if var not in ds:
                    raise KeyError(f"Required variable {var} not found in netCDF file")
            
            # Get projection parameters
            proj_var = ds['lambert_azimuthal_equal_area']
            proj_params = {
                'proj': 'laea',
                'lat_0': proj_var.latitude_of_projection_origin,
                'lon_0': proj_var.longitude_of_projection_origin,
                'x_0': proj_var.false_easting,
                'y_0': proj_var.false_northing,
                'a': proj_var.semi_major_axis,
                'b': proj_var.semi_minor_axis,
                'units': 'm'
            }
            
            # Create coordinate transformer
            transformer = pyproj.Transformer.from_crs(
                {'proj': 'latlong', 'ellps': 'WGS84', 'datum': 'WGS84'},
                proj_params,
                always_xy=True
            )
            
            # Convert coordinates (handles arrays automatically)
            x_target, y_target = transformer.transform(lon_arr, lat_arr)
            logger.debug(f"Projected coordinates: x={x_target}, y={y_target}")
            
            # Get grid coordinates
            x_arr = ds['projection_x_coordinate'].values
            y_arr = ds['projection_y_coordinate'].values
            
            # Find nearest grid indices (handles arrays)
            x_idx = find_nearest(x_arr, x_target)
            y_idx = find_nearest(y_arr, y_target)
            logger.info(f"Nearest grid indices: x_idx={x_idx}, y_idx={y_idx}")
            
            # Validate indices are within bounds
            if np.any(x_idx < 0) or np.any(x_idx >= len(x_arr)) or \
               np.any(y_idx < 0) or np.any(y_idx >= len(y_arr)):
                raise ValueError("Target coordinates outside grid bounds")
            
            # Get rainfall value(s) - handles both scalar and array indices
            rainfall = ds['thickness_of_rainfall_amount'].isel(
                projection_y_coordinate=y_idx,
                projection_x_coordinate=x_idx
            ).values
            
            # Convert to proper float types
            rainfall = ensure_float(rainfall)
            logger.info(f"Rainfall values: {rainfall} m")
            
            # Squeeze single values from arrays
            if lat_arr.size == 1:
                rainfall = rainfall.item() if isinstance(rainfall, np.ndarray) else rainfall
            
            if return_indices:
                if lat_arr.size == 1:
                    return rainfall, int(x_idx), int(y_idx)
                return rainfall, x_idx.astype(int), y_idx.astype(int)
            return rainfall
            
    except Exception as e:
        logger.error(f"Error processing coordinates: {str(e)}")
        raise RuntimeError(f"Failed to process coordinates: {str(e)}")


# Example usage
if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)
    
    nc_path = "data/asdi/20241222T0600Z/20241222T0800Z-PT0002H00M-rainfall_accumulation-PT01H.nc"
    
    try:
        # Single point - returns Python float
        lat, lon = 51.5074, -0.1278  # London
        rainfall = latlon_to_rainfall(nc_path, lat, lon)
        print(f"Single point rainfall: {rainfall} m (type: {type(rainfall)})")
        
        # Single point with indices
        rainfall, x_idx, y_idx = latlon_to_rainfall(nc_path, lat, lon, return_indices=True)
        print(f"Single point: {rainfall} m at grid ({x_idx}, {y_idx}) (types: {type(rainfall)}, {type(x_idx)}, {type(y_idx)})")
        
        # Multiple points - returns numpy array
        lats = [51.5074, 53.4808]  # London, Manchester
        lons = [-0.1278, -2.2426]
        rainfalls = latlon_to_rainfall(nc_path, lats, lons)
        print(f"Multiple points rainfall: {rainfalls} m (type: {type(rainfalls)}, dtype: {rainfalls.dtype})")
        
        # Multiple points with indices
        rainfalls, x_idxs, y_idxs = latlon_to_rainfall(nc_path, lats, lons, return_indices=True)
        for i, (rain, x, y) in enumerate(zip(rainfalls, x_idxs, y_idxs)):
            print(f"Point {i+1}: {rain} m at grid ({x}, {y}) (types: {type(rain)}, {type(x)}, {type(y)})")
            
    except Exception as e:
        print(f"Error: {str(e)}")

