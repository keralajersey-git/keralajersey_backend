import base64
import os
from dotenv import load_dotenv
import psycopg2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

load_dotenv()

import os
from dotenv import load_dotenv
import psycopg2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BLOB_WEBHOOK_PUBLIC_KEY = os.getenv("BLOB_WEBHOOK_PUBLIC_KEY")
BLOB_STORE_ID = os.getenv("BLOB_STORE_ID")


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg2.connect(DATABASE_URL)


def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    if not BLOB_WEBHOOK_PUBLIC_KEY:
        raise RuntimeError("BLOB_WEBHOOK_PUBLIC_KEY is not configured")
    if not signature_header:
        return False

    try:
        signature = base64.b64decode(signature_header)
    except Exception:
        return False

    public_key = load_pem_public_key(BLOB_WEBHOOK_PUBLIC_KEY.encode("utf-8"))
    if not isinstance(public_key, Ed25519PublicKey):
        raise RuntimeError("Unsupported webhook public key type")

    try:
        public_key.verify(signature, raw_body)
        return True
    except InvalidSignature:
        return False
BLOB_WEBHOOK_PUBLIC_KEY = os.getenv("BLOB_WEBHOOK_PUBLIC_KEY")
BLOB_STORE_ID = os.getenv("BLOB_STORE_ID")


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg2.connect(DATABASE_URL)


def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    if not BLOB_WEBHOOK_PUBLIC_KEY:
        raise RuntimeError("BLOB_WEBHOOK_PUBLIC_KEY is not configured")
    if not signature_header:
        return False

    try:
        signature = base64.b64decode(signature_header)
    except Exception:
        return False

    public_key = load_pem_public_key(BLOB_WEBHOOK_PUBLIC_KEY.encode("utf-8"))
    if not isinstance(public_key, Ed25519PublicKey):
        raise RuntimeError("Unsupported webhook public key type")

    try:
        public_key.verify(signature, raw_body)
        return True
    except InvalidSignature:
        return False
