import base64
import os



DEFAULT_KID = os.getenv('EMAIL_SECRETS_MASTER_KID', 'v1')


def _load_master_key():
    encoded = os.getenv('EMAIL_SECRETS_MASTER_KEY', '').strip()
    if not encoded:
        raise ValueError('EMAIL_SECRETS_MASTER_KEY is required for SMTP password encryption.')
    padded = encoded + '=' * (-len(encoded) % 4)
    key = base64.urlsafe_b64decode(padded.encode('utf-8'))
    if len(key) != 32:
        raise ValueError('EMAIL_SECRETS_MASTER_KEY must be a base64-encoded 32-byte key for AES-256-GCM.')
    return key


def encrypt_secret(plaintext):
    if plaintext is None:
        plaintext = ''
    key = _load_master_key()
    nonce = os.urandom(12)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return {
        'ciphertext': base64.urlsafe_b64encode(ciphertext).decode('utf-8'),
        'nonce': base64.urlsafe_b64encode(nonce).decode('utf-8'),
        'kid': DEFAULT_KID,
    }


def decrypt_secret(ciphertext, nonce):
    if not ciphertext or not nonce:
        return ''
    key = _load_master_key()
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    raw_ciphertext = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
    raw_nonce = base64.urlsafe_b64decode(nonce.encode('utf-8'))
    return aesgcm.decrypt(raw_nonce, raw_ciphertext, None).decode('utf-8')
