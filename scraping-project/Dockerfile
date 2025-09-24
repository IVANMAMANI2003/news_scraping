FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY api/requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p data logs celery_tasks celery_workers

# Copiar archivos de configuración
COPY celery_app.py .
COPY celery_tasks/ ./celery_tasks/
COPY celery_workers/ ./celery_workers/
COPY config/ ./config/

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["python", "start_automatic_system.py"]
