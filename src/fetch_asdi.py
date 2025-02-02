# Script to fetch ASDI data

from aiohttp import ClientError
import boto3
import botocore
import logging
from config import AWS_ACCESS, AWS_SECRET, AWS_REGION

BUCKET_NAME = "met-office-atmospheric-model-data"
PREFIX = "uk-deterministic-2km/"


def list_object_v2(aws_access, aws_secret, aws_region, bucket_name, prefix):
    
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
                print(f'    {content["Key"]}, {content["Size"]/1024} KB')
        else:
            print(f"No objects found in {prefix}")
    
    except ClientError as e:
        logging.error(e)
        return False
    
    return True

# https://boto3.amazonaws.com/v1/documentation/api/1.9.42/guide/s3-example-download-file.html
def download_file():
    
    s3 = boto3.resource('s3')

    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, )


if __name__ == "__main__":

    list_object_v2(AWS_ACCESS, AWS_SECRET, AWS_REGION, BUCKET_NAME, PREFIX)