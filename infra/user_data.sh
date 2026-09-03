#!/bin/bash
set -e

dnf update -y
dnf install -y docker
systemctl start docker
systemctl enable docker

docker pull ${docker_username}/file-processing-api:latest
docker pull ${docker_username}/file-processing-worker:latest

docker run -d --restart always \
  --log-driver=awslogs \
  --log-opt awslogs-region=${aws_region} \
  --log-opt awslogs-group=/${project_name}/api \
  -p 8000:8000 \
  -e AWS_ENDPOINT_URL="" \
  -e AWS_REGION=${aws_region} \
  -e S3_BUCKET=${s3_bucket} \
  -e SQS_QUEUE_NAME=${sqs_queue_name} \
  -e DYNAMODB_TABLE=${dynamodb_table} \
  ${docker_username}/file-processing-api:latest

docker run -d --restart always \
  --log-driver=awslogs \
  --log-opt awslogs-region=${aws_region} \
  --log-opt awslogs-group=/${project_name}/worker \
  -e AWS_ENDPOINT_URL="" \
  -e AWS_REGION=${aws_region} \
  -e S3_BUCKET=${s3_bucket} \
  -e SQS_QUEUE_NAME=${sqs_queue_name} \
  -e DYNAMODB_TABLE=${dynamodb_table} \
  ${docker_username}/file-processing-worker:latest
