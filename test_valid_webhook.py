import hashlib
import hmac
import json
import os

import httpx
from dotenv import load_dotenv


load_dotenv()

secret = os.getenv("PSEUDOGRAM_API_KEY")

payload = {
    "event_id": "evt_regression_valid_002",
    "event_type": "comment.created",
    "sent_at": "2026-08-17T05:30:00Z",
    "data": {
        "comment_id": "cmt_regression_valid_002",
        "post_id": "post_regression_valid_002",
        "text": "PRICE please",
        "created_at": "2026-08-17T05:29:59Z",
        "from": {
            "user_id": "usr_regression_valid_002",
            "username": "regression_valid_user",
        },
    },
}

raw_body = json.dumps(
    payload,
    separators=(",", ":"),
).encode("utf-8")

signature = hmac.new(
    secret.encode("utf-8"),
    raw_body,
    hashlib.sha256,
).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-PseudoGram-Signature": f"sha256={signature}",
}

response = httpx.post(
    "http://127.0.0.1:8000/webhook",
    content=raw_body,
    headers=headers,
    timeout=10.0,
)

print("Status:", response.status_code)
print("Response:", response.text)