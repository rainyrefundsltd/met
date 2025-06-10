import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import contextily as ctx


def _generate_land_point(shape, cities, probabilities, max_attempts=100):
    """Generate a random point on land, biased towards population centers"""
    uk_bounds = {"lon_min": -7.5, "lon_max": 2.0, "lat_min": 50.0, "lat_max": 59.0}
    
    for _ in range(max_attempts):
        # Choose whether to generate near a city or randomly
        if np.random.random() < 0.25:  # 25% chance to generate near a city
            city_idx = np.random.choice(cities.index, p=probabilities)
            city = cities.loc[city_idx]
            lon = city["Longitude"] + np.random.normal(0, 0.5)
            lat = city["Latitude"] + np.random.normal(0, 0.5)
        else:  # 75% chance to generate anywhere in UK
            lon = np.random.uniform(uk_bounds["lon_min"], uk_bounds["lon_max"])
            lat = np.random.uniform(uk_bounds["lat_min"], uk_bounds["lat_max"])
        
        point = Point(lon, lat)
        if point.within(shape):
            return (lon, lat)
    
    raise ValueError("Could not generate point on land after 100 attempts")



def _generate_png(map, gdf, cities):

    # Plot with Enhanced Styling
    plt.style.use('default')
    plt.rcParams.update({
        'font.size': 12,
        'axes.titlesize': 16,
        'axes.labelsize': 12,
        'grid.alpha': 0.3,
        'grid.linestyle': '--'
    })

    fig, ax = plt.subplots(figsize=(14, 12))

    # Plot UK with modern color
    map.plot(ax=ax, color="#f0f0f0", edgecolor="#444444", linewidth=0.5)

    # Add basemap
    try:
        ctx.add_basemap(ax, crs=map.crs, source=ctx.providers.Stamen.TonerLite)
    except:
        print("Basemap not loaded. Install with: pip install contextily")

    # Plot all points with same size (20)
    gdf.plot(ax=ax, color="#e63946", markersize=20, alpha=0.8, 
            edgecolor="white", linewidth=0.5)

    # Annotate major cities
    for _, row in cities.iterrows():
        ax.annotate(row["City"], xy=(row["Longitude"], row["Latitude"]), 
                    xytext=(5, 5), textcoords="offset points",
                    fontsize=10, color="#333333",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.7))

    # Style adjustments
    ax.set_xlim(-7.5, 2.0)
    ax.set_ylim(50.0, 59.0)
    ax.set_title("UK Points: On Land & Population-Biased", pad=20)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True)

    plt.tight_layout()
    plt.savefig("data/pngs/uk_land_population_points.png", dpi=300, bbox_inches="tight")
    plt.show()



def get_uk_coordinates(shapefile_path, city_prob=0.25, create_graph=False, create_csv=False):
    
    # Load UK Map
    world = gpd.read_file(shapefile_path)
    uk_map = world[world["SOVEREIGNT"] == "United Kingdom"]
    uk_shape = uk_map.geometry.union_all()

    # Load UK Cities with Population Data
    cities = pd.DataFrame({
        "City": ["London", "Birmingham", "Manchester", "Glasgow", "Liverpool", 
                "Bristol", "Sheffield", "Leeds", "Edinburgh", "Leicester"],
        "Latitude": [51.5074, 52.4862, 53.4808, 55.8642, 53.4084, 
                   51.4545, 53.3811, 53.8008, 55.9533, 52.6369],
        "Longitude": [-0.1278, -1.8904, -2.2426, -4.2518, -2.9916, 
                    -2.5879, -1.4701, -1.5491, -3.1883, -1.1398],
        "Population": [8900000, 1150000, 547000, 626000, 864000, 
                      567000, 518000, 474000, 482000, 443000]
    })
    probabilities = cities["Population"] / cities["Population"].sum()

    # Generate Random Points ON LAND with Population Bias
    land_coords = [_generate_land_point(uk_shape, cities, probabilities) for _ in range(100)]

    # Create GeoDataFrame
    geometry = [Point(lon, lat) for lon, lat in land_coords]
    gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")

    if create_graph:
        _generate_png(uk_map, gdf, cities)

    if create_csv:
        df = pd.DataFrame(land_coords)
        df.columns = ['long','lat']
        df.to_csv("data/csvs/random_uk_land_coords.csv")
    
    return land_coords



if __name__ == "__main__":
    
    shapefile_path = "data/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp"
    get_uk_coordinates(shapefile_path, create_graph=True, create_csv=True)