FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
# Journaux lisibles : sans les avertissements de dépréciation des bibliothèques Google (sans effet sur le code).
ENV PYTHONWARNINGS=ignore::UserWarning,ignore::FutureWarning,ignore::DeprecationWarning
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos "" app && chown -R app /app
USER app

# Service web par défaut ; le job de synchro remplace la commande par « python sync_job.py ».
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
