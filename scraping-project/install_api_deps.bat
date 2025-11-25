@echo off
echo ========================================
echo Instalando dependencias para API
echo ========================================
echo.

REM Verificar si hay entorno virtual
if exist venv\Scripts\activate.bat (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
    echo Entorno virtual activado.
) else (
    echo No se encontro entorno virtual.
    echo Instalando en entorno global de Python...
)

echo.
echo Instalando todas las dependencias de api/requirements.txt...
python -m pip install -r api/requirements.txt

echo.
echo Verificando instalacion de dependencias criticas...
python -c "import bs4; print('✓ beautifulsoup4 OK')" 2>nul || echo "✗ beautifulsoup4 FALTA"
python -c "import pandas; print('✓ pandas OK')" 2>nul || echo "✗ pandas FALTA"
python -c "import requests; print('✓ requests OK')" 2>nul || echo "✗ requests FALTA"
python -c "import dateutil; print('✓ python-dateutil OK')" 2>nul || echo "✗ python-dateutil FALTA"

echo.
echo ========================================
echo Si alguna dependencia falta, ejecuta:
echo   pip install beautifulsoup4 pandas requests python-dateutil
echo ========================================
pause

