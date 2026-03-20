import os
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
import joblib # 🎯 NUEVO: Para guardar el modelo físicamente

# Machine Learning & Forecasting
from sklearn.metrics import mean_absolute_error, mean_squared_error
from catboost import CatBoostRegressor
from mlforecast import MLForecast
from mlforecast.target_transforms import Differences
from mlforecast.lag_transforms import RollingMean, RollingStd
from mlforecast.utils import PredictionIntervals 

# Tracking & Optimization
import mlflow
import mlflow.sklearn
import optuna

# ==========================================
# 🧱 CONFIGURACIÓN DE RUTAS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Mantenemos MLflow para el tracking local de métricas durante el entrenamiento
DB_PATH = f"sqlite:///{BASE_DIR.as_posix()}/mlflow.db"
ARTIFACT_ROOT = f"file:///{BASE_DIR.as_posix()}/mlflow_artifacts"
EXPERIMENT_NAME = "Portfolio_Forecasting_Global"

mlflow.set_tracking_uri(DB_PATH)
optuna.logging.set_verbosity(optuna.logging.WARNING)

def get_or_create_experiment():
    exp = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if exp is None:
        return mlflow.create_experiment(
            name=EXPERIMENT_NAME, 
            artifact_location=ARTIFACT_ROOT
        )
    return exp.experiment_id

def objective(trial, df):
    param = {
        'iterations': trial.suggest_int('iterations', 200, 800),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'depth': trial.suggest_int('depth', 4, 8),
        'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1e-3, 10.0, log=True),
        'random_seed': 42,
        'silent': True
    }

    fcst = MLForecast(
        models={'CatBoost': CatBoostRegressor(**param)},
        freq='h', 
        lags=[1, 2, 3, 24, 168], 
        lag_transforms={
            1: [RollingMean(window_size=24)], 
            24: [RollingMean(window_size=168), RollingStd(window_size=168)] 
        },
        date_features=['hour', 'dayofweek', 'month'], 
        target_transforms=[Differences([24, 168])] 
    )

    static_cols = [col for col in df.columns if col.startswith('is_') or col == 'country']
    cv_res = fcst.cross_validation(df=df, n_windows=3, h=24, step_size=24, static_features=static_cols)
    return mean_absolute_error(cv_res['y'], cv_res['CatBoost'])

def train_model():
    print(f"🏠 Proyecto detectado en: {BASE_DIR}")
    exp_id = get_or_create_experiment()
    mlflow.set_experiment(EXPERIMENT_NAME)

    # 1. Carga de datos
    data_path = BASE_DIR / "data" / "processed" / "features_clean.parquet"
    if not data_path.exists():
        print(f"❌ Error: No se encontró el dataset en {data_path}")
        return

    df = pd.read_parquet(data_path)
    df['country'] = df['unique_id']
    df = pd.get_dummies(df, columns=['country'], prefix='is', dtype=float)
    
    print(f"📊 Dataset cargado con {len(df)} registros.")

    # 2. Optimización de hiperparámetros
    print("🔍 [Optuna] Iniciando optimización...")
    study = optuna.create_study(direction="minimize")
    study.optimize(lambda trial: objective(trial, df), n_trials=10)
    best_params = study.best_params
    print(f"🏆 Mejores parámetros encontrados: {best_params}")

    # 3. Entrenamiento
    with mlflow.start_run(experiment_id=exp_id):
        best_params.update({'random_seed': 42, 'silent': True})
        mlflow.log_params(best_params)
        
        fcst_final = MLForecast(
            models={'CatBoost': CatBoostRegressor(**best_params)},
            freq='h', 
            lags=[1, 2, 3, 24, 168], 
            lag_transforms={
                1: [RollingMean(window_size=24)], 
                24: [RollingMean(window_size=168), RollingStd(window_size=168)] 
            },
            date_features=['hour', 'dayofweek', 'month'], 
            target_transforms=[Differences([24, 168])]
        )

        static_cols = [col for col in df.columns if col.startswith('is_') or col == 'country']
        
        # Backtesting
        print("🔄 Ejecutando Time Series CV final (Backtesting)...")
        cv_res_final = fcst_final.cross_validation(df=df, n_windows=7, h=24, step_size=24, static_features=static_cols)
        
        mae_val = mean_absolute_error(cv_res_final['y'], cv_res_final['CatBoost'])
        rmse_val = np.sqrt(mean_squared_error(cv_res_final['y'], cv_res_final['CatBoost']))
        
        print(f"📉 Métricas calculadas: MAE={mae_val:.2f}, RMSE={rmse_val:.2f}")
        mlflow.log_metric("cv_mae", float(mae_val))
        mlflow.log_metric("cv_rmse", float(rmse_val))

        # Fit Final
        print("🚀 Entrenando modelo final con intervalos de predicción...")
        fcst_final.fit(df, prediction_intervals=PredictionIntervals(h=24), fitted=True, static_features=static_cols)

        output_dir = BASE_DIR / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        cv_res_final.to_parquet(output_dir / "cv_predictions.parquet")
        
        # 4. 🎯 EXPORTACIÓN FÍSICA PARA LA NUBE
        print("💾 Exportando modelo a formato .pkl...")
        models_dir = BASE_DIR / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        model_export_path = models_dir / "model_prod.pkl"
        
        joblib.dump(fcst_final, model_export_path)
        print(f"✅ Modelo guardado localmente en {model_export_path}")

        # 5. ☁️ SUBIDA OPCIONAL A GOOGLE CLOUD STORAGE
        # Si ejecutamos esto en Google Cloud, le pasaremos el nombre del bucket
        bucket_name = os.environ.get("MODEL_BUCKET_NAME")
        if bucket_name:
            try:
                from google.cloud import storage
                print(f"☁️ Subiendo modelo a GCS (Bucket: {bucket_name})...")
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob("models/model_prod.pkl")
                blob.upload_from_filename(str(model_export_path))
                print("✅ ¡Modelo subido a la nube con éxito!")
            except Exception as e:
                print(f"❌ Error al subir a GCS: {e}")

if __name__ == "__main__":
    if os.path.exists("mlruns"):
        shutil.rmtree("mlruns")
    train_model()