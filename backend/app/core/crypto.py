from cryptography.fernet import Fernet
import base64
import hashlib
from typing import Dict, Any

def _derive_fernet_key(secret: str) -> bytes:
    # Derive a 32-byte urlsafe base64 key from an arbitrary secret
    sha = hashlib.sha256(secret.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(sha)

def get_cipher(secret: str) -> Fernet:
    return Fernet(_derive_fernet_key(secret))

def encrypt_dict(data: Dict[str, Any], secret: str) -> Dict[str, str]:
    cipher = get_cipher(secret)
    enc: Dict[str, str] = {}
    for k, v in data.items():
        if v is None:
            continue
        # Ensure value is bytes
        s = str(v).encode('utf-8')
        enc[k] = cipher.encrypt(s).decode('utf-8')
    return enc

def decrypt_dict(data: Dict[str, str], secret: str) -> Dict[str, str]:
    cipher = get_cipher(secret)
    dec: Dict[str, str] = {}
    for k, v in data.items():
        if v is None:
            continue
        dec[k] = cipher.decrypt(v.encode('utf-8')).decode('utf-8')
    return dec

