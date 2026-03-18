import os
import yaml
import pandas as pd
import requests
from entsoe import EntsoePandasClient
import time

COUNTRY_HUBS = {
    'ES': {
        "Madrid": {"lat": 40.4168, "lon": -3.7038},
        "Barcelona": {"lat": 41.3874, "lon": 2.1686},
        "Valencia": {"lat": 39.4699, "lon": -0.3774},
        "Sevilla": {"lat": 37.3891, "lon": -5.9845}
    },
    'FR': {
        "Paris": {"lat": 48.8566, "lon": 2.3522},
        "Marseille": {"lat": 43.2965, "lon": 5.3698},
        "Lyon": {"lat": 45.7640, "lon": 4.8357},
        "Toulouse": {"lat": 43.6047, "lon": 1.4442}
    },
    'DE': {
        "Berlin": {"lat": 52.5200, "lon": 13.4050},
        "Munich": {"lat": 48.1351, "lon": 11.5820},
        "Frankfurt": {"lat": 50.1109, "lon": 8.6821},
        "Hamburg": {"lat": 53.5511, "lon": 9.9937}
    },
    'IT': {
        "Rome": {"lat": 41.9028, "lon": 12.4964},
        "Milan": {"lat": 45.4642, "lon": 9.1900},
        "Naples": {"lat": 40.8518, "lon": 14.2681},
        "Turin": {"lat": 45.0703, "lon": 7.6869}
    }
}

def fetch_weather_for_hubs(start_date, end_date, hubs):
    """Descarga el clima histórico usando el endpoint ARCHIVE de Open-Meteo."""
    all_weather_dfs = []
    # 🎯 CAMBIO: Usamos el servidor de datos históricos
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    for city, coords in hubs.items():
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ["temperature_2m", "wind_speed_10m", "direct_radiation"],
            "timezone": "UTC"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        weather_data = response.json()["hourly"]
        
        df = pd.DataFrame({
            "ds": pd.to_datetime(weather_data["time"]),
            "temperature": weather_data["temperature_2m"],
            "wind_speed": weather_data["wind_speed_10m"],
            "solar_rad": weather_data["direct_radiation"]
        })
        all_weather_dfs.append(df)
        
    df_combined = pd.concat(all_weather_dfs)
    df_mean = df_combined.groupby('ds').mean().reset_index()
    df_mean['ds'] = df_mean['ds'].dt.tz_localize(None)
    
    return df_mean

def fetch_entsoe_in_chunks(client, country_code, start, end):
    """Descarga datos de ENTSO-E mes a mes para evitar errores de la API."""
    ts_list = []
    # Creamos bloques de tiempo mensuales
    chunks = pd.date_range(start, end, freq='MS') 
    
    if len(chunks) == 0:
        chunks = [start]
        
    for i in range(len(chunks)):
        chunk_start = chunks[i]
        # El fin del bloque es el inicio del siguiente, o el 'end' final
        chunk_end = chunks[i+1] if i+1 < len(chunks) else end
        
        # Evitar peticiones de 0 días si las fechas coinciden
        if chunk_start >= chunk_end:
            continue
            
        print(f"      🗓️ Mes: {chunk_start.strftime('%Y-%m')}...")
        try:
            ts = client.query_load(country_code, start=chunk_start, end=chunk_end)
            if isinstance(ts, pd.Series):
                df_chunk = ts.to_frame(name='y')
            else:
                df_chunk = pd.DataFrame({'y': ts.sum(axis=1)})
                
            ts_list.append(df_chunk)
            time.sleep(1) # Pausa por cortesía a la API
        except Exception as e:
            print(f"      ⚠️ Aviso en {chunk_start.strftime('%Y-%m')}: {str(e)}")
            continue

    if not ts_list:
        raise ValueError("No se pudieron descargar datos de ENTSO-E en ningún bloque.")
        
    df_load = pd.concat(ts_list)
    df_load = df_load.reset_index()
    df_load.rename(columns={df_load.columns[0]: 'ds'}, inplace=True)
    df_load['ds'] = df_load['ds'].dt.tz_localize(None)
    df_load = df_load.drop_duplicates(subset=['ds'])
    df_load = df_load.resample('h', on='ds').mean().reset_index()
    
    return df_load

