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

"""
Uploads a record to the specified DDB table. Record must obviously
adhere to the expected schema or it will be impossible to query.

By default we declare the attribute_not_exists(TransactionID) ConditionExpression to prevent
overwriting existing records.
"""
def upload_record_to_ddb_table(tableName, record):
    ddb_client = boto3.client('dynamodb')
    try:
        response = ddb_client.put_item(TableName=tableName, Item=record, ConditionExpression='attribute_not_exists(TransactionID)')
    except ClientError as e:
        # Disregard the errors thrown from the ConditionExpression check
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            logging.error(e)
            return False
    return True

"""
TODO: Delete this after testing
"""
def query_ddb_example():
    ddb_client = boto3.client('dynamodb')
    try:
        response = ddb_client.put_item(TableName=tableName, Item=record)
        # response = ddb_client.put_item(TableName=tableName, Item=record, ConditionExpression='attribute_not_exists(TransactionID)')
    except ClientError as e:
        # Disregard the errors thrown from the ConditionExpression check
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            logging.error(e)
            return False
    return True
