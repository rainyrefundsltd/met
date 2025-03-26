# forecast_accuracy_finder.py

# Script to create a report on the accuracy of the met office deterministic forecast.

# 1) Input the latitude and the longitude of the point in the UK that you want to measure between the bounds of the UK
# 2) The code will download a lot of files into a temp folder and extract the data that you require for the given latitude and longitude.

# internal
from read_nc import get_rainfall_m
from fetch_open_meteo import HistoricData

# external
import logging
import os
import pandas as pd



def get_met_office_forecast(dir, lat, long):

    """Input the folder name in data/asdi, and get the total rainfall forecast for a given location"""

    # List directory
    cwd_dir = os.path.join(os.getcwd(),"data/asdi",dir)
    dir_list = [os.path.join("data/asdi",dir, item) for item in os.listdir(cwd_dir)]
    print(dir_list)

    logging.debug(f"Files in {dir}: {dir_list}")

    # loop through files in the directory and take values for the given lat/long
    arr = []
    forecast_publish_dt = pd.to_datetime(dir) # Get forecast date from folder fn
    for file in dir_list:
        
        # Get forecast date from filename
        forecast_dt = pd.to_datetime(file.split("/")[3].split("-")[0])
        
        # Query files in data/asdi folder
        rain_mm = float(get_rainfall_m(file,lat,long).data) * 1000
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



def get_weather_comparison_df(lat, long, start_dt_str, end_dt_str):

    """ 
    Pull data from Open Meteo (actual weather) & the MET Office (forecasted weather) for a given timeframe and coordinates 
    to examine in a df
    """

    # Get met office data
    df = get_range_met_office_forecasts(lat, long, start_dt_str, end_dt_str)

    # Create required parameters for Open Meteo data pull
    open_meteo_df = HistoricData({
    'latitude': lat,
    'longitude': long,
    'start_date': pd.to_datetime(start_dt_str).strftime("%Y-%m-%d"),
    'end_date': pd.to_datetime(end_dt_str).strftime("%Y-%m-%d"),
    'hourly': 'precipitation'
    }).dropna()

    # Combine forecast and actuals into one table
    df = df.merge(open_meteo_df, right_on="date", left_on="forecast_datetime_utc")
    
    return df



if __name__ == "__main__":

    # Set logging to INFO if ran on the cmd
    logging.basicConfig(level=logging.CRITICAL)
    logger = logging.getLogger(__name__)

    # Set up args
    # dir = "20240930T0600Z" 
    start_dt_str = "20230301T0600Z"
    end_dt_str = "20250324T0600Z"
    lat = 53.48095
    long = -2.23743

    df = get_weather_comparison_df(lat, long, start_dt_str, end_dt_str)
    df.drop(columns=["forecast_datetime_utc","date"]).groupby("forecast_publish_datetime_utc").sum()

    df.to_clipboard()

    # df = get_met_office_forecast(dir,lat,long)
    print(f"{df}\n SUM (mm): {df.thickness_of_rainfall_amount_mm.sum()}")