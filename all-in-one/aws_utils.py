import logging
import boto3
from botocore.exceptions import ClientError

"""
Upload a file to an S3 bucket. Source taken directly from:
https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html

:param file_name: File to upload
:param bucket: Bucket to upload to
:param object_name: S3 object name. If not specified then file_name is used
:return: True if file was uploaded, else False
"""
def upload_file(file_name, bucket, object_name=None):
    

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True