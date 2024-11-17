import secrets

# Generate a random secret key
secret_key = secrets.token_hex(32)  # Generates a 64-character hex string (256 bits)
print("Generated JWT Secret Key:", secret_key)
