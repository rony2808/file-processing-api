#!/bin/bash
set -e

export AWS_DEFAULT_REGION=eu-central-1

echo "Creating local AWS resources..."

awslocal s3 mb s3://file-processing

awslocal dynamodb create-table \
  --table-name file-processing-jobs \
  --attribute-definitions AttributeName=job_id,AttributeType=S \
  --key-schema AttributeName=job_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

awslocal sqs create-queue --queue-name file-processing-dlq

awslocal sqs create-queue \
  --queue-name file-processing-queue \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:eu-central-1:000000000000:file-processing-dlq\",\"maxReceiveCount\":\"3\"}"
  }'

echo "Resources created."
