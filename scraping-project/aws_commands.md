# 🚀 Comandos Útiles para AWS

## 📋 Comandos de Despliegue

```bash
# 1. Conectar a tu instancia EC2
ssh -i tu-key.pem ubuntu@tu-ip-publica

# 2. Desplegar sistema completo
wget https://raw.githubusercontent.com/IVANMAMANI2003/news_scraping/main/scraping-project/aws_startup.sh
chmod +x aws_startup.sh
./aws_startup.sh
```

## 🔍 Comandos de Monitoreo

```bash
# Ver contenedores activos
sudo docker ps

# Ver logs del sistema
sudo docker-compose -f docker-compose-aws.yml logs -f

# Ver logs específicos
sudo docker-compose -f docker-compose-aws.yml logs -f aws_news_system

# Monitoreo avanzado
sudo docker exec -it aws_news_system python aws_monitor_advanced.py

# Prueba del sistema
sudo docker exec -it aws_news_system python test_parallel_scraping.py
```

## 🗄️ Comandos de Base de Datos

```bash
# Acceder a PostgreSQL
sudo docker exec -it aws_postgres psql -U postgres -d noticias

# Ver datos por fuente
sudo docker exec -it aws_postgres psql -U postgres -d noticias -c "SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente;"

# Ver últimas noticias
sudo docker exec -it aws_postgres psql -U postgres -d noticias -c "SELECT titulo, fuente, fecha_extraccion FROM noticias ORDER BY fecha_extraccion DESC LIMIT 10;"

# Verificar duplicados
sudo docker exec -it aws_postgres psql -U postgres -d noticias -c "SELECT url, COUNT(*) FROM noticias GROUP BY url HAVING COUNT(*) > 1;"
```

## 🔧 Comandos de Mantenimiento

```bash
# Reiniciar sistema
sudo docker-compose -f docker-compose-aws.yml down
sudo docker-compose -f docker-compose-aws.yml up -d --build

# Limpiar contenedores
sudo docker system prune -f

# Ver uso de recursos
sudo docker stats

# Backup de base de datos
sudo docker exec aws_postgres pg_dump -U postgres noticias > backup_$(date +%Y%m%d_%H%M%S).sql
```

## 📊 Características del Sistema

✅ **Scraping Paralelo**: 4 hilos simultáneos  
✅ **Sin Limpieza Automática**: Mantiene toda la data histórica  
✅ **Detección de Duplicados**: Evita URLs repetidas  
✅ **Scraping Continuo**: Cada hora automáticamente  
✅ **Monitoreo Avanzado**: Verificación de estado y calidad  
✅ **Recuperación Automática**: Continúa después de reinicios  
