#!/bin/bash

echo "========================================"
echo "    BIZNEWS - SISTEMA DE NOTICIAS"
echo "========================================"
echo

echo "[1/4] Iniciando Backend (API)..."
cd scraping-project
source venv/bin/activate
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
sleep 3

echo "[2/4] Iniciando Frontend..."
cd ../biznews
python serve.py &
FRONTEND_PID=$!
sleep 2

echo "[3/4] Abriendo navegador..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8080
elif command -v open > /dev/null; then
    open http://localhost:8080
fi
sleep 2

echo "[4/4] Verificando servicios..."
echo
echo "✅ Backend API: http://localhost:8000"
echo "✅ Frontend: http://localhost:8080"
echo "✅ Documentación API: http://localhost:8000/docs"
echo
echo "Presiona Ctrl+C para detener todos los servicios..."

# Función para limpiar procesos al salir
cleanup() {
    echo
    echo "Deteniendo servicios..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Servicios detenidos."
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

# Esperar indefinidamente
wait
