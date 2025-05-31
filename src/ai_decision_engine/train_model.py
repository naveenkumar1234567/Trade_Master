# src/ai_decision_engine/train_model.py

import os
import sys
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.trademaster.broker import AngelOneClient  # Corrected import
from src.trademaster.data_collector import DataCollector

def train_and_save_model():
    # Initialize AngelOneClient
    logger.info("Initializing AngelOneClient...")
    try:
        client = AngelOneClient()
        client._initialize_smart_api()
        logger.info("AngelOneClient initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AngelOneClient: {e}")
        return

    # Initialize DataCollector with the SmartConnect instance and the client for instrument list
    logger.info("Initializing DataCollector...")
    dc = DataCollector(client.smart_api, client)

    # Fetch instrument list
    try:
        dc.get_instruments()  # Calls AngelOneClient.get_instrument_list()
        logger.info(f"Instrument list fetched with {len(dc.instrument_list)} instruments")
    except ValueError as e:
        logger.error(f"Failed to fetch instrument list: {e}")
        return

    # Fetch NSE equity symbols
    try:
        symbols = client.fetch_all_nse_equity_symbols()
        logger.info(f"Total NSE equity symbols fetched: {len(symbols)}")
        if not symbols:
            logger.error("No NSE equity symbols fetched")
            return
        logger.debug(f"Sample symbols: {symbols[:5]}")
    except Exception as e:
        logger.error(f"Failed to fetch NSE equity symbols: {e}")
        return

    # Fetch training data
    logger.info("Fetching training data using DataCollector...")
    try:
        df, labels = dc.get_training_data(symbols)
        if df is None or df.empty:
            logger.error("No data returned from DataCollector")
            return
        logger.info(f"Data shape: {df.shape}")
        logger.debug(f"Sample data:\n{df.head().to_string()}")
    except Exception as e:
        logger.error(f"Exception during data collection: {e}")
        return

    # Verify required features
    required_features = ["open", "high", "low", "close", "volume", "gap"]
    for feature in required_features:
        if feature not in df.columns:
            logger.error(f"Missing expected feature column: {feature}")
            return

    # Prepare data for training
    X = df[required_features]
    y = labels

    # Train model
    logger.info("Training model...")
    try:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        logger.info("Model training complete")
    except Exception as e:
        logger.error(f"Failed to train model: {e}")
        return

    # Save model with both pickle and joblib
    save_path_pickle = os.path.join(os.path.dirname(__file__), "ai_trade_model.pkl")
    save_path_joblib = os.path.join(os.path.dirname(__file__), "ai_trade_model.joblib")

    try:
        with open(save_path_pickle, "wb") as f:
            pickle.dump(model, f)
        joblib.dump(model, save_path_joblib)
        logger.info(f"Model saved to:\n - {save_path_pickle}\n - {save_path_joblib}")
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        return

if __name__ == "__main__":
    train_and_save_model()