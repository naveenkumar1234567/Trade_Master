import os
from dotenv import load_dotenv
from pyotp import TOTP

# Load environment variables from .env file
load_dotenv()

class TradeMaster:
    def __init__(self):
        print(">>> Initializing TradeMaster")

        # Load environment variables
        self.api_key = os.getenv("API_KEY")
        self.client_id = os.getenv("CLIENT_ID")
        self.password = os.getenv("PASSWORD")
        self.token = os.getenv("TOKEN")

        # Print values for debugging
        print(">>> API_KEY:", self.api_key)
        print(">>> CLIENT_ID:", self.client_id)
        print(">>> PASSWORD:", self.password)
        print(">>> TOKEN fetched in TradeMaster:", self.token)

        # Validate values
        if not all([self.api_key, self.client_id, self.password, self.token]):
            raise ValueError("One or more environment variables are not set or empty. Please check your .env file.")

        # Generate TOTP
        self.totp = TOTP(self.token).now()
        print(">>> TOTP generated:", self.totp)

    def make_some_money(self):
        print(">>> Pretending to make some money...")
        # Placeholder for actual trading logic
        return "Money made successfully!"