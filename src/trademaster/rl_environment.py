# src/trademaster/rl_environment.py (updated with logging)

import gymnasium as gym
import numpy as np
import pandas as pd
from typing import Dict, List

class StockTradingEnv(gym.Env):
    def __init__(self, data: Dict[str, pd.DataFrame], initial_balance: float = 100000):
        super(StockTradingEnv, self).__init__()
        self.data = data  # Dictionary of ticker: DataFrame (from DataCollector)
        self.tickers = list(data.keys())
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.shares_held = {ticker: 0 for ticker in self.tickers}
        self.current_step = 0
        self.max_steps = min([df.shape[0] for df in data.values()]) - 1

        # Action space: [buy, sell, hold] for each ticker
        self.action_space = gym.spaces.MultiDiscrete([3] * len(self.tickers))
        # Observation space: [balance, shares_held, open, high, low, close, volume, gap] for each ticker
        obs_shape = (len(self.tickers) * 7 + 1,)  # 7 features per ticker + balance
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=obs_shape, dtype=np.float32)
        print(f"[INFO] Environment initialized with {self.max_steps} steps (one step per candle)")

    def reset(self, seed=None, options=None):
        self.balance = self.initial_balance
        self.shares_held = {ticker: 0 for ticker in self.tickers}
        self.current_step = 0
        return self._get_observation(), {}

    def step(self, action):
        assert self.action_space.contains(action), f"Invalid action: {action}"
        reward = 0
        transaction_cost = 0.001  # 0.1% per trade

        # Process actions for each ticker
        for ticker_idx, act in enumerate(action):
            ticker = self.tickers[ticker_idx]
            current_price = self.data[ticker].iloc[self.current_step]["close"]

            if act == 0:  # Buy
                shares_to_buy = self.balance // current_price
                cost = shares_to_buy * current_price
                self.balance -= cost * (1 + transaction_cost)
                self.shares_held[ticker] += shares_to_buy
            elif act == 1:  # Sell
                shares_to_sell = self.shares_held[ticker]
                revenue = shares_to_sell * current_price
                self.balance += revenue * (1 - transaction_cost)
                self.shares_held[ticker] = 0
                reward += revenue - cost if 'cost' in locals() else 0
            # act == 2: Hold (no action)

        self.current_step += 1
        done = self.current_step >= self.max_steps
        truncated = False
        if self.balance <= 0:
            done = True
            reward -= 1000  # Penalty for bankruptcy

        # Calculate portfolio value as reward
        portfolio_value = self.balance + sum(
            self.shares_held[ticker] * self.data[ticker].iloc[self.current_step]["close"]
            for ticker in self.tickers if self.current_step < self.max_steps
        )
        reward = portfolio_value - self.initial_balance if not done else reward

        return self._get_observation(), reward, done, truncated, {}

    def _get_observation(self):
        obs = [self.balance]
        for ticker in self.tickers:
            row = self.data[ticker].iloc[self.current_step]
            obs.extend([
                self.shares_held[ticker],
                row["open"], row["high"], row["low"], row["close"],
                row["volume"], row["gap"]
            ])
        return np.array(obs, dtype=np.float32)