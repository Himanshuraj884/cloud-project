"""Small S3 helpers. Endpoint from S3_ENDPOINT; credentials from the standard AWS_* variables
(supplied by a Kubernetes Secret, never stored in the repository)."""
import os

import boto3
from botocore.config import Config


def client(endpoint=None):
    return boto3.client(
        "s3",
        endpoint_url=endpoint or os.environ["S3_ENDPOINT"],
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 5}),
    )


def get_text(s3, bucket, key):
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")


def get_text_or_none(s3, bucket, key):
    try:
        return get_text(s3, bucket, key)
    except s3.exceptions.NoSuchKey:
        return None


def put_text(s3, bucket, key, text):
    s3.put_object(Bucket=bucket, Key=key, Body=text.encode("utf-8"))
