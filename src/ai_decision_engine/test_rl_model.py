# src/ai_decision_engine/test_rl_model.py (updated)

import os
import sys
import logging
import numpy as np
from dotenv import load_dotenv
from stable_baselines3 import PPO

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

def test_rl_model():
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

    # Use a small subset of symbols for testing
    symbols = symbols[:3]  # e.g., ['RELIANCE-EQ', 'TCS-EQ', 'INFY-EQ']
    logger.info(f"Testing with subset of symbols: {symbols}")

    # Fetch historical data (daily candles for 1 year)
    logger.info("Fetching historical data for testing...")
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
        logger.info(f"Fetched test data for {len(hist_data)} tickers")
    except Exception as e:
        logger.error(f"Exception during data collection: {e}")
        return

    # Create RL environment with test data
    env = StockTradingEnv(hist_data, initial_balance=100000)
    logger.info("Stock trading environment initialized for testing")

    # Load the trained PPO model
    model_path = os.path.join(os.path.dirname(__file__), "ppo_stock_trading_model")
    try:
        model = PPO.load(model_path)
        logger.info(f"PPO model loaded from: {model_path}")
    except Exception as e:
        logger.error(f"Failed to load PPO model: {e}")
        return

    # Test the model
    logger.info("Starting model testing...")
    obs, _ = env.reset()
    done = False
    total_reward = 0
    steps = 0
    actions_log = []

    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = env.step(action)
        total_reward += reward
        steps += 1

        # Log actions for each ticker
        action_desc = []
        for ticker_idx, act in enumerate(action):
            ticker = symbols[ticker_idx]
            if act == 0:
                action_desc.append(f"Buy {ticker}")
            elif act == 1:
                action_desc.append(f"Sell {ticker}")
            else:
                action_desc.append(f"Hold {ticker}")
        actions_log.append(f"Step {steps}: {', '.join(action_desc)}, Reward: {reward:.2f}")

        if done or truncated:
            break

    # Log the testing summary
    logger.info("Testing completed")
    logger.info(f"Total steps: {steps}")
    logger.info(f"Total reward (profit): {total_reward:.2f}")
    logger.info("Action history:")
    for log_entry in actions_log:
        logger.info(log_entry)

    # Calculate final portfolio value
    portfolio_value = env.balance + sum(
        env.shares_held[ticker] * env.data[ticker].iloc[env.current_step]["close"]
        for ticker in symbols if env.current_step < env.max_steps
    )
    logger.info(f"Initial balance: {env.initial_balance:.2f}")
    logger.info(f"Final portfolio value: {portfolio_value:.2f}")
    logger.info(f"Profit percentage: {((portfolio_value - env.initial_balance) / env.initial_balance) * 100:.2f}%")

if __name__ == "__main__":
    test_rl_model()