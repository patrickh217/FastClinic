FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# No database and no volume: MedBackend is the system of record, so the container
# is stateless and holds nothing that needs persisting between restarts.
EXPOSE 5005

# /health is liveness only. /health/ready is the deploy gate - it 503s while any
# required setting is missing or still a placeholder, so a half-configured deploy
# fails visibly instead of serving a broken app.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl --fail http://localhost:5005/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5005"]
