@echo off
echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale em python.org
    pause
    exit /b 1
)
echo Instalando dependencias...
pip install flask flask-cors --quiet
echo.
echo Iniciando sistema SESI Sumare...
python app.py
pause
