
# function to fetch historic actual weather data from open meteo


import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from typing import Dict, Any
from datetime import timezone, timedelta


def HistoricData(params: Dict[str, Any]) -> pd.DataFrame:

    """
    Fetch historical weather data using Open-Meteo API.

    Parameters
    ----------
    params : dict
        Dictionary containing parameters for the data pull. Expected keys:
            latitude : float
                Latitude of the historic weather data location.
            longitude : float
                Longitude of the historic weather data location.
            start_date : str
                Inclusive start date in 'YYYY-MM-DD' format, timezone = "Europe/London".
            end_date : str
                Inclusive end date in 'YYYY-MM-DD' format, timezone = "Europe/London".
            hourly : str
                Defines which historic data parameter should be pulled (e.g., "precipitation").
            timezone : str
                Timezone for the start and end dates, currently set to "Europe/London".

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame containing:
            An arbitrary index.
            'date' : datetime
                Hourly data column in UTC.
            'precipitation' : float
                Hourly precipitation data measured in mm.
    """

    # TZ always GMT
    params["timezone"] = "GMT"

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_precipitation = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True).tz_convert(
                timezone(timedelta(seconds=response.UtcOffsetSeconds()))
            ),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True).tz_convert(
                timezone(timedelta(seconds=response.UtcOffsetSeconds()))
            ),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }
    hourly_data["precipitation_mm"] = hourly_precipitation
    hourly_dataframe = pd.DataFrame(data=hourly_data)
    # hourly_dataframe.date = hourly_dataframe.date.dt.tz_convert(real_timezone)

    return hourly_dataframe


if __name__ == "__main__":

        temp = HistoricData({
            'latitude': 53.869932,
            'longitude': -1.379663,
            'start_date': '2024-11-01',
            'end_date': '2024-11-31',
            'hourly': 'precipitation'
        })

        print(temp)
