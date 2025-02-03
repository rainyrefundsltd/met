# Script to fetch ASDI data

import boto3
from datetime import datetime
import os
import numpy as np
from config import AWS_ACCESS, AWS_SECRET, AWS_REGION

BUCKET_NAME = "met-office-atmospheric-model-data"
PREFIX = "uk-deterministic-2km/"
FILE_NAME_FORMAT = "rainfall_accumulation-PT01H.nc" # precipitation_rate.nc


def _naming_convention(dt):
    """Use this naming convention throughout"""
    assert dt.minute == 0, "Error: Can go through forecasts that were published on the hour"
    return f"{dt.year:04}{dt.month:02}{dt.day:02}T{dt.hour:02}00Z"


def paginator(aws_access, aws_secret, aws_region, bucket_name, prefix, forecast_publish_date, FILE_NAME_FORMAT, output="print"):
    
    """ 
    Create paginator to read multiple bucket pages (which are limited to 1000)
    More details on Pagination here: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html
    """
    
    assert output == "print" or output == "np_arr", "output variable must be set to 'print' or 'np_arr'"

    s3_client = boto3.client(
        's3',
        aws_access_key_id = aws_access,
        aws_secret_access_key=aws_secret,
        region_name=aws_region
    )

    date_str = _naming_convention(forecast_publish_date) # "20230203T0600Z"

    paginator = s3_client.get_paginator('list_objects_v2')
    operation_parameters = {'Bucket': bucket_name,
                            'Prefix': prefix + date_str + "/"}
    page_iterator = paginator.paginate(**operation_parameters)
    _arr = []
    for page_no, page in enumerate(page_iterator):
        for content in page['Contents']:
                correct_file_bool = checkFileName(content, FILE_NAME_FORMAT) # Returns true if correct file
                if correct_file_bool:
                    if output == "print":
                        print(f'    {content["Key"]}, {content["Size"]/1024} KB')
                    elif output == "np_arr":
                        _arr.append(content["Key"])
    if output =="np_arr":
        return np.array(_arr)
        
                         


def checkFileName(content, FILE_NAME_FORMAT):
    """ Checks that the file in content is the same as FILE_NAME_FORMAT, returns bool"""
    return "-".join(content["Key"].split("/")[2].split("-")[2:]) == FILE_NAME_FORMAT


def get_hours_and_minutes(start_time, end_time):
    """
    Calculates the number of hours and minutes between two datetime objects.

    Returns:
        hours (int): Whole hours difference
        minutes (int): Remaining minutes after full hours
    """
    time_difference = end_time - start_time  # timedelta object
    total_minutes = time_difference.total_seconds() // 60  # Convert to minutes
    hours = total_minutes // 60  # Extract whole hours
    minutes = total_minutes % 60  # Get remaining minutes

    return int(hours), int(minutes)

def date_file_key_str(forecast_publish_date, date2):
    
    """
    Formats a given date and time (UTC) into the Met Office ASDI timestamp format.
    
    Example: format_met_office_timestamp(2023, 2, 1, 0, 0)
    Returns: "20230201T0000Z-PT0000H00M"
    """

    # TO DO: Sort forecast day logic.
    
    # first file = 20230201T0000Z (never includes hours/minutes)
    date_part = _naming_convention(forecast_publish_date)

    # Get hours and minutes diff
    forecast_hours, forecast_minutes = get_hours_and_minutes(forecast_publish_date, date2)

    # Ensure values are zero-padded, first part of file name: 20230201T1445Z (includes hours and minutes)
    date_part_hm = f"{date2.year:04}{date2.month:02}{date2.day:02}T{date2.hour:02}{date2.minute:02}Z"
    
    # Fixed duration part
    duration_part = f"PT{forecast_hours:04}H{forecast_minutes:02}M"
    
    return date_part + "/" + date_part_hm + "-" + duration_part



def download_file(aws_access, aws_secret, aws_region, bucket_name, FILE_KEY, FILE_NAME_FORMAT, DROP_FOLDER):
    
    """Download ASDI file to data/asdi."""

    s3_client = boto3.client(
        's3',
        aws_access_key_id = aws_access,
        aws_secret_access_key=aws_secret,
        region_name=aws_region
    )

    DROP_FILE = os.path.join(DROP_FOLDER,FILE_KEY.split("/")[2])


    # Download the file
    try:
        s3_client.download_file(bucket_name, FILE_KEY, DROP_FILE)
        print(f"File downloaded successfully to {DROP_FILE}")
    except Exception as e:
        print(f"Error downloading file: {e}")

    
def download_files(forecast_publish_date, AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX, FILE_NAME_FORMAT):

    """Downloads all forecast files from a specific date, with specified file name (e.g. rainfall_accumulation-PT01H.nc)"""

    # Get list of file names from this date, with correct file name
    np_arr = paginator(AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX, forecast_publish_date, FILE_NAME_FORMAT,output="np_arr")

    # Create folder in data/ to house output
    forecast_date_str = _naming_convention(forecast_publish_date)
    os.makedirs(f"data/asdi/{forecast_date_str}",exist_ok=True) # Errors if the file already exists in data/asdi

    # Loop through files in np_arr and dowload into new directory
    for FILE_KEY in np_arr:
        download_file(AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, FILE_KEY, FILE_NAME_FORMAT, f"data/asdi/{forecast_date_str}")



if __name__ == "__main__":
    
    """
    Compare these files: 
        1) uk-deterministic-2km/20230202T0000Z/20230203T0100Z-PT0025H00M-rainfall_accumulation-PT01H.nc, 519.1923828125 KB
        2) uk-deterministic-2km/20230203T0000Z/20230203T0100Z-PT0001H00M-rainfall_accumulation-PT01H.nc, 504.126953125 KB
    """
    
    forecast_publish_date = datetime(2024,2,3,6) # Initial folder dt

    download_files(forecast_publish_date, AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX, FILE_NAME_FORMAT)