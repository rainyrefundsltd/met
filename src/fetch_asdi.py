# Script to fetch ASDI data

from aiohttp import ClientError
import boto3
from datetime import datetime
import logging
from config import AWS_ACCESS, AWS_SECRET, AWS_REGION

BUCKET_NAME = "met-office-atmospheric-model-data"
PREFIX = "uk-deterministic-2km/"
FILE_NAME_FORMAT = "rainfall_accumulation-PT01H.nc" # precipitation_rate.nc


def paginator(aws_access, aws_secret, aws_region, bucket_name, prefix, FILE_NAME_FORMAT):
    
    """ 
    Create paginator to read multiple bucket pages (which are limited to 1000)
    More details on Pagination here: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html
    """
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id = aws_access,
        aws_secret_access_key=aws_secret,
        region_name=aws_region
    )

    paginator = s3_client.get_paginator('list_objects_v2')
    operation_parameters = {'Bucket': bucket_name,
                            'Prefix': prefix + "20230203T0000Z/"}
    page_iterator = paginator.paginate(**operation_parameters)
    for page_no, page in enumerate(page_iterator):
        print(f"PAGE NO: {page_no + 1}")
        for content in page['Contents']:
                correct_file_bool = checkFileName(content, FILE_NAME_FORMAT) # Returns true if correct file
                if correct_file_bool:
                    print(f'    {content["Key"]}, {content["Size"]/1024} KB')


def checkFileName(content, FILE_NAME_FORMAT):
    """ Checks that the file in content is the same as FILE_NAME_FORMAT, returns bool"""
    return "-".join(content["Key"].split("/")[2].split("-")[2:]) == FILE_NAME_FORMAT


def list_object_v2(aws_access, aws_secret, aws_region, bucket_name, prefix, FILE_NAME_FORMAT):
    
    """List objects in a specified AWS bucket, with a specified prefix"""
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id = aws_access,
        aws_secret_access_key=aws_secret,
        region_name=aws_region
    )

    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" in response:
            for content in response['Contents']:
                correct_file_bool = checkFileName(content, FILE_NAME_FORMAT) # Returns true if correct file
                if correct_file_bool:
                    print(f'    {content["Key"]}, {content["Size"]/1024} KB')
        else:
            print(f"No {FILE_NAME_FORMAT} objects found in {prefix}")
    
    except ClientError as e:
        logging.error(e)
        return False
    
    return True

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

def date_file_key_str(date1, date2):
    
    """
    Formats a given date and time (UTC) into the Met Office ASDI timestamp format.
    
    Example: format_met_office_timestamp(2023, 2, 1, 0, 0)
    Returns: "20230201T0000Z-PT0000H00M"
    """

    # TO DO: Sort forecast day logic.
    
    # first file = 20230201T0000Z (never includes hours/minutes)
    date_part = f"{date1.year:04}{date1.month:02}{date1.day:02}T0000Z"

    # Get hours and minutes diff
    forecast_hours, forecast_minutes = get_hours_and_minutes(date1, date2)

    # Ensure values are zero-padded, first part of file name: 20230201T1445Z (includes hours and minutes)
    date_part_hm = f"{date2.year:04}{date2.month:02}{date2.day:02}T{date2.hour:02}{date2.minute:02}Z"
    
    # Fixed duration part
    duration_part = f"PT{forecast_hours:04}H{forecast_minutes:02}M"
    
    return date_part + "/" + date_part_hm + "-" + duration_part



def download_file(aws_access, aws_secret, aws_region, bucket_name, date1, date2, FILE_NAME_FORMAT):
    
    """Download ASDI file to data/asdi."""

    s3_client = boto3.client(
        's3',
        aws_access_key_id = aws_access,
        aws_secret_access_key=aws_secret,
        region_name=aws_region
    )

    DATE_STR = date_file_key_str(date1, date2)
    KEY = "uk-deterministic-2km/" + DATE_STR  + "-" + FILE_NAME_FORMAT
    DROP_FILE = "data/asdi/" + DATE_STR.replace("/","-")  + "-" + FILE_NAME_FORMAT


    # Download the file
    try:
        s3_client.download_file(bucket_name, KEY, DROP_FILE)
        print(f"File downloaded successfully to {DROP_FILE}")
    except Exception as e:
        print(f"Error downloading file: {e}")

    
def download_files():

    """Downloads all files within specified dates, with specified file name (e.g. rainfall_accumulation-PT01H.nc)"""

    pass



if __name__ == "__main__":
    
    """
    Compare these files: 
        1) uk-deterministic-2km/20230202T0000Z/20230203T0100Z-PT0025H00M-rainfall_accumulation-PT01H.nc, 519.1923828125 KB
        2) uk-deterministic-2km/20230203T0000Z/20230203T0100Z-PT0001H00M-rainfall_accumulation-PT01H.nc, 504.126953125 KB
    """
    
    date1 = datetime(2024,2,3,0) # Initial folder dt
    date2 = datetime(2024,2,3,1) # Forecast end or something??

    download_file(AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, date1, date2, FILE_NAME_FORMAT)
    # list_object_v2(AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX, FILE_NAME_FORMAT)
    # paginator(AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX, FILE_NAME_FORMAT)