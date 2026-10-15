FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY agents/ agents/

# Never run as root in the container.
RUN adduser --disabled-password --gecos "" app && chown -R app /app
USER app

# Cloud Run injects $PORT (8080 by default).
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
