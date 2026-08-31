import io
import json
import logging

from PIL import Image

from .aws import dynamodb, s3, sqs
from .config import settings

from prometheus_client import Counter, start_http_server

jobs_processed = Counter("jobs_processed_total", "Total images processed successfully")
jobs_failed = Counter("jobs_failed_total", "Total images that failed processing")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("worker")


def poll_once(queue_url):
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20,
    )
    messages = response.get("Messages", [])

    if not messages:
        logger.info("No messages, waiting...")
        return

    for message in messages:
        logger.info("Received message: %s", message["Body"])
        # Phase 2 : traitement de l'image ici
        body = json.loads(message["Body"])
        job_id = body["job_id"]
        existing = dynamodb.get_item(
            TableName=settings.dynamodb_table,
            Key={"job_id": {"S": job_id}},
        )
        status = existing["Item"]["status"]["S"]
        if status == "done":
            logger.info("Job %s already done, skipping", job_id)
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message["ReceiptHandle"],
            )
            continue
        try:
            dynamodb.update_item(
                TableName=settings.dynamodb_table,
                Key={"job_id": {"S": job_id}},
                UpdateExpression="SET #s = :status",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":status": {"S": "processing"}},
            )
            response = dynamodb.get_item(
                TableName=settings.dynamodb_table,
                Key={"job_id": {"S": job_id}},
            )
            item = response["Item"]
            source_key = item["source_key"]["S"]
            s3_response = s3.get_object(Bucket=settings.s3_bucket, Key=source_key)
            image_bytes = s3_response["Body"].read()
            image = Image.open(io.BytesIO(image_bytes))
            image.thumbnail((256, 256))
            output = io.BytesIO()
            image.save(output, format="JPEG")
            thumbnail_bytes = output.getvalue()
            logger.info("Thumbnail generated: %d bytes", len(thumbnail_bytes))
            thumbnail_key = f"thumbnails/{job_id}.jpg"
            s3.put_object(
                Bucket=settings.s3_bucket, Key=thumbnail_key, Body=thumbnail_bytes
            )
            dynamodb.update_item(
                TableName=settings.dynamodb_table,
                Key={"job_id": {"S": job_id}},
                UpdateExpression="SET #s = :status, thumbnail_key = :tk",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":status": {"S": "done"},
                    ":tk": {"S": thumbnail_key},
                },
            )
            logger.info("Job %s done", job_id)
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message["ReceiptHandle"],
            )
            logger.info("Message deleted")
            jobs_processed.inc()
        except Exception as error:  # noqa: BLE001
            logger.error("Job %s failed: %s", job_id, error)
            dynamodb.update_item(
                TableName=settings.dynamodb_table,
                Key={"job_id": {"S": job_id}},
                UpdateExpression="SET #s = :status, #e = :error",
                ExpressionAttributeNames={"#s": "status", "#e": "error"},
                ExpressionAttributeValues={
                    ":status": {"S": "failed"},
                    ":error": {"S": str(error)},
                },
            )
            jobs_failed.inc()


def main():
    logger.info("Worker started, polling queue...")
    queue_url = sqs.get_queue_url(QueueName=settings.sqs_queue_name)["QueueUrl"]
    logger.info("Resolved queue URL: %s", queue_url)
    start_http_server(8001)
    while True:
        poll_once(queue_url)


if __name__ == "__main__":
    main()
