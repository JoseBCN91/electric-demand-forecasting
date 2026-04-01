import os
import json
import joblib
from pathlib import Path
from datetime import datetime, timezone
from google.cloud import storage

from src.training.train import train_model
from src.utils.logger import model_logger

# ==========================================
# 🔐 GESTIÓN DE CREDENCIALES GCP
# ==========================================
def setup_gcp_credentials() -> bool:
    """
    Configure GCP credentials from environment variable.
    Returns True if credentials are properly set up, False otherwise.
    """
    gcp_creds_json = os.environ.get("GCP_CREDENTIALS_JSON")
    
    if not gcp_creds_json:
        model_logger.warning("GCP_CREDENTIALS_JSON not found. GCS operations will fail. Set this env var for cloud storage support.")
        return False
    
    try:
        creds_path = "/tmp/gcp_creds.json"
        with open(creds_path, "w") as f:
            f.write(gcp_creds_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        model_logger.info("✅ GCP credentials loaded successfully")
        return True
    except Exception as e:
        model_logger.error(f"❌ Failed to set up GCP credentials: {str(e)}")
        return False

# Initialize GCP credentials at module load time
gcp_available = setup_gcp_credentials()

# ==========================================
# 🧱 CONFIGURACIÓN DE RUTAS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOCAL_MODEL_PATH = BASE_DIR / "models" / "model_prod.pkl"


def get_model_age_gcs(bucket_name, blob_name="models/model_prod.pkl"):
    """
    Connect to Google Cloud Storage and return model age in days.
    If model doesn't exist or GCS is unavailable, returns None.
    
    Args:
        bucket_name: GCS bucket name
        blob_name: Path to model file in bucket
        
    Returns:
        Age in days (int) or None if unavailable
    """
    if not gcp_available:
        model_logger.debug("GCP not configured. Skipping GCS model age check.")
        return None
    
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            model_logger.info(f"Model not found in GCS: gs://{bucket_name}/{blob_name}")
            return None
            
        now = datetime.now(timezone.utc)
        age = now - blob.updated
        model_logger.debug(f"Model age: {age.days} days")
        return age.days
        
    except Exception as e:
        model_logger.warning(f"⚠️ Error checking model age in GCS: {str(e)}")
        return None

def load_production_model():
    """
    Load the production model (.pkl) into memory, training if necessary.
    
    Implements "Lazy Training" logic:
    - Trains from scratch if no model exists
    - Retrains if model is >7 days old
    - Downloads from GCS if needed
    - Falls back to local model if available
    
    Returns:
        Loaded model object or None if loading fails
    """
    model_logger.info("🔮 Initializing production model loader...")
    
    # ==========================================
    # 1. VALIDATE CONFIGURATION
    # ==========================================
    bucket_name = os.environ.get("MODEL_BUCKET_NAME")
    if not bucket_name:
        model_logger.warning("MODEL_BUCKET_NAME not set. Will use local model only.")
    
    # ==========================================
    # 2. CHECK MODEL AGE IN CLOUD
    # ==========================================
    model_logger.info("🔍 Checking model status...")
    age_days = get_model_age_gcs(bucket_name) if bucket_name else None
    
    # ==========================================
    # 3. LAZY TRAINING LOGIC
    # ==========================================
    if age_days is None and bucket_name:
        model_logger.warning("⚠️ No model found in GCS. Triggering training...")
        try:
            train_model()
        except Exception as e:
            model_logger.error(f"❌ Training failed: {str(e)}")
            return None
            
    elif age_days is not None and age_days >= 7:
        model_logger.warning(f"⚠️ Model is {age_days} days old (limit: 7). Retraining...")
        try:
            train_model()
        except Exception as e:
            model_logger.error(f"❌ Retraining failed: {str(e)}")
            return None
    else:
        if age_days is not None:
            model_logger.info(f"✅ Model is fresh ({age_days} days old). Skipping training.")

    # ==========================================
    # 4. DOWNLOAD MODEL FROM CLOUD IF NEEDED
    # ==========================================
    LOCAL_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not LOCAL_MODEL_PATH.exists() and bucket_name:
        model_logger.info(f"📥 Downloading model from gs://{bucket_name}/models/model_prod.pkl...")
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob("models/model_prod.pkl")
            blob.download_to_filename(str(LOCAL_MODEL_PATH))
            model_logger.info("✅ Download completed")
        except Exception as e:
            model_logger.error(f"❌ Failed to download model: {str(e)}")
            return None
    elif not LOCAL_MODEL_PATH.exists():
        model_logger.error(f"❌ Model not found at {LOCAL_MODEL_PATH} and no GCS bucket configured")
        return None

    # ==========================================
    # 5. LOAD MODEL INTO RAM
    # ==========================================
    try:
        model_logger.info(f"⚙️ Loading model from {LOCAL_MODEL_PATH}...")
        model = joblib.load(LOCAL_MODEL_PATH)
        model_logger.info("✅ Model loaded successfully and ready for inference")
        return model
    except Exception as e:
        model_logger.error(f"❌ Failed to load model file: {str(e)}")
        return None