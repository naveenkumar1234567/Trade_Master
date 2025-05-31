# src/ai_decision_engine/train_model.py (updated)

import os
import sys
import logging
from dotenv import load_dotenv
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.trademaster.broker import AngelOneClient
from src.trademaster.data_collector import DataCollector
from src.trademaster.rl_environment import StockTradingEnv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def train_rl_model():
    # Initialize AngelOneClient
    logger.info("Initializing AngelOneClient...")
    try:
        client = AngelOneClient()
        client._initialize_smart_api()
        logger.info("AngelOneClient initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AngelOneClient: {e}")
        return

    # Initialize DataCollector
    logger.info("Initializing DataCollector...")
    dc = DataCollector(client.smart_api, client)

    # Fetch instrument list
    try:
        dc.get_instruments()
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
    except Exception as e:
        logger.error(f"Failed to fetch NSE equity symbols: {e}")
        return

    # Test with a smaller subset for faster training
    symbols = symbols[:3]  # e.g., ['RELIANCE-EQ', 'TCS-EQ', 'INFY-EQ']
    logger.info(f"Using subset of symbols: {symbols}")

    # Fetch historical data (daily candles for 1 year)
    logger.info("Fetching historical data using DataCollector...")
    try:
        hist_data = dc.hist_data_0920(
            tickers=symbols,
            duration=365,  # 1 year of data
            interval="ONE_DAY",  # Daily candles
            instrument_list=dc.instrument_list
        )
        if not hist_data:
            logger.error("No historical data returned")
            return
        logger.info(f"Fetched data for {len(hist_data)} tickers")
    except Exception as e:
        logger.error(f"Exception during data collection: {e}")
        return

    # Create RL environment
    env = StockTradingEnv(hist_data)
    check_env(env)  # Validate the environment

    # Train PPO model
    logger.info("Training PPO model...")
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=3e-4, n_steps=2048)
    model.learn(total_timesteps=50000)  # Increased timesteps for swing trading
    # Save the model
    save_path = os.path.join(os.path.dirname(__file__), "ppo_stock_trading_model")
    model.save(save_path)
    logger.info(f"RL model saved to: {save_path}")

if __name__ == "__main__":
    train_rl_model()