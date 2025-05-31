import os
import sys
from dotenv import load_dotenv
from celery import Celery

# Set paths before any imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

load_dotenv()  # Load .env after setting sys.path if needed

from celery import shared_task
from src.trademaster.trading_bot import TradeMaster

@shared_task
def run_trade_task():
    trade = TradeMaster()
    result = trade.make_some_money()
    print("Result from make_some_money:", result)