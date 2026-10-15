FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Cloud Run fournit le port dans la variable PORT (8080 par défaut).
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
