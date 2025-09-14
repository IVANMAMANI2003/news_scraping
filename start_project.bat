@echo off
echo ========================================
echo    BIZNEWS - SISTEMA DE NOTICIAS
echo ========================================
echo.

echo [1/4] Iniciando Backend (API)...
cd scraping-project
start "BizNews Backend" cmd /k "venv\Scripts\activate && uvicorn api.main:app --reload --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak > nul

echo [2/4] Iniciando Frontend...
cd ..\biznews
start "BizNews Frontend" cmd /k "python serve.py"
timeout /t 2 /nobreak > nul

echo [3/4] Abriendo navegador...
start http://localhost:8080
timeout /t 2 /nobreak > nul

echo [4/4] Verificando servicios...
echo.
echo ✅ Backend API: http://localhost:8000
echo ✅ Frontend: http://localhost:8080
echo ✅ Documentación API: http://localhost:8000/docs
echo.
echo Presiona cualquier tecla para salir...
pause > nul
