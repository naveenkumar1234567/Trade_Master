import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Read environment variables
# api_key = os.environ.get('API_KEY')
# client_id = os.environ.get('CLIENT_ID')
# password = os.environ.get('PASSWORD')
# token = os.environ.get('TOKEN')

api_key = "N46Ju7kE"
client_id = "AAAM842306"
password = 9742
token = os.environ.get('TOKEN')

# Debugging output (visible during startup)
print(">>> Config.py MODULE LOADED")
print("CONFIG: Loading environment variables...")
print("CONFIG: API_KEY =", api_key)
print("CONFIG: CLIENT_ID =", client_id)
print("CONFIG: PASSWORD =", password)
print("CONFIG: TOKEN =", token)
# Validation
if not all([api_key, client_id, password, token]):
    raise ValueError("One or more environment variables are not set or empty. Please check your .env file.")
