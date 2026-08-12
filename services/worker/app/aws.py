import boto3

from .config import settings


def _client(service_name):
    return boto3.client(
        service_name,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )


s3 = _client("s3")
sqs = _client("sqs")
dynamodb = _client("dynamodb")
