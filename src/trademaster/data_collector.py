import time
import datetime as dt
from typing import List, Dict, Union
import pandas as pd
from tqdm import tqdm
import logging

from src.trademaster.utils import token_lookup

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data_collector.log")
    ]
)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, smart_api, client):
        self.smart_api = smart_api
        self.client = client
        self.instrument_list = None
        logger.info("DataCollector initialized with smart_api and client")

    def get_instruments(self):
        """Fetch instrument list from the provided client."""
        logger.info("Fetching instrument list")
        if hasattr(self.client, 'get_instrument_list'):
            try:
                self.instrument_list = self.client.get_instrument_list()
                if self.instrument_list is None or not self.instrument_list:
                    logger.error("Instrument list is None or empty after fetching")
                    raise ValueError("Instrument list is None or empty after fetching")
                logger.info(f"Fetched {len(self.instrument_list)} instruments")
                # Check for specific tickers
                test_tickers = ["FACT-EQ", "RADHIKAJWE-EQ", "FEDERALBNK-EQ", "JSWSTEEL-EQ"]
                for ticker in test_tickers:
                    ticker_clean = ticker.replace('-EQ', '') if ticker.endswith('-EQ') else ticker
                    found = any(
                        (instrument.get("symbol") == ticker or 
                         instrument.get("symbol") == f"{ticker_clean}-EQ" or
                         instrument.get("name") == ticker_clean or
                         instrument.get("name") == ticker) and
                        instrument.get("exch_seg") == "NSE" and
                        instrument.get("symbol", "").endswith("-EQ")
                        for instrument in self.instrument_list
                    )
                    logger.debug(f"Ticker {ticker} in instrument list: {found}")
                # Log sample instrument
                logger.debug(f"Sample instrument: {self.instrument_list[:3] if self.instrument_list else 'Empty'}")
            except Exception as e:
                logger.error(f"Failed to fetch instrument list: {e}", exc_info=True)
                raise
        else:
            logger.error("Client does not have get_instrument_list method")
            raise AttributeError("client does not have get_instrument_list method")

    def hist_data_0920(
        self,
        tickers: List[str],
        duration: int,
        interval: str,
        instrument_list: List[Dict[str, Union[str, int]]],
        exchange: str = "NSE",
    ) -> Dict[str, pd.DataFrame]:
        """Get historical data for swing trading with retry logic."""
        hist_data_tickers: Dict[str, pd.DataFrame] = {}
        total_data_size = 0  # Track total data size in memory

        if not instrument_list:
            logger.error("instrument_list is None or empty in hist_data_0920")
            raise ValueError("instrument_list is None or empty in hist_data_0920")

        for ticker in tqdm(tickers, desc="Fetching stock data"):
            try:
                time.sleep(0.4)
                logger.debug(f"Fetching data for ticker: {ticker}")
                token = token_lookup(ticker, instrument_list, exchange)
                if not token:
                    logger.warning(f"No token found for ticker: {ticker}, skipping")
                    continue
                logger.debug(f"Found token {token} for ticker: {ticker}")

                params = {
                    "exchange": exchange,
                    "symboltoken": str(token),
                    "interval": interval,
                    "fromdate": (dt.date.today() - dt.timedelta(days=duration)).strftime('%Y-%m-%d 00:00'),
                    "todate": (dt.date.today() - dt.timedelta(days=1)).strftime('%Y-%m-%d 23:59'),
                }
                logger.debug(f"API request params for {ticker}: {params}")

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        hist_data = self.smart_api.getCandleData(params)
                        logger.debug(f"API response for {ticker}: {hist_data}")

                        if not isinstance(hist_data, dict):
                            logger.error(f"Invalid hist_data type for {ticker}: {type(hist_data)} | Value: {hist_data}")
                            continue

                        if hist_data.get("status") is not True:
                            if "Invalid session" in hist_data.get("message", ""):
                                logger.warning(f"Session expired for {ticker}. Refreshing session...")
                                self.client.refresh_session()
                                self.smart_api = self.client.get_smart_api()
                                hist_data = self.smart_api.getCandleData(params)
                                logger.debug(f"Retry API response after session refresh for {ticker}: {hist_data}")
                                if hist_data.get("status") is not True:
                                    logger.error(f"Retry failed for {ticker}: {hist_data.get('message')}")
                                    continue
                            else:
                                logger.warning(f"API returned status false for {ticker}, message: {hist_data.get('message')}")
                                if attempt < max_retries - 1:
                                    logger.info(f"Retrying ({attempt + 1}/{max_retries}) for {ticker} after {2 ** attempt}s")
                                    time.sleep(2 ** attempt)
                                    continue
                                logger.error(f"Failed to fetch data for {ticker} after {max_retries} attempts")
                                break

                        data_list = hist_data.get("data")
                        if not isinstance(data_list, list) or not data_list:
                            logger.warning(f"Empty or invalid data for {ticker}. Full response: {hist_data}")
                            continue

                        try:
                            df_data = pd.DataFrame(
                                data_list,
                                columns=["date", "open", "high", "low", "close", "volume"],
                            )
                            df_data.set_index("date", inplace=True)
                            df_data.index = pd.to_datetime(df_data.index).tz_localize(None)
                            df_data["gap"] = ((df_data["open"] / df_data["close"].shift(1)) - 1) * 100
                            hist_data_tickers[ticker] = df_data
                            total_data_size += df_data.memory_usage(deep=True).sum() / (1024 ** 2)  # Size in MB
                            logger.info(f"Successfully fetched and processed data for {ticker} with {len(df_data)} rows. Total data size: {total_data_size:.2f} MB")
                            # Clear memory
                            del df_data
                            break
                        except Exception as e:
                            logger.error(f"Error creating DataFrame for {ticker}: {e}", exc_info=True)
                            continue

                    except Exception as e:
                        logger.error(f"Exception in API call for {ticker} (attempt {attempt + 1}/{max_retries}): {e}", exc_info=True)
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying ({attempt + 1}/{max_retries}) for {ticker} after {2 ** attempt}s")
                            time.sleep(2 ** attempt)
                        else:
                            logger.error(f"Failed to fetch data for {ticker} after {max_retries} attempts")
                            break

            except Exception as e:
                logger.error(f"Unexpected error processing ticker {ticker}: {e}", exc_info=True)
                continue

        logger.info(f"Completed fetching data for {len(hist_data_tickers)} out of {len(tickers)} tickers. Total data size: {total_data_size:.2f} MB")
        return hist_data_tickers

    def get_training_data(self, tickers: List[str], duration: int = 365, interval: str = "ONE_DAY"):
        """Fetch historical data and prepare training features for swing trading."""
        logger.info(f"Fetching training data for {len(tickers)} tickers with duration={duration} days, interval={interval}")
        if self.instrument_list is None or not self.instrument_list:
            logger.info("Instrument list not initialized, fetching now")
            self.get_instruments()

        logger.debug(f"Sample tickers: {tickers[:5] if tickers else 'Empty'}")
        data = self.hist_data_0920(
            tickers=tickers,
            duration=duration,
            interval=interval,
            instrument_list=self.instrument_list,
        )

        final_data = []
        labels = []
        total_data_size = 0

        try:
            for ticker, df in data.items():
                try:
                    if df.shape[0] >= 2:
                        row = df.iloc[-2]
                        label = 1 if row["close"] > row["open"] else 0
                        final_data.append(row[["open", "high", "low", "close", "volume", "gap"]].values)
                        labels.append(label)
                        total_data_size += df.memory_usage(deep=True).sum() / (1024 ** 2)
                        logger.debug(f"Processed training data for {ticker}: label={label}, features={row[['open', 'high', 'low', 'close', 'volume', 'gap']].to_dict()}")
                        # Clear memory
                        del df
                    else:
                        logger.warning(f"Insufficient data for {ticker}: {df.shape[0]} rows")
                except Exception as e:
                    logger.error(f"Error processing training data for {ticker}: {e}", exc_info=True)
                    continue
        except Exception as e:
            logger.error(f"Error processing training data: {e}", exc_info=True)
            raise

        logger.info(f"Training data shape: {len(final_data)} samples. Total data size: {total_data_size:.2f} MB")
        if not final_data:
            logger.warning("No training data collected. Check ticker list or API responses.")
        return pd.DataFrame(final_data, columns=["open", "high", "low", "close", "volume", "gap"]), pd.Series(labels)