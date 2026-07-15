import hashlib
import hmac

from app.utils.log import log


def compute_cryptobot_hmac(token: str, raw_body: bytes) -> str:
    """Compute CryptoBot webhook HMAC over the raw JSON body."""
    secret = hashlib.sha256(token.encode()).digest()
    return hmac.new(secret, raw_body, hashlib.sha256).hexdigest()


def verify_cryptobot_signature(raw_body: bytes, header_sig: str, token: str) -> bool:
    """Verify CryptoBot webhook signature."""
    try:
        expected = compute_cryptobot_hmac(token, raw_body)
        return hmac.compare_digest(expected, header_sig)
    except Exception as e:
        log.error(f"CryptoBot signature verification error: {e}")
        return False
