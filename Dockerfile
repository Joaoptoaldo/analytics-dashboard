FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /app

# Copia apenas requirements para vantagem de cache
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt

# Copia apenas o código do backend (evita transferir arquivos sensíveis/monorepo extras)
COPY backend /app/backend

# Cria um usuário não-root para rodar a aplicação
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV PORT=8080
ENV WEB_CONCURRENCY=2
ENV GUNICORN_TIMEOUT=60
ENV GUNICORN_GRACEFUL_TIMEOUT=30
ENV GUNICORN_KEEPALIVE=5
EXPOSE 8080

# Use gunicorn com workers uvicorn para produção
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT:-8080} backend.main:app --log-level info --access-logfile - --error-logfile - --capture-output --timeout ${GUNICORN_TIMEOUT:-60} --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-30} --keep-alive ${GUNICORN_KEEPALIVE:-5}"]

# Healthcheck para o container (ajustar caminho se necessário)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:${PORT:-8080}/readiness || exit 1
