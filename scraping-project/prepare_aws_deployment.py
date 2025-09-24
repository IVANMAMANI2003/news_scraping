#!/usr/bin/env python3
"""
Script para preparar el despliegue en AWS
Sube todos los archivos necesarios al repositorio
"""

import os
import shutil
import subprocess


def create_aws_deployment_structure():
    """Crear estructura de archivos para AWS"""
    print("📁 Creando estructura de archivos para AWS...")
    
    # Crear directorio de despliegue
    aws_dir = "aws_deployment"
    os.makedirs(aws_dir, exist_ok=True)
    
    # Archivos que necesitamos copiar
    files_to_copy = [
        "docker-compose-aws.yml",
        "init.sql", 
        "start_aws_system.py",
        "aws_startup.sh",
        "aws_monitor.py",
        "Dockerfile.aws",
        "AWS_DEPLOYMENT_INSTRUCTIONS.md"
    ]
    
    # Copiar archivos
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, aws_dir)
            print(f"✅ Copiado: {file}")
        else:
            print(f"❌ No encontrado: {file}")
    
    print(f"✅ Estructura creada en: {aws_dir}")
    return aws_dir

def create_deployment_readme():
    """Crear README específico para AWS"""
    readme_content = """# 🚀 Despliegue en AWS - Sistema de Noticias

## 📋 Archivos incluidos

- `docker-compose-aws.yml` - Configuración Docker para AWS
- `init.sql` - Script de inicialización de base de datos
- `start_aws_system.py` - Sistema principal con scraping recursivo
- `aws_startup.sh` - Script de inicio automático
- `aws_monitor.py` - Script de monitoreo en tiempo real
- `Dockerfile.aws` - Dockerfile optimizado para AWS
- `AWS_DEPLOYMENT_INSTRUCTIONS.md` - Instrucciones completas

## 🚀 Instrucciones rápidas

### 1. En tu instancia EC2:
```bash
# Descargar y ejecutar
wget https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/aws_startup.sh
chmod +x aws_startup.sh
./aws_startup.sh
```

### 2. Monitorear:
```bash
cd /home/ubuntu/news-scraping/scraping-project
python aws_monitor.py
```

### 3. Ver logs:
```bash
docker-compose -f docker-compose-aws.yml logs -f
```

## 📊 Características

- ✅ Scraping recursivo automático
- ✅ PostgreSQL en la misma instancia
- ✅ Continuación desde donde se quedó
- ✅ Monitoreo en tiempo real
- ✅ Backup automático disponible

## 🔧 Fuentes de noticias

- **Pachamama Radio**: Cada 2 horas
- **Puno Noticias**: Cada 2 horas (30 min después)
- **Sin Fronteras**: Cada 3 horas
- **Los Andes**: Cada 3 horas (30 min después)

## 📞 Soporte

Para problemas o preguntas, revisar:
- `AWS_DEPLOYMENT_INSTRUCTIONS.md`
- Logs del sistema
- Issues en GitHub
"""
    
    with open("aws_deployment/README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ README.md creado para AWS")

def create_quick_deploy_script():
    """Crear script de despliegue rápido"""
    quick_deploy = """#!/bin/bash
# Script de despliegue rápido para AWS

echo "🚀 DESPLIEGUE RÁPIDO EN AWS"
echo "=========================="

# Verificar que estamos en Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    echo "❌ Este script está diseñado para Ubuntu"
    exit 1
fi

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt-get update

# Instalar Docker
echo "🐳 Instalando Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
echo "🔧 Instalando Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Crear directorio
echo "📁 Creando directorio del proyecto..."
mkdir -p /home/ubuntu/news-scraping
cd /home/ubuntu/news-scraping

# Clonar repositorio
echo "📥 Clonando repositorio..."
git clone https://github.com/IVANMAMANI2003/news_scraping.git .

# Navegar al proyecto
cd scraping-project

# Descargar archivos AWS
echo "⬇️  Descargando archivos de configuración AWS..."
wget -O docker-compose-aws.yml https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/docker-compose-aws.yml
wget -O init.sql https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/init.sql
wget -O start_aws_system.py https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/start_aws_system.py
wget -O aws_monitor.py https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/aws_monitor.py
wget -O Dockerfile.aws https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/Dockerfile.aws

# Crear directorios
mkdir -p data logs

# Iniciar sistema
echo "🚀 Iniciando sistema..."
docker-compose -f docker-compose-aws.yml up -d --build

echo "✅ ¡Sistema iniciado correctamente!"
echo "📊 Para monitorear: python aws_monitor.py"
echo "📋 Para ver logs: docker-compose -f docker-compose-aws.yml logs -f"
"""
    
    with open("aws_deployment/quick_deploy.sh", "w") as f:
        f.write(quick_deploy)
    
    # Hacer ejecutable
    os.chmod("aws_deployment/quick_deploy.sh", 0o755)
    print("✅ quick_deploy.sh creado")

def main():
    """Función principal"""
    print("☁️  PREPARANDO DESPLIEGUE PARA AWS")
    print("=" * 50)
    
    # Crear estructura
    aws_dir = create_aws_deployment_structure()
    
    # Crear README
    create_deployment_readme()
    
    # Crear script de despliegue rápido
    create_quick_deploy_script()
    
    print("\n✅ ¡Preparación completada!")
    print(f"\n📁 Archivos listos en: {aws_dir}/")
    print("\n📋 Próximos pasos:")
    print("1. Subir archivos a tu repositorio GitHub")
    print("2. Crear instancia EC2 en AWS")
    print("3. Ejecutar: wget https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/aws_startup.sh")
    print("4. Ejecutar: chmod +x aws_startup.sh && ./aws_startup.sh")
    
    print("\n🚀 Comando de despliegue rápido:")
    print("wget https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/aws_deployment/quick_deploy.sh")
    print("chmod +x quick_deploy.sh && ./quick_deploy.sh")

if __name__ == "__main__":
    main()
