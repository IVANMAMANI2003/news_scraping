FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DOCKER_ENV=1

WORKDIR /app

# System deps
RUN apt-get update -y && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# Copy project
COPY . /app

EXPOSE 8000

# Default command runs the API; scheduler container overrides this
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]


