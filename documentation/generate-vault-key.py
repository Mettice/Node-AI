#!/usr/bin/env python3
"""
Generate a secure encryption key for the secrets vault.

This generates a 32-byte (256-bit) random key in hex format,
which is required for VAULT_ENCRYPTION_KEY.
"""

import secrets

# Generate 32 random bytes (256 bits)
key_bytes = secrets.token_bytes(32)

# Convert to hex string (64 characters)
key_hex = key_bytes.hex()

print("=" * 60)
print("VAULT_ENCRYPTION_KEY")
print("=" * 60)
print(key_hex)
print("=" * 60)
print()
print("Copy this value and add it to Vercel Environment Variables:")
print("Key: VAULT_ENCRYPTION_KEY")
print(f"Value: {key_hex}")
print()
print("⚠️  IMPORTANT: Keep this key secret and secure!")
print("   If you lose it, you cannot decrypt existing secrets.")
print("=" * 60)

