import io
from unittest.mock import patch

from app.main import app


def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_create_job_no_file():
    client = app.test_client()
    response = client.post("/jobs")
    assert response.status_code == 400


def test_create_job_not_an_image():
    client = app.test_client()
    data = {"file": (io.BytesIO(b"pas une image"), "document.txt", "text/plain")}
    response = client.post("/jobs", data=data, content_type="multipart/form-data")
    assert response.status_code == 400


@patch("app.main.sqs")
@patch("app.main.dynamodb")
@patch("app.main.s3")
def test_create_job_with_image(mock_s3, mock_dynamodb, mock_sqs):
    mock_sqs.get_queue_url.return_value = {"QueueUrl": "http://fake-queue"}

    client = app.test_client()
    data = {"file": (io.BytesIO(b"fake image bytes"), "photo.jpg", "image/jpeg")}
    response = client.post("/jobs", data=data, content_type="multipart/form-data")

    assert response.status_code == 202
    assert "job_id" in response.get_json()

    mock_s3.put_object.assert_called_once()
    mock_dynamodb.put_item.assert_called_once()
    mock_sqs.send_message.assert_called_once()
