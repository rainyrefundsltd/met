# forecast_accuracy_finder.py

# Script to create a report on the accuracy of the met office deterministic forecast.

# 1) Input the latitude and the longitude of the point in the UK that you want to measure between the bounds of the UK
# 2) The code will download a lot of files into a temp folder and extract the data that you require for the given latitude and longitude.

# internal
from read_nc import latlon_to_rainfall
# from fetch_open_meteo import HistoricData

# external
import logging
import os
import pandas as pd



def get_met_office_forecast(dir, lat, long):

    """Input the folder name in data/asdi, and get the total rainfall forecast for a given location"""

    # List directory
    cwd_dir = os.path.join(os.getcwd(),"data/asdi",dir)
    dir_list = [os.path.join("data/asdi",dir, item) for item in os.listdir(cwd_dir)]

    logging.debug(f"Files in {dir}: {dir_list}")

    # loop through files in the directory and take values for the given lat/long
    arr = []
    forecast_publish_dt = pd.to_datetime(dir) # Get forecast date from folder fn
    for file in dir_list:
        
        # Get forecast date from filename
        forecast_dt = pd.to_datetime(file.split("/")[3].split("-")[0])
        
        # Query files in data/asdi folder
        rain_mm = latlon_to_rainfall(file,lat,long) * 1000
        arr.append([forecast_publish_dt, forecast_dt, rain_mm])

    return arr




def get_range_met_office_forecasts(lat, long, start_dt_str, end_dt_str):

    """Creates a date range from the start and end datetimes and then queries the asdi files."""

    # Create the date range
    date_range = [item.strftime("%Y%m%dT%H%MZ") for item in pd.date_range(start=start_dt_str, end=end_dt_str,tz='UTC')]

    # Create array for 
    arr = []
    for date in date_range:

        # Get forecast for date 
        _arr = get_met_office_forecast(date, lat, long)

        # Append to arr
        arr.append(_arr)

    # Convert to pd.DataFrame
    df = pd.DataFrame(arr[0])
    for item in enumerate(arr):
        # Create the df if it is the first item
        if item[0] == 0:
            df = pd.DataFrame(arr[0])
        else:
            df = pd.concat([df, pd.DataFrame(item[1])]).reset_index(drop=True)
    
    df.columns = ["forecast_publish_datetime_utc", "forecast_datetime_utc","thickness_of_rainfall_amount_mm"]
    df.sort_values(["forecast_publish_datetime_utc","forecast_datetime_utc"],inplace=True)

    return df.reset_index(drop=True)




def read_gpm_csvs_and_apply_logic(lat, long, start_dt_str, end_dt_str):

    # Read both csvs and concat
    df_23 = pd.read_csv("data/csvs/2023-04-01 00:00:00---2023-10-01 00:00:00.csv")
    df_24 = pd.read_csv("data/csvs/2024-04-01 00:00:00---2024-10-01 00:00:00.csv")
    df = pd.concat([df_23, df_24])
    del df_23, df_24

    # Get column from coordinates
    col = f"[{str(lat)}, {str(long)}]"

    # Set index to dt
    df.set_index(df.columns[0],drop=True,inplace=True)
    df.index = pd.to_datetime(df.index).tz_localize("UTC") # convert type to UTC
    df.index.name = "actual_datetime_utc"

    # Group by hour
    df = df.groupby(pd.Grouper(freq='h')).sum()

    # Get only relevant columns and rename
    df = pd.DataFrame(df[col])
    df.rename(columns={col: "gpm_IMERG-FR_mm"}, inplace=True)

    # Shift everything upwards to show HOW MUCH RAIN WILL HAVE FALLEN IN THE PREVIOUS HOUR (this matches MET Office forecast logic)
    df = df.shift(1)
    df = df.iloc[1:, :]

    return df




def get_weather_comparison_df(lat, long, start_dt_str, end_dt_str):

    """ 
    Pull data from Open Meteo (actual weather) & the MET Office (forecasted weather) for a given timeframe and coordinates 
    to examine in a df
    """

    # Get met office data
    df = get_range_met_office_forecasts(lat, long, start_dt_str, end_dt_str)

    # Read GPM csvs, convery to hourly and splice using start and end dates
    gpm_df = read_gpm_csvs_and_apply_logic(lat, long, start_dt_str, end_dt_str)
    
    # Combine forecast and actuals into one table
    df = df.merge(gpm_df, right_on="actual_datetime_utc", left_on="forecast_datetime_utc")
    
    return df




def create_forecast_accuracy_report(lat, long, start_dt_str, end_dt_str):

    # Get data df
    df = get_weather_comparison_df(lat, long, start_dt_str, end_dt_str)

    # Rearrange to daily, this is taking data from 7am -> midnight
    df = df.drop(columns=["forecast_datetime_utc"]).groupby("forecast_publish_datetime_utc").sum()

    # Add column to show coordinates
    df["latitude"] = float(lat)
    df["longitude"] = float(long)

    return df



if __name__ == "__main__":

    # Set logging to INFO if ran on the cmd
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Read csv with coords
    df = pd.read_csv("data/csvs/random_uk_land_coords.csv", index_col=0)

    # For concat
    arr = []

    for index, row in df.iterrows():

        for year in [23,24]:

            # Only summer dates
            start_dt_str = f"20{str(year)}0401T0700Z"
            end_dt_str = f"20{str(year)}0930T0700Z"    

            # Input the historic and forecasted values and create an accuracy report
            _df = create_forecast_accuracy_report(row['lat'], row['long'], start_dt_str, end_dt_str)

            # Append to arr for concat
            arr.append(_df)

    # Concatenate coordinate reports
    df_concat = pd.concat(arr, ignore_index=False)

    # Output to csv
    df_concat.to_csv(os.path.join(os.getcwd(), "nimrod_comparison.csv"))
