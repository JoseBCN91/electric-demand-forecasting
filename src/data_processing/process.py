import os
import pandas as pd

def process_data():
    input_path = "data/processed/features.parquet"
    output_path = "data/processed/features_clean.parquet"
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encontraron datos crudos en {input_path}")
        return

    print("⚙️ [Procesamiento] Cargando datos raw...")
    df = pd.read_parquet(input_path)
    
    print("🧹 [Procesamiento] Ajustando a frecuencia HORARIA y limpiando nulos...")
    df['ds'] = pd.to_datetime(df['ds'])
    
    # 1. Eliminar duplicados exactos
    df = df.drop_duplicates(subset=['unique_id', 'ds'])
    
    # 2. Resampleo seguro manteniendo TODAS las columnas (Demanda y Clima)
    df = df.set_index('ds')
    
    # Agrupamos por país (unique_id), resampleamos a 1 hora ('h') y hacemos la media.
    # Al no aislar ['y'], Pandas aplica la media a todas las columnas numéricas.
    df_clean = (
        df.groupby('unique_id')
        .resample('h')
        .mean()
    )
    
    # 3. Rellenar huecos (Forward Fill y luego Backward Fill)
    df_clean = df_clean.ffill().bfill().reset_index()

    # 4. Limpieza final de seguridad
    df_clean = df_clean.dropna(subset=['y'])
    
    # Reordenar columnas para mantener las buenas prácticas de Nixtla
    cols = ['unique_id', 'ds', 'y', 'temperature', 'wind_speed', 'solar_rad']
    # Solo seleccionamos las columnas que realmente existen (por si falta alguna)
    df_clean = df_clean[[c for c in cols if c in df_clean.columns]]

    # 5. Guardar
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_clean.to_parquet(output_path)
    
    print(f"✅ [Procesamiento] Datos limpios. Total: {len(df_clean)} registros HORARIOS.")
    print(df_clean.head(3))

if __name__ == "__main__":
    process_data()