#!/bin/bash

echo "🚀 Iniciando API de Forecasting (FastAPI)..."
# Lanzamos FastAPI en segundo plano (el símbolo & al final es la clave)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

echo "⏳ Esperando 5 segundos a que el modelo cargue..."
sleep 5

echo "📊 Iniciando Dashboard (Streamlit)..."
# Lanzamos Streamlit en el puerto 7860, que es el que Hugging Face exige
# IMPORTANTE: Verifica que la ruta 'src/app/dashboard.py' sea correcta según tu proyecto
streamlit run src/app/dashboard.py --server.port 7860 --server.address 0.0.0.0