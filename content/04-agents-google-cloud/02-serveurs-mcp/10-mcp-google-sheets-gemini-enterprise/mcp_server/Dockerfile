# Image des serveurs MCP Google (construite par Cloud Build : gcloud builds submit mcp_server --config=cloudbuild.yaml). PRODUIT choisit les outils.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Tous les fichiers Python : main.py, noyau.py, outils_sheets.py, outils_slides.py (un oubli = conteneur qui ne démarre pas, vu en vrai)
COPY *.py ./
RUN adduser --disabled-password --gecos "" app
USER app
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
