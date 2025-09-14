@echo off
echo 🚀 REINICIANDO SISTEMA DE SCRAPING
echo ====================================

echo 🔄 Activando entorno virtual...
call venv\Scripts\activate

echo 🐳 Iniciando contenedores Docker...
docker-compose -f docker-compose-full.yml up -d

echo ⏳ Esperando que los servicios estén listos...
timeout /t 10 /nobreak

echo 👷 Iniciando sistema Celery...
start "Worker Scraping" cmd /k "venv\Scripts\activate && python celery_workers/start_worker.py --queue scraping"
start "Worker Migration" cmd /k "venv\Scripts\activate && python celery_workers/start_worker.py --queue migration"
start "Scheduler Beat" cmd /k "venv\Scripts\activate && python celery_workers/start_beat.py"

echo ✅ Sistema reiniciado correctamente!
echo 📊 Para ver el estado: docker ps
echo 🛑 Para detener: docker-compose -f docker-compose-full.yml down
pause
