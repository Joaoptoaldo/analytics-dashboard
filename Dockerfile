FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema necessárias para numpy/pandas e psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    gfortran \
    libatlas-base-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Atualiza pip
RUN pip install --upgrade pip

# Copia arquivo de dependências (ajuda cache de build)
COPY backend/pyproject.toml /app/backend/pyproject.toml

# Instala dependências principais (ajuste conforme seu lockfile)
RUN pip install fastapi numpy pandas "uvicorn[standard]" requests SQLAlchemy psycopg2-binary

# Copia o código
COPY . /app

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
