@echo off
echo ========================================
echo Instalando dependencias para API y Scrapers
echo ========================================
echo.

REM Verificar si hay entorno virtual
if exist venv\Scripts\activate.bat (
    echo [1/3] Activando entorno virtual...
    call venv\Scripts\activate.bat
    echo Entorno virtual activado.
) else (
    echo [1/3] No se encontro entorno virtual.
    echo Instalando en entorno global de Python...
)

echo.
echo [2/3] Instalando dependencias de api/requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r api/requirements.txt

echo.
echo [3/3] Verificando instalacion de dependencias criticas...
echo.
python -c "import bs4; print('✓ beautifulsoup4 instalado correctamente')" 2>nul || echo "✗ beautifulsoup4 NO instalado - Ejecuta: pip install beautifulsoup4"
python -c "import pandas; print('✓ pandas instalado correctamente')" 2>nul || echo "✗ pandas NO instalado - Ejecuta: pip install pandas"
python -c "import requests; print('✓ requests instalado correctamente')" 2>nul || echo "✗ requests NO instalado - Ejecuta: pip install requests"
python -c "import dateutil; print('✓ python-dateutil instalado correctamente')" 2>nul || echo "✗ python-dateutil NO instalado - Ejecuta: pip install python-dateutil"

echo.
echo ========================================
echo Instalacion completada
echo ========================================
echo.
echo IMPORTANTE: Si alguna dependencia falta, ejecuta manualmente:
echo   pip install beautifulsoup4 pandas requests python-dateutil
echo.
echo Reinicia el servidor de la API despues de instalar las dependencias.
echo.
pause

