from dotenv import load_dotenv
load_dotenv()  # ✅ Make sure this runs before any os.getenv calls
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
print(">>> Tasks.py MODULE LOADED")
from celery import shared_task
import os
from src.trademaster.trading_bot import TradeMaster



@shared_task
def run_trade_task():
    print(">>> Running Trade Task")
    trade = TradeMaster()
    result = trade.make_some_money()
    print("Result from make_some_money:", result)
