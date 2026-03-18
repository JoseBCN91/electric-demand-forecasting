import pandas as pd
import requests
import warnings
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.api.model_loader import load_production_model

# ==========================================
# CONFIGURACIÓN Y SILENCIADO DE AVISOS
# ==========================================
# Silenciamos avisos de MLForecast en producción para logs limpios
warnings.filterwarnings("ignore", category=UserWarning)

COUNTRY_HUBS = {
    'ES': {"lat": 40.4168, "lon": -3.7038},  # Madrid
    'FR': {"lat": 48.8566, "lon": 2.3522},   # Paris
    'DE': {"lat": 52.5200, "lon": 13.4050},  # Berlin
    'IT': {"lat": 41.9028, "lon": 12.4964}   # Roma
}

app = FastAPI(
    title="API de Forecasting Eléctrico Global (ENTSO-E)",
    description="Predicción de demanda (MW) usando CatBoost y clima futuro.",
    version="3.1.0"
)

# Cargar el modelo al inicio
model = load_production_model(model_name="CatBoost_Global_Load_Prod")

class PredictRequest(BaseModel):
    horizon: int = 24  
    country: str = 'ES' 
    levels: Optional[List[int]] = [80, 95]

def get_broad_weather_europe() -> pd.DataFrame:
    """Descarga clima (1 día pasado + 7 días de forecast) para cubrir huecos."""
    all_weather_dfs = []
    url = "https://api.open-meteo.com/v1/forecast"
    
    for country_code, coords in COUNTRY_HUBS.items():
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "past_days": 1,
            "forecast_days": 7,
            "hourly": ["temperature_2m", "wind_speed_10m", "direct_radiation"],
            "timezone": "UTC"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()["hourly"]
        
        df = pd.DataFrame({
            "unique_id": country_code,
            "ds": pd.to_datetime(data["time"]),
            "temperature": data["temperature_2m"],
            "wind_speed": data["wind_speed_10m"],
            "solar_rad": data["direct_radiation"]
        })
        
        df['ds'] = df['ds'].dt.tz_localize(None)
        all_weather_dfs.append(df)
        
    return pd.concat(all_weather_dfs, ignore_index=True)

@app.get("/")
def home():
    return {"status": "online", "message": "API Global de Forecasting lista."}

@app.post("/predict")
def predict(request: PredictRequest):
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Modelo no disponible.")

        if request.country not in COUNTRY_HUBS:
            raise HTTPException(status_code=400, detail=f"País no soportado: {request.country}")

        # 1. 🎯 Plantilla del futuro que necesita el modelo
        expected_df = model.make_future_dataframe(h=request.horizon)

        # 2. 🌤️ Obtención de clima
        try:
            weather_df = get_broad_weather_europe()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error en API clima: {str(e)}")

        # 3. 🧩 Cruce y LIMPIEZA DE NULOS (Fix de UserWarnings)
        X_df = pd.merge(expected_df, weather_df, on=['unique_id', 'ds'], how='left')
        
        # Ordenamos por tiempo para asegurar que el ffill sea coherente
        X_df = X_df.sort_values(['unique_id', 'ds'])
        
        # Rellenamos nulos: primero hacia adelante y luego hacia atrás por si el fallo es al inicio
        cols_clima = ['temperature', 'wind_speed', 'solar_rad']
        X_df[cols_clima] = X_df.groupby('unique_id')[cols_clima].ffill().bfill()
        
        # Última defensa: si persiste algún nulo (caso extremo), rellenar con 0 para evitar error del modelo
        X_df[cols_clima] = X_df[cols_clima].fillna(0)

        # 4. 🔮 Predicción
        forecast = model.predict(
            h=request.horizon, 
            level=request.levels,
            X_df=X_df 
        )

        # 5. 🧹 Filtrado por país y formato de respuesta
        if isinstance(forecast, pd.DataFrame):
            # Filtramos solo el país solicitado
            forecast_filtered = forecast[forecast['unique_id'] == request.country].copy()
            
            # Formatear fecha para JSON
            if 'ds' in forecast_filtered.columns:
                forecast_filtered['ds'] = forecast_filtered['ds'].dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            result = forecast_filtered.reset_index(drop=True).to_dict(orient="records")
        else:
            result = forecast.tolist()

        return {
            "status": "success",
            "country": request.country,
            "horizon": request.horizon,
            "data": result
        }

    except Exception as e:
        print(f"❌ Error en inferencia: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallo interno: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Nota: uvicorn.run(app, ...) es preferible a pasar el string en entornos locales simples
    uvicorn.run(app, host="0.0.0.0", port=8000)