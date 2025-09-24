#!/usr/bin/env python3
"""
Script de configuración para AWS
Configura el sistema completo en una instancia EC2
"""

import os
import subprocess
import sys
import time
import psycopg2
from datetime import datetime

def install_dependencies():
    """Instalar dependencias del sistema"""
    print("📦 Instalando dependencias del sistema...")
    
    commands = [
        "sudo apt-get update",
        "sudo apt-get install -y python3-pip python3-venv postgresql postgresql-contrib redis-server",
        "sudo systemctl start postgresql",
        "sudo systemctl enable postgresql",
        "sudo systemctl start redis-server",
        "sudo systemctl enable redis-server"
    ]
    
    for cmd in commands:
        print(f"🔧 Ejecutando: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ {cmd} - Completado")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error en {cmd}: {e}")
            return False
    
    return True

def setup_postgresql():
    """Configurar PostgreSQL"""
    print("🐘 Configurando PostgreSQL...")
    
    try:
        # Crear usuario y base de datos
        commands = [
            "sudo -u postgres psql -c \"ALTER USER postgres PASSWORD '123456';\"",
            "sudo -u postgres psql -c \"CREATE DATABASE noticias;\"",
            "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE noticias TO postgres;\""
        ]
        
        for cmd in commands:
            print(f"🔧 Ejecutando: {cmd}")
            subprocess.run(cmd, shell=True, check=True)
            print(f"✅ Completado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando PostgreSQL: {e}")
        return False

def create_aws_docker_compose():
    """Crear docker-compose para AWS"""
    print("🐳 Creando configuración Docker para AWS...")
    
    docker_compose_content = """version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: aws_postgres
    environment:
      POSTGRES_DB: noticias
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 123456
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: aws_redis
    ports:
      - "6379:6379"
    restart: unless-stopped

  news_system:
    build: .
    container_name: aws_news_system
    depends_on:
      - postgres
      - redis
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=123456
      - POSTGRES_DB=noticias
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - AWS_ENV=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    command: python start_aws_system.py

volumes:
  postgres_data:
"""
    
    with open('docker-compose-aws.yml', 'w') as f:
        f.write(docker_compose_content)
    
    print("✅ docker-compose-aws.yml creado")

def create_aws_init_sql():
    """Crear script SQL de inicialización"""
    print("📋 Creando script SQL de inicialización...")
    
    init_sql_content = """-- Script de inicialización para AWS
CREATE TABLE IF NOT EXISTS noticias (
    id SERIAL PRIMARY KEY,
    titulo TEXT,
    fecha TIMESTAMP,
    hora TIME,
    resumen TEXT,
    contenido TEXT,
    categoria VARCHAR(100),
    autor VARCHAR(200),
    tags TEXT,
    url TEXT UNIQUE,
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imagenes TEXT,
    fuente VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_noticias_fuente ON noticias(fuente);
CREATE INDEX IF NOT EXISTS idx_noticias_fecha ON noticias(fecha);
CREATE INDEX IF NOT EXISTS idx_noticias_url ON noticias(url);

-- Tabla de control de scraping
CREATE TABLE IF NOT EXISTS scraping_control (
    id SERIAL PRIMARY KEY,
    fuente VARCHAR(100) NOT NULL,
    ultima_pagina INTEGER DEFAULT 0,
    ultima_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) DEFAULT 'activo',
    total_noticias INTEGER DEFAULT 0
);

-- Insertar fuentes de noticias
INSERT INTO scraping_control (fuente, ultima_pagina, estado) VALUES
('Pachamama Radio', 0, 'activo'),
('Puno Noticias', 0, 'activo'),
('Sin Fronteras', 0, 'activo'),
('Los Andes', 0, 'activo')
ON CONFLICT (fuente) DO NOTHING;
"""
    
    with open('init.sql', 'w') as f:
        f.write(init_sql_content)
    
    print("✅ init.sql creado")

