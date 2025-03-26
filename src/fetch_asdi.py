# Script to fetch ASDI data

import boto3
import argparse
from datetime import datetime
import os
import sys
import numpy as np
import pandas as pd
from config import AWS_ACCESS, AWS_SECRET, AWS_REGION
import logging

# Set up logging configuration
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)


def _naming_convention(dt):
    """Use this naming convention throughout"""
    if dt.minute != 0:
        logger.error("Forecast date %s is not on the hour.", dt)
    assert dt.minute == 0, "Error: Can go through forecasts that were published on the hour"
    naming = f"{dt.year:04}{dt.month:02}{dt.day:02}T{dt.hour:02}00Z"
    logger.debug("Naming convention for %s: %s", dt, naming)
    return naming


def paginator(aws_access, aws_secret, aws_region, bucket_name, prefix, forecast_publish_date, FILE_NAME_FORMAT, output="print"):
    """ 
    Create paginator to read multiple bucket pages (which are limited to 1000).
    More details on Pagination here: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html
    """
    assert output == "print" or output == "np_arr", "output variable must be set to 'print' or 'np_arr'"
    logger.info("Starting paginator for forecast date: %s", forecast_publish_date)
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access,
        aws_secret_access_key=aws_secret,
        region_name=aws_region
    )

    date_str = _naming_convention(forecast_publish_date)  # e.g. "20230203T0600Z"
    logger.debug("Using date string: %s", date_str)

    paginator_obj = s3_client.get_paginator('list_objects_v2')
    operation_parameters = {'Bucket': bucket_name,
                            'Prefix': prefix + date_str + "/"}
    logger.debug("Operation parameters: %s", operation_parameters)
    page_iterator = paginator_obj.paginate(**operation_parameters)
    _arr = []
    for page_no, page in enumerate(page_iterator):
        logger.debug("Processing page %d", page_no)
        for content in page.get('Contents', []):
            correct_file_bool = checkFileName(content, FILE_NAME_FORMAT)
            if correct_file_bool:
                logger.debug("Found matching file: %s", content["Key"])
                if output == "print":
                    print(f'    {content["Key"]}, {content["Size"]/1024:.2f} KB')
                elif output == "np_arr":
                    _arr.append(content["Key"])
    if output == "np_arr":
        logger.info("Paginator found %d matching files", len(_arr))
        return np.array(_arr)


def checkFileName(content, FILE_NAME_FORMAT):
    """Checks that the file in content is the same as FILE_NAME_FORMAT, returns bool"""
    file_part = "-".join(content["Key"].split("/")[2].split("-")[2:])
    result = file_part == FILE_NAME_FORMAT
    logger.debug("File %s matches FILE_NAME_FORMAT: %s", content["Key"], result)
    return result


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
    logger.debug("Time difference between %s and %s: %d hours, %d minutes", start_time, end_time, hours, minutes)
    return int(hours), int(minutes)


def date_file_key_str(forecast_publish_date, date2):
    """
    Formats a given date and time (UTC) into the Met Office ASDI timestamp format.
    
    Example: format_met_office_timestamp(2023, 2, 1, 0, 0)
    Returns: "20230201T0000Z-PT0000H00M"
    """
    date_part = _naming_convention(forecast_publish_date)
    forecast_hours, forecast_minutes = get_hours_and_minutes(forecast_publish_date, date2)
    date_part_hm = f"{date2.year:04}{date2.month:02}{date2.day:02}T{date2.hour:02}{date2.minute:02}Z"
    duration_part = f"PT{forecast_hours:04}H{forecast_minutes:02}M"
    file_key = date_part + "/" + date_part_hm + "-" + duration_part
    logger.debug("Generated file key: %s", file_key)
    return file_key


def download_file(aws_access, aws_secret, aws_region, bucket_name, FILE_KEY, FILE_NAME_FORMAT, DROP_FOLDER):
    """Download ASDI file to data/asdi."""
    logger.info("Starting download for file: %s", FILE_KEY)
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access,
        aws_secret_access_key=aws_secret,
        region_name=aws_region
    )

    DROP_FILE = os.path.join(DROP_FOLDER, FILE_KEY.split("/")[2])
    logger.debug("Local drop file path: %s", DROP_FILE)

    try:
        s3_client.download_file(bucket_name, FILE_KEY, DROP_FILE)
        logger.info("File downloaded successfully to %s", DROP_FILE)
    except Exception as e:
        logger.error("Error downloading file %s: %s", FILE_KEY, e)


