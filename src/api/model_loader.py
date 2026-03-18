import mlflow.sklearn
import os
from pathlib import Path

# Subimos 3 niveles desde src/api/ para llegar a la raíz (ML_template)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = f"sqlite:///{BASE_DIR.as_posix()}/mlflow.db"

def load_production_model(model_name="CatBoost_Global_Load_Prod"):
    """Carga el modelo desde la base de datos unificada."""
    print(f"🔮 [Inference] Conectando a MLflow en {DB_PATH}")
    
    mlflow.set_tracking_uri(DB_PATH)
    mlflow.set_registry_uri(DB_PATH)
    
    # Intentamos cargar la versión más reciente
    model_uri = f"models:/{model_name}/latest"
    
    try:
        # Cargamos el modelo. MLflow resolverá internamente la ruta file:///
        model = mlflow.sklearn.load_model(model_uri)
        print(f"✅ Modelo '{model_name}' cargado desde el Registry.")
        return model
    except Exception as e:
        print(f"❌ Error al cargar el modelo: {e}")
        return None