def create_aws_system_script():
    """Crear script principal para AWS"""
    print("🚀 Creando script principal para AWS...")
    
    aws_system_content = """#!/usr/bin/env python3
\"\"\"
Sistema principal para AWS
Ejecuta scraping recursivo continuo
\"\"\"

import os
import time
import psycopg2
import logging
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aws_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración Celery para AWS
celery_app = Celery('aws_news_system')
celery_app.conf.broker_url = 'redis://redis:6379/0'
celery_app.conf.result_backend = 'redis://redis:6379/0'
celery_app.conf.timezone = 'America/Lima'

# Configuración de tareas
celery_app.conf.beat_schedule = {
    'scrape-pachamama': {
        'task': 'scrape_source',
        'schedule': crontab(minute=0, hour='*/2'),  # Cada 2 horas
        'args': ('pachamamaradio',)
    },
    'scrape-puno': {
        'task': 'scrape_source',
        'schedule': crontab(minute=30, hour='*/2'),  # Cada 2 horas, 30 min después
        'args': ('punonoticias',)
    },
    'scrape-sinfronteras': {
        'task': 'scrape_source',
        'schedule': crontab(minute=0, hour='*/3'),  # Cada 3 horas
        'args': ('sinfronteras',)
    },
    'scrape-losandes': {
        'task': 'scrape_source',
        'schedule': crontab(minute=30, hour='*/3'),  # Cada 3 horas, 30 min después
        'args': ('losandes',)
    },
    'cleanup-old-data': {
        'task': 'cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2 AM
    }
}

def connect_to_db():
    \"\"\"Conectar a la base de datos\"\"\"
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', '123456'),
            database=os.getenv('POSTGRES_DB', 'noticias')
        )
        return conn
    except Exception as e:
        logger.error(f"Error conectando a DB: {e}")
        return None

@celery_app.task
def scrape_source(source_name):
    \"\"\"Tarea para hacer scraping de una fuente específica\"\"\"
    logger.info(f"🕷️  Iniciando scraping de {source_name}")
    
    try:
        # Importar el scraper correspondiente
        if source_name == 'pachamamaradio':
            from spiders.pachamamaradio_local import PachamamaRadioLocalScraper
            scraper = PachamamaRadioLocalScraper()
        elif source_name == 'punonoticias':
            from spiders.punonoticias_local import PunoNoticiasLocalScraper
            scraper = PunoNoticiasLocalScraper()
        elif source_name == 'sinfronteras':
            from spiders.sinfronteras_local import SinFronterasLocalScraper
            scraper = SinFronterasLocalScraper()
        elif source_name == 'losandes':
            from spiders.losandes_local import LosAndesLocalScraper
            scraper = LosAndesLocalScraper()
        else:
            logger.error(f"Fuente desconocida: {source_name}")
            return False
        
        # Obtener última página procesada
        conn = connect_to_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("SELECT ultima_pagina FROM scraping_control WHERE fuente = %s", (source_name,))
        result = cursor.fetchone()
        last_page = result[0] if result else 0
        
        # Configurar scraper para continuar desde la última página
        scraper.start_page = last_page + 1
        scraper.max_pages = 10  # Procesar 10 páginas por ejecución
        
        # Ejecutar scraping
        articles = scraper.scrape_news()
        
        # Guardar en base de datos
        saved_count = 0
        for article in articles:
            try:
                cursor.execute("""
