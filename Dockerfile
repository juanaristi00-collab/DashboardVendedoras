FROM python:3.12-slim

# Metadata para David
LABEL maintainer="Saanye CRM" \
      description="Backend API — Saanye Sales Bar" \
      version="0.3.0"

# Evitar que Python genere archivos .pyc y buffering en logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para aiomysql
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python (cacheado en capas separadas)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar solo el backend (el frontend vive en Vercel)
COPY backend /app/backend

# Establecer el directorio de trabajo donde uvicorn encontrará app.main:app
WORKDIR /app/backend

# Puerto expuesto
EXPOSE 8000

# Producción: 4 workers uvicorn, sin reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info"]
