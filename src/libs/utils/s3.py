import os

import boto3
from botocore.exceptions import ClientError

from libs.utils.env import AWS_DEFAULT_REGION
from libs.utils.log import get_logger

log = get_logger(logs_to_file=True, logs_to_console=True)

s3_client = boto3.client("s3", region_name=AWS_DEFAULT_REGION)


def file_exists_in_s3(bucket: str, key: str) -> bool:
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise


def download_file_from_s3(bucket: str, key: str, local_path: str) -> None:
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3_client.download_file(bucket, key, local_path)
    log.info(f"File {key} downloaded from S3 to {local_path}")


def upload_file_to_s3(bucket: str, key: str, local_path: str) -> None:
    s3_client.upload_file(local_path, bucket, key)
    log.info(f"File uploaded to S3 at bucket: {bucket} file: {key}")
