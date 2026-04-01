import os
import yaml
import pandas as pd
import requests
from entsoe import EntsoePandasClient
import time
from src.utils.logger import data_logger

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
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    data_logger.info(f"Fetching weather for {len(hubs)} locations from {start_date} to {end_date}")
    
    for city, coords in hubs.items():
        try:
            params = {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "start_date": start_date,
                "end_date": end_date,
                "hourly": ["temperature_2m", "wind_speed_10m", "direct_radiation"],
                "timezone": "UTC"
            }
            
            data_logger.debug(f"Requesting weather for {city}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            weather_data = response.json()["hourly"]
            
            df = pd.DataFrame({
                "ds": pd.to_datetime(weather_data["time"]),
                "temperature": weather_data["temperature_2m"],
                "wind_speed": weather_data["wind_speed_10m"],
                "solar_rad": weather_data["direct_radiation"]
            })
            all_weather_dfs.append(df)
            data_logger.info(f"✅ Weather data loaded for {city}: {len(df)} records")
        except Exception as e:
            data_logger.error(f"Failed to fetch weather for {city}: {str(e)}")
            raise
        
    if not all_weather_dfs:
        data_logger.error("No weather data was collected for any location")
        raise ValueError("No weather data retrieved")
    
    df_combined = pd.concat(all_weather_dfs)
    df_mean = df_combined.groupby('ds').mean().reset_index()
    df_mean['ds'] = df_mean['ds'].dt.tz_localize(None)
    
    data_logger.info(f"Weather aggregation complete: {len(df_mean)} hourly records")
    return df_mean

def fetch_entsoe_in_chunks(client, country_code, start, end):
    """Descarga datos de ENTSO-E mes a mes para evitar errores de la API."""
    ts_list = []
    chunks = pd.date_range(start, end, freq='MS') 
    
    if len(chunks) == 0:
        chunks = [start]
    
    data_logger.info(f"Fetching ENTSOE data for {country_code} in {len(chunks)} chunks")
        
    for i in range(len(chunks)):
        chunk_start = chunks[i]
        chunk_end = chunks[i+1] if i+1 < len(chunks) else end
        
        if chunk_start >= chunk_end:
            continue
            
        try:
            data_logger.debug(f"Fetching {country_code} for month: {chunk_start.strftime('%Y-%m')}")
            ts = client.query_load(country_code, start=chunk_start, end=chunk_end)
            if isinstance(ts, pd.Series):
                df_chunk = ts.to_frame(name='y')
            else:
                df_chunk = pd.DataFrame({'y': ts.sum(axis=1)})
                
            ts_list.append(df_chunk)
            data_logger.debug(f"Loaded {len(df_chunk)} records for {chunk_start.strftime('%Y-%m')}")
            time.sleep(1)
        except Exception as e:
            data_logger.warning(f"Warning fetching {country_code} {chunk_start.strftime('%Y-%m')}: {str(e)}")
            continue

    if not ts_list:
        data_logger.error(f"No ENTSOE data retrieved for {country_code}")
        raise ValueError(f"No ENTSOE data could be downloaded for {country_code}")
        
    df_load = pd.concat(ts_list)
    df_load = df_load.reset_index()
    df_load.rename(columns={df_load.columns[0]: 'ds'}, inplace=True)
    df_load['ds'] = df_load['ds'].dt.tz_localize(None)
    df_load = df_load.drop_duplicates(subset=['ds'])
    df_load = df_load.resample('h', on='ds').mean().reset_index()
    
    data_logger.info(f"ENTSOE data for {country_code}: {len(df_load)} hourly records")
    return df_load

def run_ingestion():
    """Main ingestion pipeline: download ENTSOE load + weather data and save as parquet."""
    CONFIG_PATH = os.path.join("deployment", "config.yaml")
    OUTPUT_PATH = "data/processed/features.parquet"
    
    data_logger.info("Starting data ingestion pipeline...")
    
    # Try to load API key from environment first, then from config file
    api_key = os.environ.get("ENTSOE_API_KEY")
    
    if not api_key:
        data_logger.info("ENTSOE_API_KEY not in environment. Checking config.yaml...")
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    config = yaml.safe_load(f)
                    api_key = config.get('entsoe_api_key')
                data_logger.debug("API key loaded from config.yaml")
            except Exception as e:
                data_logger.error(f"Failed to read config.yaml: {str(e)}")
        else:
            data_logger.warning(f"Config file not found: {CONFIG_PATH}")

    if not api_key or api_key == "USE_ENV_VARIABLE":
        data_logger.error("ENTSOE API key not found. Set ENTSOE_API_KEY environment variable or update config.yaml")
        raise ValueError("Missing ENTSOE_API_KEY")

    try:
        data_logger.info("Initializing ENTSOE client...")
        client = EntsoePandasClient(api_key=api_key)
    except Exception as e:
        data_logger.error(f"Failed to initialize ENTSOE client: {str(e)}")
        raise
    
    # Set date range: 2 years of historical data, ending 3 days ago (for weather API limits)
    end = pd.Timestamp.now(tz='UTC').floor('h') - pd.Timedelta(days=3)
    start = end - pd.DateOffset(years=2) 
    
    start_date = start.strftime('%Y-%m-%d')
    end_date = end.strftime('%Y-%m-%d')

    data_logger.info(f"Ingestion period: {start_date} to {end_date} (2 years)")

    all_countries_data = []
    
    for country_code, hubs in COUNTRY_HUBS.items():
        data_logger.info(f"Processing country: {country_code}")
        
        try:
            # 1. Fetch ENTSOE load data
            data_logger.info(f"Downloading ENTSOE load data for {country_code}...")
            df_load = fetch_entsoe_in_chunks(client, country_code, start, end)
            
            # 2. Fetch weather data
            data_logger.info(f"Downloading weather data for {country_code}...")
            df_weather = fetch_weather_for_hubs(start_date, end_date, hubs)
            
            # 3. Merge and validate
            data_logger.debug(f"Merging datasets for {country_code}...")
            df_merged = pd.merge(df_load, df_weather, on='ds', how='inner')
            df_merged['unique_id'] = country_code
            df_merged = df_merged.dropna()
            cols = ['unique_id', 'ds', 'y', 'temperature', 'wind_speed', 'solar_rad']
            df_merged = df_merged[cols]
            
            all_countries_data.append(df_merged)
            data_logger.info(f"✅ {country_code}: {len(df_merged)} hourly records")
            
        except Exception as e:
            data_logger.error(f"Failed to process {country_code}: {str(e)}", exc_info=True)
            continue

    # 4. Save combined dataset
    if all_countries_data:
        df_final = pd.concat(all_countries_data, ignore_index=True)
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df_final.to_parquet(OUTPUT_PATH)
        
        data_logger.info(f"✅ Ingestion complete! Final dataset: {len(df_final)} records")
        data_logger.info(f"Output saved to: {OUTPUT_PATH}")
        return OUTPUT_PATH
    else:
        data_logger.error("❌ No data was successfully retrieved from any country")
        raise ValueError("Ingestion failed: no data collected")

if __name__ == "__main__":
    try:
        output_path = run_ingestion()
        data_logger.info(f"Pipeline succeeded! Output: {output_path}")
    except Exception as e:
        data_logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise
