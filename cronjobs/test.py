import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
load_dotenv()

# Now import the function
from cronjobs.tasks import run_trade_task

# Call it directly like a normal function
run_trade_task.apply_async()

