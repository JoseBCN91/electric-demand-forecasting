import os
from pathlib import Path
from huggingface_hub import HfApi

def main():
    # El token se inyectará automáticamente desde GitHub Actions
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise ValueError("❌ No se encontró el HF_TOKEN en las variables de entorno.")

    # 🎯 Tus datos exactos
    REPO_ID = "Jose91-BCN/Electricity_demand"
    
    api = HfApi(token=token)
    base_dir = Path(__file__).resolve().parent.parent.parent

    print("🚀 Iniciando subida directa a Hugging Face Space...")

    # 1. Subir la base de datos de MLflow
    db_path = base_dir / "mlflow.db"
    if db_path.exists():
        print(f"📦 Subiendo {db_path.name}...")
        api.upload_file(
            path_or_fileobj=str(db_path),
            path_in_repo="mlflow.db",
            repo_id=REPO_ID,
            repo_type="space"
        )
    else:
        print("⚠️ No se encontró mlflow.db")

    # 2. Subir la carpeta de los modelos (Artefactos)
    artifacts_path = base_dir / "mlflow_artifacts"
    if artifacts_path.exists():
        print(f"📦 Subiendo carpeta {artifacts_path.name}/...")
        api.upload_folder(
            folder_path=str(artifacts_path),
            path_in_repo="mlflow_artifacts",
            repo_id=REPO_ID,
            repo_type="space"
        )
    else:
        print("⚠️ No se encontró la carpeta mlflow_artifacts")

    print("✅ ¡Archivos subidos con éxito! El Space se reiniciará automáticamente.")

if __name__ == "__main__":
    main()