def download_files(forecast_publish_date, AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX, FILE_NAME_FORMAT):
    """Downloads all forecast files from a specific date, with specified file name (e.g. rainfall_accumulation-PT01H.nc)"""
    logger.info("Downloading files for forecast publish date: %s", forecast_publish_date)
    
    # Get list of file names from this date, with correct file name
    np_arr = paginator(AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX, forecast_publish_date, FILE_NAME_FORMAT, output="np_arr")
    forecast_date_str = _naming_convention(forecast_publish_date)
    drop_directory = f"data/asdi/{forecast_date_str}"
    
    try:
        os.makedirs(drop_directory, exist_ok=False)  # Errors if the folder already exists
        logger.info("Created directory: %s", drop_directory)
    except Exception as e:
        logger.error("Failed to create directory %s: %s", drop_directory, e)
        sys.exit(1)

    # Loop through files in np_arr and download into the new directory
    for FILE_KEY in np_arr:
        # Extract day from the file key to determine if it's within the same forecast day
        day = FILE_KEY.split("/")[2].split("-")[0][9:11]
        logger.debug("Processing FILE_KEY: %s, extracted day: %s", FILE_KEY, day)
        # If it starts reading the forecast past midnight on the following day, stop processing.
        if int(day) == 0:
            logger.info("Encountered file with day 0; stopping further downloads for this date.")
            break
        download_file(AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, FILE_KEY, FILE_NAME_FORMAT, drop_directory)


def download_files_for_date_range(forecast_publish_start_date, forecast_publish_end_date, AWS_ACCESS, AWS_SECRET, AWS_REGION, 
                                  BUCKET_NAME, PREFIX, FILE_NAME_FORMAT):
    """Loops over the download_files function above to create a library of forecasts at a given time each day (typically 9am UTC)"""
    logger.info("Starting download for date range: %s to %s", forecast_publish_start_date, forecast_publish_end_date)
    date_range = pd.date_range(start=forecast_publish_start_date, end=forecast_publish_end_date)
    logger.debug("Date range contains %d dates.", len(date_range))
    for DATE in date_range:
        logger.info("Processing forecast date: %s", DATE)
        download_files(DATE, AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX, FILE_NAME_FORMAT)


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="UTC time for ASDI file download start & end datetimes.")
    parser.add_argument("--sd", required=True, help="The forecast publish date in 'YYYY-MM-DD HH:MM:SS' format")
    parser.add_argument("--ed", required=True, help="The forecast publish date in 'YYYY-MM-DD HH:MM:SS' format")
    args = parser.parse_args()

    # Parse the start date argument
    try:
        FORECAST_START_DATE = datetime.strptime(args.sd, "%Y-%m-%d %H:%M:%S")
        logger.info("Parsed start date: %s", FORECAST_START_DATE)
    except ValueError:
        logger.error("Incorrect start date format. Please use 'YYYY-MM-DD HH:MM:SS'")
        sys.exit(1)

    # Parse the end date argument
    try:
        FORECAST_END_DATE = datetime.strptime(args.ed, "%Y-%m-%d %H:%M:%S")
        logger.info("Parsed end date: %s", FORECAST_END_DATE)
    except ValueError:
        logger.error("Incorrect end date format. Please use 'YYYY-MM-DD HH:MM:SS'")
        sys.exit(1)

    BUCKET_NAME = "met-office-atmospheric-model-data"
    PREFIX = "uk-deterministic-2km/"
    FILE_NAME_FORMAT = "rainfall_accumulation-PT01H.nc"
    
    logger.info("Initiating download_files_for_date_range.")
    download_files_for_date_range(FORECAST_START_DATE, FORECAST_END_DATE, AWS_ACCESS, AWS_SECRET, AWS_REGION, 
                                  BUCKET_NAME, PREFIX, FILE_NAME_FORMAT)
