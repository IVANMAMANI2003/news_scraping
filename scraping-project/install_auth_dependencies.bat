@echo off
echo ========================================
echo Instalando dependencias de autenticacion
echo ========================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: No se encontro el entorno virtual
    echo Por favor, crea el entorno virtual primero:
    echo   python -m venv venv
    pause
    exit /b 1
)

echo Instalando bcrypt y PyJWT...
venv\Scripts\python.exe -m pip install bcrypt==4.1.2 PyJWT==2.8.0

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Dependencias instaladas correctamente!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ERROR al instalar dependencias
    echo ========================================
)

pause

