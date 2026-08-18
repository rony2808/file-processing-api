import os


class Settings:
    aws_endpoint_url = os.getenv("AWS_ENDPOINT_URL") or None
    aws_region = os.getenv("AWS_REGION", "eu-central-1")
    s3_bucket = os.getenv("S3_BUCKET", "file-processing")
    sqs_queue_name = os.getenv("SQS_QUEUE_NAME", "file-processing-queue")
    dynamodb_table = os.getenv("DYNAMODB_TABLE", "file-processing-jobs")


settings = Settings()
