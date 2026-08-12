from flask import Flask, request
from config import settings
from aws import s3, dynamodb, sqs
import json
import uuid

app = Flask(__name__)


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.post("/jobs")
def create_job():
    file = request.files.get("file")
    if file is None:
        return {"error": "no file provided"}, 400
    if not file.content_type.startswith("image/"):
        return {"error": "file must be an image"}, 400
    job_id = str(uuid.uuid4())
    key = f"uploads/{job_id}.jpg"
    s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=file.read())
    dynamodb.put_item(
        TableName=settings.dynamodb_table,
        Item={
            "job_id": {"S": job_id},
            "status": {"S": "pending"},
            "source_key": {"S": key},
        },
    )
    queue_url = sqs.get_queue_url(QueueName=settings.sqs_queue_name)["QueueUrl"]
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({"job_id": job_id}),
    )
    return {"job_id": job_id}, 202


@app.get("/jobs/<job_id>")
def get_job(job_id):
    response = dynamodb.get_item(
        TableName=settings.dynamodb_table,
        Key={"job_id": {"S": job_id}},
    )
    item = response.get("Item")
    if not item:
        return {"error": "job not found"}, 404
    return item, 200
