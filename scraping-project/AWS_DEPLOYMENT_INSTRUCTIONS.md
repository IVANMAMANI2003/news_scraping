# 🚀 INSTRUCCIONES PARA DESPLEGAR EN AWS

## 📋 Requisitos previos
1. Instancia EC2 con Ubuntu 20.04 o superior
2. Acceso SSH a la instancia
3. Grupo de seguridad configurado (puertos 22, 80, 443, 5432, 6379)

## 🔧 Pasos de despliegue

### 1. Conectar a la instancia EC2
```bash
ssh -i tu-key.pem ubuntu@tu-ip-publica
```

### 2. Actualizar el sistema
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 3. Instalar Docker y Docker Compose
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 4. Subir archivos del proyecto
```bash
# Crear directorio
mkdir -p /home/ubuntu/news-scraping
cd /home/ubuntu/news-scraping

# Subir archivos (usar scp, rsync, o git)
scp -i tu-key.pem -r ./aws_deployment/* ubuntu@tu-ip:/home/ubuntu/news-scraping/
```

### 5. Iniciar el sistema
```bash
cd /home/ubuntu/news-scraping
chmod +x aws_startup.sh
./aws_startup.sh
```

### 6. Verificar que funciona
```bash
# Ver contenedores
docker ps

# Ver logs
docker-compose -f docker-compose-aws.yml logs -f

# Monitorear estadísticas
python aws_monitor.py
```

## 📊 Monitoreo

### Ver estadísticas en tiempo real
```bash
python aws_monitor.py
```

### Ver logs del sistema
```bash
docker-compose -f docker-compose-aws.yml logs -f news_system
```

### Acceder a la base de datos
```bash
docker exec -it aws_postgres psql -U postgres -d noticias
```

## 🔄 Mantenimiento

### Reiniciar el sistema
```bash
docker-compose -f docker-compose-aws.yml restart
```

### Actualizar el sistema
```bash
docker-compose -f docker-compose-aws.yml down
docker-compose -f docker-compose-aws.yml up -d --build
```

### Hacer backup de la base de datos
```bash
docker exec aws_postgres pg_dump -U postgres noticias > backup_$(date +%Y%m%d_%H%M%S).sql
```

## 🚨 Solución de problemas

### Si los contenedores no inician
```bash
docker-compose -f docker-compose-aws.yml logs
```

### Si hay problemas de memoria
```bash
# Aumentar swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Si hay problemas de red
```bash
# Verificar puertos
sudo netstat -tlnp | grep :5432
sudo netstat -tlnp | grep :6379
```

## 📈 Escalabilidad

### Para instancias más grandes
- Aumentar `max_pages` en `start_aws_system.py`
- Configurar múltiples workers de Celery
- Usar RDS para PostgreSQL en lugar de contenedor

### Para alta disponibilidad
- Usar Application Load Balancer
- Configurar múltiples instancias EC2
- Usar ElastiCache para Redis
