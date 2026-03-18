#!/bin/bash

# =================================================================
# ORQUESTADOR DE DESPLIEGUE - HUGGING FACE SPACES (16GB RAM)
# =================================================================

# Salir inmediatamente si un comando falla
set -e

echo "----------------------------------------------------------"
echo "🧠 PASO 1: Iniciando Entrenamiento del Modelo (CatBoost)"
echo "----------------------------------------------------------"
# Ejecutamos el entrenamiento. 
# Esto usará los 16GB de RAM del Space para procesar los .parquet
# y generará el 'mlflow.db' y los artefactos del modelo.
python -m src.training.train

echo "✅ Entrenamiento completado con éxito."

echo "----------------------------------------------------------"
echo "📡 PASO 2: Lanzando API de Inferencia (FastAPI)"
echo "----------------------------------------------------------"
# Lanzamos FastAPI en el puerto 8000 en segundo plano (&)
# Usamos 'python -m' para asegurar que el PYTHONPATH sea correcto
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# Esperamos unos segundos para que MLflow y FastAPI carguen el modelo en memoria
echo "⏳ Esperando a que el modelo cargue en la API..."
sleep 10

echo "----------------------------------------------------------"
echo "📊 PASO 3: Lanzando Dashboard (Streamlit)"
echo "----------------------------------------------------------"
# Streamlit DEBE ir en el puerto 7860 para que Hugging Face lo muestre
# No usamos '&' aquí porque queremos que este proceso mantenga vivo el contenedor
streamlit run src/app/dashboard.py --server.port 7860 --server.address 0.0.0.0
