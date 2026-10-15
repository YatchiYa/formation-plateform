# Image d'UN agent de agents/trio (un service Cloud Run par agent). Construite DANS Google Cloud (Cloud Build) :
# pas besoin de Docker sur votre poste. Depuis le dossier du projet :
#   gcloud builds submit --region=europe-west1 --config=01-bis-cloud-run-a2a/cloudbuild.yaml \
#     --substitutions=_AGENT_DIR=meteo_agent,_IMAGE=<image> .
# Le « contexte » est le dossier du projet (filtré par .gcloudignore : seul le code des agents est envoyé).
# Avec Docker (facultatif) : docker build -f 01-bis-cloud-run-a2a/Dockerfile --build-arg AGENT_DIR=meteo_agent -t <image> .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Dépendances d'abord : couche en cache tant que requirements.txt ne change pas.
COPY agents/trio/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Le code commun + UN agent (AGENT_DIR=meteo_agent). Par défaut (AGENT_DIR=.) : tous les agents.
# Une image par agent : ajouter ou modifier un autre agent ne change pas l'image de celui-ci.
ARG AGENT_DIR=.
COPY agents/trio/commun.py .
COPY agents/trio/${AGENT_DIR} ./${AGENT_DIR}
COPY 01-bis-cloud-run-a2a/main.py .

# Jamais root dans le conteneur.
RUN adduser --disabled-password --gecos "" app && chown -R app /app
USER app

# Cloud Run fournit $PORT (8080 par défaut).
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
