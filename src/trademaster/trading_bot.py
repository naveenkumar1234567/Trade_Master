import datetime as dt
import time
import pandas as pd
import os
import sys

# Add src path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import tickers and strategy base class
from src.trademaster.data_loader import ORB_TICKERS
from src.trademaster.strategies.opening_range_breakout import OpeningRangeBreakout


class TradeMaster(OpeningRangeBreakout):
    def make_some_money(self) -> None:
        print('Lets make some money')
        starttime = time.time()
        hi_lo_prices = {}

        # Step 1: Load instrument list and SmartAPI instance
        self._load_instrument_list()
        self._initialize_smart_api()

        # Step 2: Fetch historical 5-minute candles ending at 09:20
        data_0920 = self.hist_data_0920(
            ORB_TICKERS, 4, 'FIVE_MINUTE', self.instrument_list
        )

        # Step 3: Extract high and low of first 5-min candle for each ticker
        for ticker in ORB_TICKERS:
            df = data_0920.get(ticker)
            if df is None or df.empty:
                print(f"WARNING: No data for ticker {ticker}, skipping.")
                continue
            hi_lo_prices[ticker] = [
                df['high'].iloc[-1],
                df['low'].iloc[-1],
            ]

        df = pd.DataFrame.from_dict(hi_lo_prices)
        print(df)

        # Step 4: Run strategy loop until 3:00 PM
        while dt.datetime.now() < dt.datetime.strptime(
            dt.datetime.now().strftime('%Y-%m-%d') + ' 15:00', '%Y-%m-%d %H:%M'
        ):
            print('starting passthrough at {}'.format(dt.datetime.now()))
            try:
                # Fetch current positions
                position_resp = self.smart_api.position()
                print("Position API Response:", position_resp)
                positions = pd.DataFrame(position_resp.get('data', []))

                # Fetch open orders
                open_orders = self.get_open_orders()

                # Execute strategy
                self.orb_strat(ORB_TICKERS, hi_lo_prices, positions, open_orders)

            except Exception as e:
                print(f"Exception during passthrough: {e}")

            # Sleep until next 5-minute interval
            time.sleep(300 - ((time.time() - starttime) % 300.0))

        print('see you tomorrow')
