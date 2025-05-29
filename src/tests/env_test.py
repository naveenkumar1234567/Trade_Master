# test_env.py
from dotenv import load_dotenv
import os

load_dotenv()

print("API_KEY:", os.getenv("API_KEY"))
print("TOKEN:", os.getenv("TOKEN"))
print("CLIENT_ID:", os.getenv("CLIENT_ID"))
print("PASSWORD:", os.getenv("PASSWORD"))
# Ensure all required environment variables are set 