INSERT INTO noticias (titulo, fecha, hora, resumen, contenido, categoria, autor, tags, url, fecha_extraccion, imagenes, fuente, created_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (url) DO NOTHING
                """, (
                    article.get('titulo'),
                    article.get('fecha'),
                    article.get('hora'),
                    article.get('resumen'),
                    article.get('contenido'),
                    article.get('categoria'),
                    article.get('autor'),
                    article.get('tags'),
                    article.get('url'),
                    article.get('fecha_extraccion'),
                    article.get('imagenes'),
                    article.get('fuente'),
                    article.get('created_at')
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"Error guardando artículo: {e}")
                continue
        
        # Actualizar control de scraping
        cursor.execute("""
UPDATE scraping_control 
SET ultima_pagina = %s, ultima_ejecucion = %s, total_noticias = total_noticias + %s
WHERE fuente = %s
        """, (scraper.start_page + scraper.max_pages - 1, datetime.now(), saved_count, source_name))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ {source_name}: {saved_count} noticias guardadas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en scraping de {source_name}: {e}")
        return False

@celery_app.task
def cleanup_old_data():
    \"\"\"Limpiar datos antiguos (opcional)\"\"\"
    logger.info("🧹 Limpiando datos antiguos...")
    
    try:
        conn = connect_to_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Eliminar noticias más antiguas de 30 días
        cursor.execute("""
DELETE FROM noticias 
WHERE fecha_extraccion < %s
        """, (datetime.now() - timedelta(days=30),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Eliminadas {deleted_count} noticias antiguas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
        return False

def main():
    \"\"\"Función principal\"\"\"
    logger.info("🚀 Iniciando sistema AWS de noticias")
    
    # Crear directorios necesarios
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Esperar a que los servicios estén listos
    logger.info("⏳ Esperando servicios...")
    time.sleep(30)
    
    # Verificar conexión a base de datos
    conn = connect_to_db()
    if not conn:
        logger.error("❌ No se pudo conectar a la base de datos")
        return
    
    conn.close()
    logger.info("✅ Base de datos conectada")
    
    # Iniciar Celery Beat
    logger.info("🔄 Iniciando Celery Beat...")
    celery_app.start()

if __name__ == "__main__":
    main()
"""
    
    with open('start_aws_system.py', 'w') as f:
        f.write(aws_system_content)
    
    print("✅ start_aws_system.py creado")

def create_aws_dockerfile():
    """Crear Dockerfile optimizado para AWS"""
    print("🐳 Creando Dockerfile para AWS...")
    
    dockerfile_content = """FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY api/requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p data logs celery_tasks celery_workers

# Configurar permisos
RUN chmod +x start_aws_system.py

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["python", "start_aws_system.py"]
"""
    
    with open('Dockerfile.aws', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Dockerfile.aws creado")

def create_aws_startup_script():
    """Crear script de inicio para AWS"""
    print("🚀 Creando script de inicio para AWS...")
    
    startup_script = """#!/bin/bash
# Script de inicio para AWS EC2

echo "🚀 Iniciando sistema de noticias en AWS..."

# Actualizar sistema
sudo apt-get update

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Crear directorio del proyecto
mkdir -p /home/ubuntu/news-scraping
cd /home/ubuntu/news-scraping

# Copiar archivos del proyecto (esto se haría manualmente o via git)
# git clone <tu-repositorio> .

# Iniciar servicios
docker-compose -f docker-compose-aws.yml up -d --build

echo "✅ Sistema iniciado correctamente"
echo "📊 Monitorear con: docker-compose -f docker-compose-aws.yml logs -f"
"""
    
    with open('aws_startup.sh', 'w') as f:
        f.write(startup_script)
    
    # Hacer ejecutable
    os.chmod('aws_startup.sh', 0o755)
    print("✅ aws_startup.sh creado")

def create_aws_monitoring_script():
    """Crear script de monitoreo para AWS"""
    print("📊 Creando script de monitoreo...")
    
    monitoring_script = """#!/usr/bin/env python3
\"\"\"
Script de monitoreo para AWS
\"\"\"

import psycopg2
import time
from datetime import datetime

def connect_to_db():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='123456',
            database='noticias'
        )
        return conn
    except Exception as e:
        print(f"❌ Error conectando a DB: {e}")
        return None

def get_stats():
    \"\"\"Obtener estadísticas del sistema\"\"\"
    conn = connect_to_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Total de noticias
    cursor.execute("SELECT COUNT(*) FROM noticias")
    total_news = cursor.fetchone()[0]
    
    # Noticias por fuente
    cursor.execute("SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente")
    by_source = cursor.fetchall()
    
    # Últimas noticias
    cursor.execute("SELECT titulo, fuente, fecha_extraccion FROM noticias ORDER BY fecha_extraccion DESC LIMIT 5")
    latest_news = cursor.fetchall()
    
    # Control de scraping
    cursor.execute("SELECT fuente, ultima_pagina, ultima_ejecucion, total_noticias FROM scraping_control")
    scraping_control = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    print("📊 ESTADÍSTICAS DEL SISTEMA")
    print("=" * 50)
    print(f"📰 Total de noticias: {total_news}")
    print()
    
    print("📋 Por fuente:")
    for fuente, count in by_source:
        print(f"   {fuente}: {count}")
    print()
    
    print("🕷️  Control de scraping:")
    for fuente, pagina, ejecucion, total in scraping_control:
        print(f"   {fuente}: Página {pagina}, Última ejecución: {ejecucion}, Total: {total}")
    print()
    
    print("📄 Últimas noticias:")
    for titulo, fuente, fecha in latest_news:
        print(f"   {titulo[:50]}... ({fuente}) - {fecha}")

if __name__ == "__main__":
    while True:
        get_stats()
        print("\\n" + "="*50)
        time.sleep(60)  # Actualizar cada minuto
"""
    
    with open('aws_monitor.py', 'w') as f:
        f.write(monitoring_script)
    
    print("✅ aws_monitor.py creado")

def main():
    """Función principal"""
    print("☁️  CONFIGURACIÓN PARA AWS")
    print("=" * 50)
    
    # Crear archivos de configuración
    create_aws_docker_compose()
    create_aws_init_sql()
    create_aws_system_script()
    create_aws_dockerfile()
    create_aws_startup_script()
    create_aws_monitoring_script()
    
    print("\n✅ ¡Configuración para AWS completada!")
    print("\n📋 Archivos creados:")
    print("   - docker-compose-aws.yml")
    print("   - init.sql")
    print("   - start_aws_system.py")
    print("   - Dockerfile.aws")
    print("   - aws_startup.sh")
    print("   - aws_monitor.py")
    
    print("\n🚀 Próximos pasos:")
    print("1. Subir archivos a tu instancia AWS EC2")
    print("2. Ejecutar: chmod +x aws_startup.sh && ./aws_startup.sh")
    print("3. Monitorear con: python aws_monitor.py")

if __name__ == "__main__":
    main()
