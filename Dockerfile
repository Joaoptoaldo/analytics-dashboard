FROM python:3.13-slim

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

# Copia migração do Alembic - essencial para bootstrap.py executar alembic upgrade head
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

# Cria um usuário não-root para rodar a aplicação
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV PORT=8080
ENV WEB_CONCURRENCY=2
ENV GUNICORN_TIMEOUT=60
ENV GUNICORN_GRACEFUL_TIMEOUT=30
ENV GUNICORN_KEEPALIVE=5
EXPOSE 8080

# Bootstrap obrigatório: valida env, executa migrations e só então sobe a API
CMD ["python", "-m", "backend.bootstrap"]

# Healthcheck para o container (ajustar caminho se necessário)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:${PORT:-8080}/readiness || exit 1
