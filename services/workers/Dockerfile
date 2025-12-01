FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY src /app/src
ENV PYTHONPATH=/app/src

CMD ["celery", "-A", "pivot.workers.celery_app:celery_app", "worker", "--loglevel=INFO", "-Q", "ingest,embed"]
