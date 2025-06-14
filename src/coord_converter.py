
from pyproj import Transformer
from shapely.geometry import Point, shape
import fiona

# Load UK land boundaries (in EPSG:4326)
with fiona.open("boundary_files/united_kingdom_United_Kingdom_Country_Boundary.shp") as shp:
    land_polygons = [shape(feature["geometry"]) for feature in shp]

# Transformer from EPSG:27700 to EPSG:4326
transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

def coord_converter(x_projection, y_projection):
    """Convert EPSG:27700 to EPSG:4326."""
    lon, lat = transformer.transform(x_projection, y_projection)
    return lat, lon

def is_land(x_projection, y_projection):
    """Check whether the given EPSG:27700 coordinate lies on land."""
    lon, lat = transformer.transform(x_projection, y_projection)
    point = Point(lon, lat)  # now in EPSG:4326
    return any(polygon.contains(point) for polygon in land_polygons)

if __name__ == "__main__":
    
    x_projection = 580000
    y_projection = 80000

    lat, lon = coord_converter(x_projection, y_projection)
    print(f"Latitude (EPSG:4326): {lat}")
    print(f"Longitude (EPSG:4326): {lon}")

    if is_land(x_projection, y_projection):
        print("This point is on land.")
    else:
        print("This point is in the sea.")



# EPSG:27700 (Easting, Northing): 532710, 180370
# EPSG:4326 (Latitude, Longitude): 51.5045, -0.0865

# EPSG:27700: 384458, 398397
# EPSG:4326: 53.4794, -2.2453

# EPSG:27700: 325311, 673361
# EPSG:4326: 55.9486, -3.1999