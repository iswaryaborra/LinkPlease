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
        print(
            "WEBHOOK SIGNATURE DEBUG: "
            "header missing"
        )
        return False

    if not signature_header.startswith("sha256="):
        print(
            "WEBHOOK SIGNATURE DEBUG: "
            "invalid prefix"
        )
        return False

    received_signature = (
        signature_header[len("sha256="):].strip()
    )

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    is_valid = hmac.compare_digest(
        received_signature,
        expected_signature,
    )

    print(
        "WEBHOOK SIGNATURE DEBUG:",
        "body_sha256=",
        hashlib.sha256(raw_body).hexdigest(),
        "received_prefix=",
        received_signature[:16],
        "expected_prefix=",
        expected_signature[:16],
        "valid=",
        is_valid,
    )

    return is_valid