import hashlib
import hmac


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    secret: str,
) -> bool:
    """
    Verify a PseudoGram webhook signature.

    PseudoGram sends:
        X-PseudoGram-Signature: sha256=<hex>

    The signature is HMAC-SHA256 of the raw request body
    using the PseudoGram API key as the secret.
    """

    if not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    received_signature = signature_header[len("sha256="):]

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        received_signature,
        expected_signature,
    )