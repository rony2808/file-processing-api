# File Processing API

![CI](https://github.com/rony2808/file-processing-api/actions/workflows/ci.yml/badge.svg)

An asynchronous, event-driven image processing pipeline built with Python, containerized with Docker, deployed to AWS with Terraform, and instrumented with a full CI/CD and observability stack.

Users upload an image through a REST API; the image is processed asynchronously by a decoupled worker that generates a thumbnail. The two services communicate through a message queue, making the system resilient, scalable, and observable.

---

## Architecture

The system is composed of two decoupled services communicating through AWS-managed services (S3, SQS, DynamoDB):

```
                 ┌─────────────┐
   POST /jobs    │             │   1. Store image        ┌──────────┐
  ──────────────>│     API     │────────────────────────>│    S3    │
   (image file)  │   (Flask)   │   2. Create job (pending)│ uploads/ │
                 │             │────────┐                 └──────────┘
                 └─────────────┘        │                 ┌──────────┐
                        │               └────────────────>│ DynamoDB │
                        │ 3. Send message                  │   jobs   │
                        v                                  └──────────┘
                 ┌─────────────┐                                ^
                 │     SQS     │                                │
                 │    queue    │                                │
                 └─────────────┘                                │
                        │                                       │
                        │ 4. Poll message                       │
                        v                                       │
                 ┌─────────────┐   5. Download image      ┌──────────┐
                 │   Worker    │<─────────────────────────│    S3    │
                 │  (polling)  │   6. Upload thumbnail     │thumbnails│
                 │             │─────────────────────────>│    /     │
                 └─────────────┘   7. Update job (done)    └──────────┘
                        │                                       ^
                        └───────────────────────────────────────┘
```

**Flow:**
1. The client sends an image to `POST /jobs`.
2. The API stores the original in S3, creates a `pending` job record in DynamoDB, and pushes a message to SQS. It immediately returns `202 Accepted` with a `job_id`.
3. The worker polls SQS, downloads the original from S3, generates a 256×256 thumbnail, uploads it back to S3, and updates the job status to `done` in DynamoDB.
4. The client can check progress at any time via `GET /jobs/{job_id}`.

---

## Tech Stack

| Category            | Technologies                                              |
|---------------------|-----------------------------------------------------------|
| Language & Web      | Python, Flask, Gunicorn                                   |
| AWS Services        | S3, SQS (with Dead Letter Queue), DynamoDB                |
| AWS SDK             | boto3                                                      |
| Image processing    | Pillow                                                     |
| Containerization    | Docker, Docker Compose                                     |
| Infrastructure      | Terraform (Infrastructure as Code), AWS EC2, VPC, IAM     |
| CI/CD               | GitHub Actions                                             |
| Observability       | Prometheus, Grafana                                        |
| Local development   | LocalStack (local AWS emulation)                           |

---

## Key Features

- **Asynchronous & event-driven** — the API responds instantly; heavy processing happens in the background, decoupled through a message queue.
- **Resilient error handling** — failed jobs are retried and routed to a **Dead Letter Queue** after repeated failures, so no message is silently lost.
- **Idempotent processing** — already-completed jobs are safely skipped if a message is redelivered.
- **Input validation** — the API rejects missing files and non-image uploads.
- **Automated testing** — unit tests for both services using mocking, so tests run anywhere without real AWS dependencies.
- **Full CI/CD pipeline** — every push runs tests and linting for both services in parallel; Docker images are built and published only when all checks pass.
- **Infrastructure as Code** — the entire AWS environment (network, IAM, compute, data stores) is provisioned reproducibly with Terraform, following least-privilege IAM principles.
- **Observability** — business and HTTP metrics exposed via Prometheus and visualized in Grafana dashboards.

---

## Project Structure

```
file-processing-api/
├── services/
│   ├── api/                 # Flask API service
│   │   ├── app/             # Application code (main, config, aws)
│   │   ├── tests/           # Unit tests (mocked)
│   │   └── Dockerfile
│   └── worker/              # Background worker service
│       ├── app/             # Application code (main, config, aws)
│       ├── tests/           # Unit tests (mocked)
│       └── Dockerfile
├── infra/                   # Terraform infrastructure (AWS)
├── .github/workflows/       # CI/CD pipelines (GitHub Actions)
├── localstack/init/         # LocalStack resource bootstrap
├── prometheus.yml           # Prometheus scrape configuration
├── docker-compose.yml       # Local development stack
└── README.md
```

---

## Running Locally

The full stack runs locally against **LocalStack** (a local AWS emulator), so no AWS account or costs are required.

**Prerequisites:** Docker and Docker Compose.

```bash
# Start the full stack (API, worker, LocalStack, Prometheus, Grafana)
docker compose up -d --build
```

Once running:

```bash
# Submit an image for processing
curl -X POST -F "file=@your-image.jpg" http://localhost:8000/jobs
# -> {"job_id": "..."}

# Check the job status
curl http://localhost:8000/jobs/<job_id>
# -> {"status": "done", "thumbnail_key": "thumbnails/<job_id>.jpg", ...}
```

**Service endpoints:**

| Service            | URL                          |
|--------------------|------------------------------|
| API                | http://localhost:8000        |
| Worker metrics     | http://localhost:8001/metrics|
| Prometheus         | http://localhost:9090        |
| Grafana            | http://localhost:3000        |

---

## Testing

Each service has its own mocked unit-test suite. Tests use mocking to replace AWS
services, so they run fast and require no external dependencies.

```bash
# API tests
cd services/api && python -m pytest

# Worker tests
cd services/worker && python -m pytest
```

---

## CI/CD

Every push triggers a GitHub Actions pipeline that:

1. Runs the API and worker test suites in parallel (via a reusable workflow).
2. Checks formatting (`black`) and linting (`ruff`).
3. Builds and publishes both Docker images to Docker Hub — **only if all tests and checks pass** (enforced with job dependencies).

Published images:
- [`ronk1234/file-processing-api`](https://hub.docker.com/r/ronk1234/file-processing-api)
- [`ronk1234/file-processing-worker`](https://hub.docker.com/r/ronk1234/file-processing-worker)

---

## Deploying to AWS

The `infra/` directory contains the full Terraform configuration to deploy the
application to AWS. It provisions:

- **Networking** — VPC, public subnet, internet gateway, route table, security group.
- **Data stores** — S3 bucket, SQS queue + Dead Letter Queue, DynamoDB table.
- **Compute** — an EC2 instance that pulls the Docker images and runs both services, configured automatically at boot via a user-data script.
- **Security** — a least-privilege IAM role granting the instance only the exact permissions it needs, with no static credentials.

```bash
cd infra
terraform init
terraform plan  -var="my_ip=$(curl -s ifconfig.me)"
terraform apply -var="my_ip=$(curl -s ifconfig.me)"

# ... when finished, tear everything down to avoid costs:
terraform destroy -var="my_ip=$(curl -s ifconfig.me)"
```

Terraform state is stored remotely in S3 with state locking enabled.

---

## Observability

Both services are instrumented for metrics:

- **API** — HTTP request metrics (rate, latency, status codes) via `prometheus-flask-exporter`.
- **Worker** — custom business metrics (`jobs_processed_total`, `jobs_failed_total`) via `prometheus_client`, exposed on a dedicated metrics endpoint.

Prometheus scrapes both services, and Grafana visualizes the data — processing
throughput, failure rate, API traffic, and p95 latency.

---

## Author

Built by Rony — [github.com/rony2808](https://github.com/rony2808)
