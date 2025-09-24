#!/bin/bash
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

# Agregar usuario ubuntu al grupo docker
sudo usermod -aG docker ubuntu

# Crear directorio del proyecto
mkdir -p /home/ubuntu/news-scraping
cd /home/ubuntu/news-scraping

# Clonar tu repositorio de GitHub
git clone https://github.com/IVANMAMANI2003/news_scraping.git .

# Navegar al directorio del proyecto
cd scraping-project

# Copiar archivos de configuración AWS desde la raíz del repositorio
cp ../docker-compose-aws.yml .
cp ../init.sql .
cp ../start_aws_system.py .
cp ../start_aws_simple.py .
cp ../parallel_scraping_system.py .
cp ../test_parallel_scraping.py .
cp ../aws_monitor.py .
cp ../aws_monitor_advanced.py .
cp ../Dockerfile.aws .

# Crear directorios necesarios
mkdir -p data logs

# Iniciar servicios
sudo docker-compose -f docker-compose-aws.yml up -d --build

echo "✅ Sistema iniciado correctamente"
echo "📊 Monitorear con: sudo docker-compose -f docker-compose-aws.yml logs -f"
