import pyotp
from dotenv import set_key

env_path = ".env"

# Generate a new base32 secret key
base32_secret = pyotp.random_base32()

# Store it in the .env file under TOKEN
set_key(env_path, "TOKEN", base32_secret)

print("Updated .env with base32 TOTP secret:", base32_secret)
