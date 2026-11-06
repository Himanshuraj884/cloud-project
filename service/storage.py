"""Download a model prefix (s3://bucket/prefix/) into a local directory."""
import os

import boto3
from botocore.config import Config


def download_model(model_uri, endpoint, dest):
    assert model_uri.startswith("s3://"), "MODEL_URI must look like s3://models/v1/"
    bucket, _, prefix = model_uri[5:].partition("/")
    prefix = prefix if prefix.endswith("/") or not prefix else prefix + "/"
    s3 = boto3.client(
        "s3", endpoint_url=endpoint, region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 5}),
    )  # credentials: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY, injected from a Kubernetes Secret
    os.makedirs(dest, exist_ok=True)
    n = 0
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            name = obj["Key"][len(prefix):]
            if not name or name.endswith("/") or name.endswith(".sha256"):
                continue
            target = os.path.join(dest, name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            s3.download_file(bucket, obj["Key"], target)
            n += 1
    if n == 0:
        raise RuntimeError(f"no model files under {model_uri}")
    return n
