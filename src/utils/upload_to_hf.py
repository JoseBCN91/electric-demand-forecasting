from huggingface_hub import HfApi
import os

def upload_data():
    api = HfApi()
    token = os.getenv("HF_TOKEN")
    repo_id = "Jose91-BCN/Electricity_demand" # Tu Space
    
    # Lista de archivos que queremos actualizar en el Space
    files_to_upload = [
        "data/processed/features_clean.parquet",
        # Añade aquí otros archivos si procesas más
    ]
    
    for file_path in files_to_upload:
        if os.path.exists(file_path):
            print(f"Subiendo {file_path}...")
            api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=file_path,
                repo_id=repo_id,
                repo_type="space",
                token=token
            )
        else:
            print(f"⚠️ Archivo {file_path} no encontrado.")

if __name__ == "__main__":
    upload_data()
