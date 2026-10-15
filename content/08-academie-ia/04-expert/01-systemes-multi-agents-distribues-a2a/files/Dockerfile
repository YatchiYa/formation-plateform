# Une seule image pour les 3 agents : AGENT choisit le module lancé.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py registry.json ./
ENV AGENT=stock_agent
# Cloud Run fournit la variable PORT (8080 par défaut)
CMD exec uvicorn ${AGENT}:app --host 0.0.0.0 --port ${PORT:-8080}
