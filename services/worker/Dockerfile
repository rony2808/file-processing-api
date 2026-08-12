# ---- Stage 1 : builder ----"
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# ---- Stage 2 : runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTHECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

CMD ["python", "-m", "app.main"]
