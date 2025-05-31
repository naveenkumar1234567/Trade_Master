# src/trademaster/broker.py

import datetime as dt
import json
import os
import urllib.request
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from pyotp import TOTP
from SmartApi import SmartConnect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from src.trademaster.utils import token_lookup

class AngelOneClient:
    def __init__(self) -> None:
        self.api_key: str = os.environ.get('API_KEY')
        self.client_id: str = os.environ.get('CLIENT_ID')
        self.password: str = os.environ.get('PASSWORD')
        self.token: str = os.environ.get('TOKEN')
        logger.info(f"Token: {self.token}")
        self.totp: str = TOTP(self.token).now()
        logger.info(f">>> AngelOneClient MODULE LOADED {self.totp}")
        logger.info(f"CONFIG: TOTP = {self.totp}")
        self.smart_api = None
        self.instrument_list = None
        self._initialize_smart_api()

    def _initialize_smart_api(self) -> None:
        """Initialize the SmartAPI session."""
        if self.smart_api is None:
            self.smart_api = SmartConnect(self.api_key)
            try:
                data = self.smart_api.generateSession(self.client_id, self.password, self.totp)
                if data['status'] is False:
                    logger.error(f"Authentication failed: {data['message']}")
                    raise Exception(f"Authentication failed: {data['message']}")
                logger.info(f"SmartAPI session initialized. Feed Token: {self.smart_api.getfeedToken()}")
            except Exception as e:
                logger.error(f"Failed to initialize SmartAPI: {e}")
                self.smart_api = None
                raise

    def get_smart_api(self) -> SmartConnect:
        """Return the SmartConnect instance."""
        if self.smart_api is None:
            logger.error("SmartAPI session not initialized")
            raise ValueError("SmartAPI session not initialized")
        return self.smart_api

    def _load_instrument_list(self) -> None:
        """Load the instrument list."""
        if self.instrument_list is None:
            instrument_url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
            try:
                response = urllib.request.urlopen(instrument_url, timeout=10)
                self.instrument_list = json.loads(response.read())
                logger.info(f"Loaded {len(self.instrument_list)} instruments from {instrument_url}")
            except Exception as e:
                logger.error(f"Failed to load instrument list: {e}")
                self.instrument_list = []

    def get_instrument_list(self) -> List[Dict[str, Union[str, int]]]:
        """Public method to ensure instrument list is loaded and return it."""
        if self.instrument_list is None:
            logger.debug("Instrument list not loaded. Loading now...")
            self._load_instrument_list()
        if not self.instrument_list:
            logger.error("Instrument list is empty after loading")
        else:
            logger.info(f"Returning instrument list with {len(self.instrument_list)} items")
        return self.instrument_list

    def fetch_all_nse_equity_symbols(self) -> List[str]:
        """Fetch and return all NSE equity trading symbols."""
        try:
            if self.instrument_list is None:
                self._load_instrument_list()
            if not self.instrument_list:
                logger.error("Instrument list is empty")
                return []
            logger.debug("Sample item from instrument list:")
            logger.debug(self.instrument_list[0])
            equity_symbols = [
                item.get('symbol')
                for item in self.instrument_list
                if item.get('exch_seg') == 'NSE' and item.get('symbol', '').endswith('-EQ')
            ]
            logger.info(f"Fetched {len(equity_symbols)} NSE equity symbols")
            return equity_symbols
        except Exception as e:
            logger.error(f"Failed to fetch NSE equity symbols: {e}")
            return []