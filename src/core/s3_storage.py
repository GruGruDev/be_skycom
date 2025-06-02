import boto3
from botocore.client import Config

from core import settings


def init_s3_client():
    s3_config = Config(
        s3={"addressing_style": "path"},
        signature_version="s3v4",
    )

    # Khởi tạo S3 client
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=s3_config,
    )

    return s3_client
