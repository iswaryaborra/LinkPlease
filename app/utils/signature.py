import hashlib
import hmac


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    secret: str,
) -> bool:
    """
    Verify a PseudoGram webhook signature.
    """

    if not signature_header:
        print("WEBHOOK SIGNATURE DEBUG: header missing")
        return False

    print(
        "WEBHOOK SIGNATURE DEBUG:",
        "header_prefix=",
        repr(signature_header[:20]),
        "body_length=",
        len(raw_body),
    )

    if not signature_header.startswith("sha256="):
        print("WEBHOOK SIGNATURE DEBUG: invalid prefix")
        return False

    received_signature = signature_header[len("sha256="):].strip()

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
        "received_length=",
        len(received_signature),
        "expected_length=",
        len(expected_signature),
        "valid=",
        is_valid,
    )

    return is_valid