import os
import joblib
from pathlib import Path

# ==========================================
# 🧱 CONFIGURACIÓN DE RUTAS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def download_model_from_gcs():
    """Descarga el modelo desde Google Cloud Storage si no existe en local."""
    
    models_dir = BASE_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    local_model_path = models_dir / "model_prod.pkl"
    
    # 1. Verificamos si ya lo tenemos en local (ahorra tiempo y ancho de banda)
    if local_model_path.exists():
        print(f"ℹ️ El modelo ya existe en local ({local_model_path}). Omitiendo descarga.")
        return local_model_path

    # 2. Si no existe, comprobamos si tenemos un bucket configurado
    bucket_name = os.environ.get("MODEL_BUCKET_NAME")
    if not bucket_name:
        print("❌ Error: No se encontró el modelo local y la variable 'MODEL_BUCKET_NAME' no está definida.")
        return None

    # 3. Descargamos desde la nube
    print(f"📥 Descargando modelo desde gs://{bucket_name}/models/model_prod.pkl...")
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob("models/model_prod.pkl")
        
        blob.download_to_filename(str(local_model_path))
        print("✅ Descarga completada con éxito.")
        return local_model_path
        
    except Exception as e:
        print(f"❌ Error fatal al descargar el modelo de GCS: {e}")
        return None

def load_production_model(model_name=None):
    """Carga el modelo estático (.pkl) en memoria para la inferencia."""
    print(f"🔮 [Inference] Inicializando cargador de modelo...")
    
    # Obtenemos la ruta del modelo (descargándolo si hace falta)
    model_path = download_model_from_gcs()
    
    if model_path and model_path.exists():
        try:
            print("⚙️ Cargando modelo en memoria usando joblib...")
            model = joblib.load(model_path)
            print("✅ ¡Modelo cargado y listo para inferencia!")
            return model
        except Exception as e:
            print(f"❌ Error al intentar leer el archivo .pkl: {e}")
            return None
            
    print("❌ No se pudo cargar ningún modelo. La API no podrá hacer predicciones.")
    return None