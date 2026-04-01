#!/usr/bin/env python
"""
Complete ML pipeline orchestrator: Data Ingestion → Processing → Model Training

This script coordinates the entire data pipeline in sequence with error handling
and logging. Run this to prepare data and train a new model from scratch.

Usage:
    python data/scripts/run_pipeline.py
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import data_logger, training_logger
from src.data_ingestion.ingest import run_ingestion
from src.data_processing.process import process_data
from src.training.train import train_model


def run_full_pipeline():
    """
    Execute complete ML pipeline:
    1. Data Ingestion (ENTSOE + Weather)
    2. Data Processing (Cleaning, Resampling)
    3. Model Training (Hyperparameter tuning + Training)
    """
    
    print("\n" + "="*70)
    print("🚀 STARTING FULL ML PIPELINE")
    print("="*70 + "\n")
    
    # ==========================================
    # PHASE 1: DATA INGESTION
    # ==========================================
    print("📥 PHASE 1: DATA INGESTION")
    print("-" * 70)
    start_time = time.time()
    
    try:
        data_logger.info("="*70)
        data_logger.info("STARTING DATA INGESTION PIPELINE")
        data_logger.info("="*70)
        
        ingest_output = run_ingestion()
        
        ingest_duration = time.time() - start_time
        data_logger.info(f"✅ Ingestion completed in {ingest_duration:.1f} seconds")
        print(f"✅ Data ingestion completed ({ingest_duration/60:.1f} min)\n")
        
    except Exception as e:
        data_logger.error(f"❌ Ingestion pipeline failed: {str(e)}", exc_info=True)
        print(f"❌ Ingestion failed: {str(e)}\n")
        return False

    # ==========================================
    # PHASE 2: DATA PROCESSING
    # ==========================================
    print("🔄 PHASE 2: DATA PROCESSING")
    print("-" * 70)
    start_time = time.time()
    
    try:
        data_logger.info("="*70)
        data_logger.info("STARTING DATA PROCESSING PIPELINE")
        data_logger.info("="*70)
        
        process_output = process_data()
        
        process_duration = time.time() - start_time
        data_logger.info(f"✅ Processing completed in {process_duration:.1f} seconds")
        print(f"✅ Data processing completed ({process_duration:.1f} sec)\n")
        
    except Exception as e:
        data_logger.error(f"❌ Processing pipeline failed: {str(e)}", exc_info=True)
        print(f"❌ Processing failed: {str(e)}\n")
        return False

    # ==========================================
    # PHASE 3: MODEL TRAINING
    # ==========================================
    print("🤖 PHASE 3: MODEL TRAINING")
    print("-" * 70)
    start_time = time.time()
    
    try:
        training_logger.info("="*70)
        training_logger.info("STARTING MODEL TRAINING PIPELINE")
        training_logger.info("="*70)
        
        train_model()
        
        train_duration = time.time() - start_time
        training_logger.info(f"✅ Training completed in {train_duration:.1f} seconds")
        print(f"✅ Model training completed ({train_duration/60:.1f} min)\n")
        
    except Exception as e:
        training_logger.error(f"❌ Training pipeline failed: {str(e)}", exc_info=True)
        print(f"❌ Training failed: {str(e)}\n")
        return False

    # ==========================================
    # SUCCESS
    # ==========================================
    print("="*70)
    print("✅ FULL PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\n📊 Pipeline Summary:")
    print(f"  • Ingestion: {ingest_duration/60:.1f} minutes")
    print(f"  • Processing: {process_duration:.0f} seconds")
    print(f"  • Training: {train_duration/60:.1f} minutes")
    print(f"  • Total: {(time.time() - start_time)/60:.1f} minutes")
    print("\n📁 Output files:")
    print(f"  • Raw data: data/processed/features.parquet")
    print(f"  • Clean data: data/processed/features_clean.parquet")
    print(f"  • Trained model: models/model_prod.pkl")
    print("\n" + "="*70 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = run_full_pipeline()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
