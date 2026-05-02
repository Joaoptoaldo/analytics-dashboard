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

# Copia o arquivo de dependências do backend para aproveitar cache de build
COPY backend/requirements.txt /app/backend/requirements.txt

# Instala as dependências reais do backend
RUN pip install -r backend/requirements.txt

# Copia o código
COPY . /app

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
