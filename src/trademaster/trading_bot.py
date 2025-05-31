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
from src.ai_decision_engine.ai_decision_engine import AIDecisionEngine
from src.ai_decision_engine.news_fetcher import get_latest_news
from datetime import datetime, timedelta


class TradeMaster(OpeningRangeBreakout):
    def generate_dynamic_ticker_list(self):
        print("[INFO] Generating dynamic ticker list from Angel One instrument list")
        instrument_list = self.instrument_list
        nse_stocks = [i for i in instrument_list if i['exchange'] == 'NSE' and i['symbol'].endswith('-EQ')]

        volatile_stocks = []
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)

        for stock in nse_stocks:
            try:
                candles = self.fetch_candles(stock['symbol'].replace('-EQ', ''), "FIFTEEN_MINUTE", start_time, end_time)
                if candles is None or len(candles) < 2:
                    continue
                df = pd.DataFrame(candles)
                pct_change = ((df['close'].iloc[-1] - df['open'].iloc[0]) / df['open'].iloc[0]) * 100
                if abs(pct_change) > 1.5:
                    volatile_stocks.append(stock['symbol'].replace('-EQ', ''))
            except Exception as e:
                print(f"[WARN] Error calculating pct change for {stock['symbol']}: {e}")

        print(f"[INFO] Selected tickers: {volatile_stocks[:10]}")
        return volatile_stocks[:10]  # Limit to top 10 volatile stocks

    def make_some_money(self) -> None:
        print('Lets make some money')
        starttime = time.time()

        # Step 1: Load instrument list and SmartAPI instance
        self._load_instrument_list()
        self._initialize_smart_api()

        # Generate tickers dynamically
        dynamic_tickers = self.generate_dynamic_ticker_list()

        # Initialize AI decision engine
        ai_engine = AIDecisionEngine()

        # Step 2: Fetch multi-timeframe historical candles
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=3)

        multi_candle_data = {}
        for symbol in dynamic_tickers:
            multi_candle_data[symbol] = {
                "5m": self.fetch_candles(symbol, "FIVE_MINUTE", start_time, end_time),
                "15m": self.fetch_candles(symbol, "FIFTEEN_MINUTE", start_time, end_time),
                "1h": self.fetch_candles(symbol, "ONE_HOUR", start_time, end_time),
                "1d": self.fetch_candles(symbol, "ONE_DAY", start_time - timedelta(days=30), end_time),
                "1w": self.fetch_candles(symbol, "ONE_WEEK", start_time - timedelta(weeks=12), end_time)
            }

        # Step 3: Run AI model over candle data
        for symbol, candles_dict in multi_candle_data.items():
            decision = ai_engine.analyze(symbol, candles_dict)
            print(f"[AI Decision] {symbol}: {decision}")
            if decision == "BUY":
                self.place_order(symbol, action="BUY")
            elif decision == "SELL":
                self.place_order(symbol, action="SELL")

        # Step 4: Get high/low prices from initial 5-minute candles (for fallback ORB strategy)
        hi_lo_prices = {}
        data_0920 = self.hist_data_0920(dynamic_tickers, 4, 'FIVE_MINUTE', self.instrument_list)
        for ticker in dynamic_tickers:
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

        # Step 5: Run strategy loop until 3:00 PM
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

                # AI Decision Making Loop
                for ticker in dynamic_tickers:
                    try:
                        current_price = self.get_ltp(self.instrument_list, ticker)
                        df = self.get_recent_ohlcv(self.instrument_list, ticker, interval="FIVE_MINUTE", duration=20)

                        sentiment = ai_engine.predict_sentiment(ticker)
                        pattern = ai_engine.detect_pattern(df, ticker)
                        decision = ai_engine.make_trade_decision(df, sentiment, pattern)

                        print(f"[AI Decision] {ticker}: Sentiment={sentiment}, Pattern={pattern}, Decision={decision}")

                        if (
                            (positions.empty or f"{ticker}-EQ" not in positions['tradingsymbol'].values)
                            and (open_orders.empty or f"{ticker}-EQ" not in open_orders['tradingsymbol'].values)
                        ):
                            if decision == "BUY":
                                # self.place_cnc_order(self.instrument_list, ticker, "BUY", quantity=3)
                                pass
                            elif decision == "SELL":
                                # self.place_cnc_order(self.instrument_list, ticker, "SELL", quantity=3)
                                pass

                    except Exception as e:
                        print(f"AI decision error for {ticker}: {e}")

                # Execute fallback strategy
                self.orb_strat(dynamic_tickers, hi_lo_prices, positions, open_orders)

            except Exception as e:
                print(f"Exception during passthrough: {e}")

            time.sleep(300 - ((time.time() - starttime) % 300.0))

        print('see you tomorrow')

    def make_some_money(self) -> None:
        print('Lets make some money')
        starttime = time.time()

        # Step 1: Load instrument list and SmartAPI instance
        self._load_instrument_list()
        self._initialize_smart_api()

        # Initialize AI decision engine
        ai_engine = AIDecisionEngine()

        # Step 2: Fetch multi-timeframe historical candles
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=3)

        multi_candle_data = {}
        for symbol in ORB_TICKERS:
            multi_candle_data[symbol] = {
                "5m": self.fetch_candles(symbol, "FIVE_MINUTE", start_time, end_time),
                "15m": self.fetch_candles(symbol, "FIFTEEN_MINUTE", start_time, end_time),
                "1h": self.fetch_candles(symbol, "ONE_HOUR", start_time, end_time),
                "1d": self.fetch_candles(symbol, "ONE_DAY", start_time - timedelta(days=30), end_time),
                "1w": self.fetch_candles(symbol, "ONE_WEEK", start_time - timedelta(weeks=12), end_time)
            }

        # Step 3: Run AI model over candle data
        for symbol, candles_dict in multi_candle_data.items():
            decision = ai_engine.analyze(symbol, candles_dict)
            print(f"[AI Decision] {symbol}: {decision}")
            if decision == "BUY":
                self.place_order(symbol, action="BUY")
            elif decision == "SELL":
                self.place_order(symbol, action="SELL")

        # Step 4: Get high/low prices from initial 5-minute candles (for fallback ORB strategy)
        hi_lo_prices = {}
        data_0920 = self.hist_data_0920(ORB_TICKERS, 4, 'FIVE_MINUTE', self.instrument_list)
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

        # Step 5: Run strategy loop until 3:00 PM
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

                # AI Decision Making Loop
                for ticker in ORB_TICKERS:
                    try:
                        current_price = self.get_ltp(self.instrument_list, ticker)
                        df = self.get_recent_ohlcv(self.instrument_list, ticker, interval="FIVE_MINUTE", duration=20)

                        # Fetch company name dynamically from instrument list
                        company_name = self.instrument_list[
                            self.instrument_list["tradingsymbol"] == f"{ticker}-EQ"
                        ]["name"].values[0]

                        # Use company name to fetch latest news and sentiment
                        news_headline = get_latest_news(company_name)
                        sentiment = ai_engine.predict_sentiment(news_headline)

                        # Detect price pattern from chart image
                        pattern = ai_engine.detect_pattern(df, ticker)

                        # Final decision
                        decision = ai_engine.make_trade_decision(df, sentiment, pattern)

                        print(f"[AI Decision] {ticker}: News='{news_headline}', Sentiment={sentiment}, Pattern={pattern}, Decision={decision}")

                        # Place order if not already in position or open order
                        if (
                            (positions.empty or f"{ticker}-EQ" not in positions['tradingsymbol'].values)
                            and (open_orders.empty or f"{ticker}-EQ" not in open_orders['tradingsymbol'].values)
                        ):
                            if decision == "BUY":
                                self.place_cnc_order(self.instrument_list, ticker, "BUY", quantity=3)
                            elif decision == "SELL":
                                self.place_cnc_order(self.instrument_list, ticker, "SELL", quantity=3)

                    except Exception as e:
                        print(f"AI decision error for {ticker}: {e}")

                # Execute fallback ORB strategy
                self.orb_strat(ORB_TICKERS, hi_lo_prices, positions, open_orders)

            except Exception as e:
                print(f"Exception during passthrough: {e}")

            time.sleep(300 - ((time.time() - starttime) % 300.0))

        print('see you tomorrow')
        print(f"Total execution time: {time.time() - starttime:.2f} seconds")