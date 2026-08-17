import hashlib
import hmac
import json
import os

import httpx
from dotenv import load_dotenv


load_dotenv()

SECRET = os.getenv("PSEUDOGRAM_API_KEY")
URL = "http://127.0.0.1:8000/webhook"


def make_request(payload):
    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = hmac.new(
        SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-PseudoGram-Signature": f"sha256={signature}",
    }

    response = httpx.post(
        URL,
        content=raw_body,
        headers=headers,
        timeout=10.0,
    )

    print("Status:", response.status_code)
    print("Response:", response.text)
    print()


comment_id = "cmt_regression_c2_001"

created_payload = {
    "event_id": "evt_regression_c2_created_001",
    "event_type": "comment.created",
    "sent_at": "2026-08-17T06:00:00Z",
    "data": {
        "comment_id": comment_id,
        "post_id": "post_regression_c2_001",
        "text": "PRICE please",
        "created_at": "2026-08-17T05:59:59Z",
        "from": {
            "user_id": "usr_regression_c2_001",
            "username": "c2_regression_user",
        },
    },
}


deleted_payload = {
    "event_id": "evt_regression_c2_deleted_001",
    "event_type": "comment.deleted",
    "sent_at": "2026-08-17T06:00:02Z",
    "data": {
        "comment_id": comment_id,
        "post_id": "post_regression_c2_001",
        "text": None,
        "created_at": "2026-08-17T05:59:59Z",
        "from": {
            "user_id": "usr_regression_c2_001",
            "username": "c2_regression_user",
        },
    },
}


print("=== COMMENT.CREATED ===")
make_request(created_payload)

print("=== COMMENT.DELETED ===")
make_request(deleted_payload)