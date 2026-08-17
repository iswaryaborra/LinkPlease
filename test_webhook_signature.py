import hashlib
import hmac
import json
import os

from dotenv import load_dotenv


load_dotenv()


secret = os.getenv("PSEUDOGRAM_API_KEY")


payload = {
    "event_id": "evt_regression_a_001",
    "event_type": "comment.created",
    "sent_at": "2026-08-17T01:40:00Z",
    "data": {
        "comment_id": "cmt_c1_regression_001",
        "post_id": "post_regression_a_001",
        "text": "PRICE please",
        "created_at": "2026-08-17T01:39:59Z",
        "from": {
            "user_id": "usr_regression_a_001",
            "username": "regression_test_user"
        }
    }
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


print("BODY:")
print(raw_body.decode())


print("\nSIGNATURE:")
print(f"sha256={signature}")