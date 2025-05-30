# celery_config.py
from celery import Celery
from celery.schedules import crontab

from dotenv import load_dotenv
load_dotenv()
import os
import sys
print(">>> Loading Celery Configuration")
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

print(">>> TASK MODULE LOADED")
app = Celery('trade_tasks',  backend='redis://localhost:6379/1', broker='redis://localhost:6379/0')


app.conf.update(
    timezone='Asia/Kolkata',  # Updated name
    enable_utc=True,
)
print(">>> step 222222222")
app.autodiscover_tasks(['cronjobs'])
print(">>> step 333333333")

app.conf.beat_schedule = {
    'run-trade-task-every-morning': {
        'task': 'cronjobs.tasks.run_trade_task',
        'schedule': crontab(minute=20, hour=9, day_of_week='mon-fri'),
    },
}
print(">>> step 444444444")