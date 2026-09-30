"""
Encryption utilities for securing sensitive data
"""

import base64

from cryptography.fernet import Fernet
from django.conf import settings


class EncryptionUtil:
    """Utility class for encrypting and decrypting sensitive data"""

    def __init__(self):
        # Generate a key from the Django secret key
        # In production, use a dedicated encryption key stored securely
        key = base64.urlsafe_b64encode(
            settings.SECRET_KEY.encode()[:32].ljust(32, b"\0")
        )
        self.cipher_suite = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return ""
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return encrypted_data.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return ""
        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_data.decode()


# Create a global instance
encryption_util = EncryptionUtil()
