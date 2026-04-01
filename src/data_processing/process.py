import os
import pandas as pd
from src.utils.logger import data_logger


def process_data():
    """
    Data processing pipeline:
    - Loads raw features from ingestion
    - Removes duplicates and resamples to hourly frequency
    - Fills missing values with forward/backward fill
    - Saves clean features for training
    """
    input_path = "data/processed/features.parquet"
    output_path = "data/processed/features_clean.parquet"
    
    data_logger.info("Starting data processing pipeline...")
    
    if not os.path.exists(input_path):
        data_logger.error(f"Input data not found: {input_path}")
        raise FileNotFoundError(f"Raw data missing at {input_path}")

    try:
        data_logger.info(f"Loading raw data from {input_path}...")
        df = pd.read_parquet(input_path)
    except Exception as e:
        data_logger.error(f"Failed to load parquet file: {str(e)}")
        raise
    
    data_logger.info(f"Loaded {len(df)} records from raw data")
    
    # Step 1: Convert timestamp and remove duplicates
    try:
        df['ds'] = pd.to_datetime(df['ds'])
        data_logger.debug("Converted ds column to datetime")
        
        initial_count = len(df)
        df = df.drop_duplicates(subset=['unique_id', 'ds'])
        data_logger.info(f"Removed {initial_count - len(df)} duplicate records")
    except Exception as e:
        data_logger.error(f"Failed to process timestamps: {str(e)}")
        raise
    
    # Step 2: Resample to hourly frequency
    try:
        data_logger.debug("Resampling data to hourly frequency...")
        df = df.set_index('ds')
        
        df_clean = (
            df.groupby('unique_id')
            .resample('h')
            .mean()
        )
        
        data_logger.info(f"Resampled to hourly frequency: {len(df_clean)} records")
    except Exception as e:
        data_logger.error(f"Failed during resampling: {str(e)}")
        raise
    
    # Step 3: Fill missing values
    try:
        data_logger.debug("Filling missing values with forward/backward fill...")
        df_clean = df_clean.ffill().bfill().reset_index()
        unfilled = df_clean[['temperature', 'wind_speed', 'solar_rad']].isna().sum().sum()
        data_logger.info(f"Missing values after fill: {unfilled}")
    except Exception as e:
        data_logger.error(f"Failed during missing value imputation: {str(e)}")
        raise

    # Step 4: Final validation and cleanup
    try:
        df_clean = df_clean.dropna(subset=['y'])
        
        # Ensure correct column order
        cols = ['unique_id', 'ds', 'y', 'temperature', 'wind_speed', 'solar_rad']
        df_clean = df_clean[[c for c in cols if c in df_clean.columns]]
        
        data_logger.info(f"Final dataset has {len(df_clean)} hourly records")
    except Exception as e:
        data_logger.error(f"Failed during final validation: {str(e)}")
        raise

    # Step 5: Save
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_clean.to_parquet(output_path, index=False)
        data_logger.info(f"✅ Processing complete! Saved to {output_path}")
        data_logger.info(f"Shape: {df_clean.shape}, Countries: {df_clean['unique_id'].nunique()}")
        return output_path
    except Exception as e:
        data_logger.error(f"Failed to save processed data: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        output = process_data()
        data_logger.info(f"Pipeline succeeded! Output: {output}")
    except Exception as e:
        data_logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise