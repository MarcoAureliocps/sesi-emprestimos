#!/bin/bash
echo "Verificando Python..."
python3 --version 2>/dev/null || { echo "ERRO: Python3 não encontrado"; exit 1; }
echo "Instalando dependências..."
pip3 install flask flask-cors --quiet
echo ""
echo "Iniciando sistema SESI Sumaré..."
python3 app.py
