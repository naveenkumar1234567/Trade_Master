from typing import Dict, List, Optional, Union
import logging

# Configure logging for token_lookup
logger = logging.getLogger(__name__)

def token_lookup(
    ticker: str,
    instrument_list: List[Dict[str, Union[str, int]]],
    exchange: str = 'NSE',
) -> Optional[int]:
    """Lookup the token for a given ticker."""
    logger.debug(f"Looking up token for ticker: {ticker}, exchange: {exchange}")
    # Remove -EQ suffix for matching if present
    ticker_clean = ticker.replace('-EQ', '') if ticker.endswith('-EQ') else ticker
    for instrument in instrument_list:
        # Match on symbol or name, prioritizing symbol
        instrument_symbol = instrument.get('symbol', '')
        instrument_name = instrument.get('name', '')
        if (
            (instrument_symbol == ticker or 
             instrument_symbol == f"{ticker_clean}-EQ" or 
             instrument_name == ticker_clean or 
             instrument_name == ticker) and
            instrument.get('exch_seg') == exchange and
            instrument_symbol.endswith('-EQ')
        ):
            logger.debug(f"Found token for {ticker}: {instrument['token']} (symbol: {instrument_symbol}, name: {instrument_name})")
            return instrument['token']
    logger.warning(f"Token not found for ticker: {ticker}")
    logger.debug(f"Sample instrument list (first 3): {instrument_list[:3] if instrument_list else 'Empty'}")
    return None


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'