def run_ingestion():
    CONFIG_PATH = os.path.join("src", "deployment", "config.yaml")
    OUTPUT_PATH = "data/processed/features.parquet"
    
    # 🎯 CAMBIO DE SEGURIDAD MLOps:
    # 1. Intentar leer desde variables de entorno (Para GitHub Actions)
    api_key = os.environ.get("ENTSOE_API_KEY")
    
    # 2. Si no existe en entorno, intentar leer del archivo yaml (Para tu PC local)
    if not api_key:
        print("ℹ️ Clave no encontrada en entorno. Buscando en config.yaml...")
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = yaml.safe_load(f)
                api_key = config.get('entsoe_api_key')
        else:
            print(f"❌ Error: No se encuentra {CONFIG_PATH} ni la variable de entorno ENTSOE_API_KEY")
            return

    # Si después de intentar ambos métodos no hay clave, abortamos
    if not api_key or api_key == "USE_ENV_VARIABLE":
        print("❌ Error: API key de ENTSO-E no encontrada o es inválida.")
        return

    # A partir de aquí, el código sigue igual
    client = EntsoePandasClient(api_key=api_key)
    
    # 🎯 CAMBIO: 2 AÑOS DE DATOS (Terminando hace 3 días por la API histórica de clima)
    end = pd.Timestamp.now(tz='UTC').floor('h') - pd.Timedelta(days=3)
    start = end - pd.DateOffset(years=2) 
    
    start_date = start.strftime('%Y-%m-%d')
    end_date = end.strftime('%Y-%m-%d')

    print(f"🚀 Iniciando descarga masiva de datos (2 Años): {start_date} a {end_date}")

    all_countries_data = []

    for country_code, hubs in COUNTRY_HUBS.items():
        print(f"\n======================================")
        print(f"🌍 Procesando datos para: {country_code}")
        print(f"======================================")
        
        # 1. ENTSO-E (Paginado mes a mes)
        print(f"⚡ [ENTSO-E] Descargando histórico paginado...")
        try:
            df_load = fetch_entsoe_in_chunks(client, country_code, start, end)
        except Exception as e:
            print(f"❌ Fallo crítico en ENTSO-E para {country_code}: {str(e)}")
            continue

        # 2. OPEN-METEO (Clima Histórico)
        print(f"🌤️ [Open-Meteo ARCHIVE] Descargando clima histórico...")
        try:
            df_weather = fetch_weather_for_hubs(start_date, end_date, hubs)
        except Exception as e:
            print(f"❌ Fallo crítico en Open-Meteo para {country_code}: {str(e)}")
            continue

        # 3. MERGE
        df_merged = pd.merge(df_load, df_weather, on='ds', how='inner')
        df_merged['unique_id'] = country_code
        df_merged = df_merged.dropna()
        cols = ['unique_id', 'ds', 'y', 'temperature', 'wind_speed', 'solar_rad']
        df_merged = df_merged[cols]
        
        all_countries_data.append(df_merged)
        print(f"✅ {country_code} listo: {len(df_merged)} registros horarios.")

    # 4. GUARDAR
    if all_countries_data:
        df_final = pd.concat(all_countries_data, ignore_index=True)
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df_final.to_parquet(OUTPUT_PATH)
        
        print(f"\n🚀 ✅ ¡Ingesta Histórica Completada!")
        print(f"📊 Dataset final contiene {len(df_final)} registros (~17.500 horas por país).")
    else:
        print("\n❌ Error crítico: No se pudieron descargar datos.")
if __name__ == "__main__":
    run_ingestion()
