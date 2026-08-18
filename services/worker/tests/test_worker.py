import io
from unittest.mock import patch

from app.main import poll_once
from PIL import Image


def make_real_image_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (800, 600), "blue").save(buffer, format="JPEG")
    return buffer.getvalue()


@patch("app.main.sqs")
@patch("app.main.dynamodb")
@patch("app.main.s3")
def test_poll_once_success(mock_s3, mock_dynamodb, mock_sqs):
    mock_sqs.receive_message.return_value = {
        "Messages": [{"Body": '{"job_id": "abc123"}', "ReceiptHandle": "fake-handle"}]
    }
    mock_dynamodb.get_item.return_value = {
        "Item": {
            "status": {"S": "pending"},
            "source_key": {"S": "uploads/abc123.jpg"},
        }
    }
    mock_s3.get_object.return_value = {"Body": io.BytesIO(make_real_image_bytes())}

    poll_once("http://fake-queue")

    mock_s3.put_object.assert_called_once()
    mock_sqs.delete_message.assert_called_once()


@patch("app.main.sqs")
@patch("app.main.dynamodb")
@patch("app.main.s3")
def test_poll_once_idempotence(mock_s3, mock_dynamodb, mock_sqs):
    mock_sqs.receive_message.return_value = {
        "Messages": [{"Body": '{"job_id": "abc123"}', "ReceiptHandle": "fake-handle"}]
    }
    mock_dynamodb.get_item.return_value = {
        "Item": {
            "status": {"S": "done"},
            "source_key": {"S": "uploads/abc123.jpg"},
        }
    }

    poll_once("http://fake-queue")

    mock_s3.put_object.assert_not_called()
    mock_sqs.delete_message.assert_called_once()


@patch("app.main.sqs")
@patch("app.main.dynamodb")
@patch("app.main.s3")
def test_poll_once_failed(mock_s3, mock_dynamodb, mock_sqs):
    mock_sqs.receive_message.return_value = {
        "Messages": [{"Body": '{"job_id": "abc123"}', "ReceiptHandle": "fake-handle"}]
    }
    mock_dynamodb.get_item.return_value = {
        "Item": {
            "status": {"S": "pending"},
            "source_key": {"S": "uploads/abc123.jpg"},
        }
    }
    mock_s3.get_object.return_value = {"Body": io.BytesIO(b"not an image")}

    poll_once("http://fake-queue")

    mock_sqs.delete_message.assert_not_called()
