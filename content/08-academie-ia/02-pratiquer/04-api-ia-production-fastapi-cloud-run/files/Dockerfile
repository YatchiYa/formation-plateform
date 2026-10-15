FROM python:3.12-slim

# Pas de fichiers .pyc, journaux envoyés tout de suite sur stdout
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Dépendances d'abord : cette couche reste en cache tant que requirements.txt ne change pas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Utilisateur sans privilèges
RUN useradd --create-home appuser
USER appuser

# Cloud Run fournit le port dans $PORT (8080 par défaut).
# --no-access-log : le middleware de main.py écrit déjà une ligne JSON par requête
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --no-access-log
