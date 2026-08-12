#---- Stage 1 : builder ----
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

#---- STAGE 2 : runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app/ ./

RUN useradd --create-home appuser && chown -R appuser /app
USER  appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python - c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]
