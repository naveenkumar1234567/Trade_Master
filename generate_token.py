import pyotp
from dotenv import set_key
import os
import time
import base64

env_path = ".env"

secret_key = "VFEYK4LXWYDIEMTYLRG7LFK2SA"  # Replace with your actual key
totp = pyotp.TOTP(secret_key)
token = totp.now()
token = int(token) 
print(token)

def int_to_base32(num: int) -> str:
    if not (100000 <= num <= 999999):
        raise ValueError("Input must be a 6-digit integer")

    # Convert integer to 4-byte big-endian binary representation
    byte_data = num.to_bytes(4, byteorder='big')

    # Base32 encode the byte data
    base32_encoded = base64.b32encode(byte_data)

    # Decode to string and strip padding
    return base32_encoded.decode('utf-8').rstrip('=')

base32 = int_to_base32(token)
print(base32)



# Store it in the .env file under TOKEN
# set_key(env_path, "TOKEN", base32)

def encode_int_to_base32(n: int) -> str:
    # Convert to minimal byte length needed
    byte_length = (n.bit_length() + 7) // 8 or 1
    b = n.to_bytes(byte_length, 'big')
    return base64.b32encode(b).decode('utf-8').rstrip('=')

def decode_base32_to_int(s: str) -> int:
    padded = s + '=' * ((8 - len(s) % 8) % 8)
    b = base64.b32decode(padded)
    return int.from_bytes(b, 'big')

# Test
original = token
encoded = encode_int_to_base32(original)
decoded = decode_base32_to_int(encoded)

print(f"Original: {original}")
print(f"Base32  : {encoded}")
print(f"Decoded : {decoded}")

set_key(env_path, "TOKEN", encoded)