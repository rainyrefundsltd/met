
""" Script to fetch GPM (Global Precipitation Measurement) Values"""
""" Seee this tutorial for more details - https://gpm-api.readthedocs.io/en/latest/tutorials/tutorial_02_RADAR_2A.html"""

import os
import pandas as pd
import datetime
from datetime import timedelta
import xarray as xr
import numpy as np

import gpm
from gpm.utils.geospatial import (
    get_circle_coordinates_around_point,
    get_country_extent,
)

def update_config(username_pps, password_pps, username_earthdata, password_earthdata):

    gpm.define_configs(
        username_pps=username_pps,
        password_pps=password_pps,
        username_earthdata=username_earthdata,
        password_earthdata=password_earthdata,
        base_dir=os.path.join(os.getcwd(), "data/GPM")
    )



def download_files(start_datetime, end_datetime, product="IMERG-FR", product_type="RS", storage="PPS", version=7):
    
    """Script to download all the files between start and end dates, does it one by one to avoid end of day hand error"""
    
    # Could just make a datetime range and loop through them
    # iterate in 30 minute chunks
    current_start = start_datetime
    while current_start < end_datetime:
        # compute the end of this chunk
        current_end = current_start + timedelta(minutes=30)
        if current_end > end_datetime:
            current_end = end_datetime

        print(f"Downloading from {current_start} to {current_end}…")
        try:
            gpm.download(
                product=product,
                product_type=product_type,
                version=version,
                start_time=current_start,
                end_time=current_end,
                storage=storage,
                force_download=False,
                verbose=True,
                progress_bar=True,
                check_integrity=False,
            )
        except Exception as e:
            # if there’s an error for this interval, log & decide whether to break or continue
            print(f"  ⚠️ Error on interval {current_start}–{current_end}: {e!r}")
            # you can choose to `break` here, or simply continue to the next day
            break

        # advance to next interval
        current_start = current_end




def half_hourly_gpm_rainfall_csv(start_datetime_str, end_datetime_str, coords_arr, csv_path=os.getcwd(), product="IMERG-FR", product_type="RS", storage="PPS", version=7):
    
    """
    Queries the data in the GPM folder - this folder must be populated using the download files function above before the rainfall data can be read.0
    """
    print("Opening dataset")
    ds = gpm.open_dataset(
        product="IMERG-FR",
        product_type="RS",
        version=7,
        start_time=datetime.datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S"),
        end_time=datetime.datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M:%S"),
        chunks="auto"
    )

    print("Taking just the precipiation")
    # Take just the precipitation data and add it to RAM
    da = ds["precipitation"]
    dt_arr = da.time.values

    # Loop through coordinates
    data_arr = []
    for coords in coords_arr:
        print(f"Find precip for [{coords[0]},{coords[1]}]")
        data = np.array(da.sel(lat=coords[0],lon=coords[1],method="nearest").data)
        data_arr.append((f"[{coords[0]}, {coords[1]}]", data))
    
    # lat_indices = []
    # lon_indices = []
    
    # print("Finding closest coordinates")
    # for i, coords in enumerate(coords_arr):
    #     print(f"Processing point {i}/{len(coords_arr)}...")
    #     lat_idx = np.abs(da.lat - coords[0]).argmin()
    #     lon_idx = np.abs(da.lon - coords[1]).argmin()
    #     lat_indices.append(lat_idx)
    #     lon_indices.append(lon_idx)

    # # Convert to numpy arrays for fast indexing
    # lat_indices = np.array(lat_indices)
    # lon_indices = np.array(lon_indices)

    # print("4/5 - Loading all required data in bulk...")
    # subset = da.isel(
    #     lat=xr.DataArray(lat_indices, dims="points"),
    #     lon=xr.DataArray(lon_indices, dims="points")
    # )
    # data = subset.load()  # Force load into memory
    
    # print("5/5 - Preparing results...")
    # data_arr = []
    # for i, coords in enumerate(coords_arr):
    #     if i % 100 == 0:
    #         print(f"Formatting result {i}/{len(coords_arr)}...")
    #     data_arr.append((f"[{coords[0]}, {coords[1]}]", data.isel(points=i).values))

    # Create df
    df = pd.DataFrame(np.swapaxes([item[1] for item in data_arr], 0, 1), columns=[item[0] for item in data_arr], index=dt_arr)

    # Multply half hourly points by 0.5 to convert from mm/hr to total amount of rainfall in that half hour period
    df = df * 0.5

    # Output to csv 
    print(f"Saving file to: {csv_path}")
    df.to_csv(os.path.join(csv_path,"data/csvs", f"{start_datetime_str}---{end_datetime_str}.csv"))



if __name__ == "__main__":
    
    # # Update config if required
    # username_pps = r"alexander.hall@rainyrefunds.com"  # likely your mail, all in lowercase
    # password_pps = r"alexander.hall@rainyrefunds.com"  # likely your mail, all in lowercase
    # username_earthdata = "rr_uk"
    # password_earthdata = "iMpspf-G-37W3FR"
    # update_config(username_pps, password_pps, username_earthdata, password_earthdata)

    # # # Script to download file
    # start_datetime = datetime.datetime.strptime("2024-08-29 04:30:00", "%Y-%m-%d %H:%M:%S")
    # end_datetime = datetime.datetime.strptime("2024-08-29 06:30:00", "%Y-%m-%d %H:%M:%S")
    # download_files(start_datetime,end_datetime)
    
    # Read the random coords arr
    df = pd.read_csv("data/csvs/random_uk_land_coords.csv",index_col=0)#.iloc[-2:,:]

    # Test this - [57.458645005339946, -5.241651905573681]

    # Create coords arr
    coords_arr = [(row['lat'],row['long']) for index, row in df.iterrows()]

    # coords_arr = [
    #     (52.826829, 0.652),                         # Houghton
    #     (51.49988, -0.29109),                       # Waterworks
    #     (51.1586418151855, -2.58320236206054),      # Glasonbury
    #     (55.8477254, -4.2344144),                   # TRNSMT
    #     (50.435834, -5.03676),                      # Boardmasters
    #     (53.869932, -1.379663),                     # Leeds Festival
    #     (51.46367, -0.985466),                      # Reading Festival
    #     (50.706523, -1.284858),                     # Isle of Wight Festival
    #     (50.639106, -2.208773),                     # Camp Bestival
    #     (52.842018, -1.354528)                      # Download Festival
    # ]

    half_hourly_gpm_rainfall_csv("2023-04-01 00:00:00", "2023-10-01 00:00:00", coords_arr)
    half_hourly_gpm_rainfall_csv("2024-04-01 00:00:00", "2024-10-01 00:00:00", coords_arr)

