# Une seule image pour les deux agents : la variable MODULE choisit lequel démarre.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY stock_agent.py commandes_agent.py ./
ENV MODULE=stock_agent PYTHONUNBUFFERED=1
# Cloud Run fournit $PORT (8080 par défaut)
CMD exec uvicorn ${MODULE}:app --host 0.0.0.0 --port ${PORT:-8080}
