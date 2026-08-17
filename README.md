# LinkPlease

LinkPlease is a reliable Instagram-style automation backend built with FastAPI, SQLAlchemy, SQLite, and asynchronous background processing.

## Features

- Keyword-based comment automation
- Automatic DM creation for matching comments
- Duplicate event protection
- Duplicate DM protection using user + rule
- HMAC-SHA256 webhook signature verification
- Background DM processing
- Retry handling for temporary PseudoGram failures
- Rate limiting for PseudoGram API requests
- Idempotent DM sending
- Deleted-comment cancellation
- Delivery-status reconciliation
- Live DM statistics
- Startup recovery of queued DM jobs

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- HTTPX
- Uvicorn
- PseudoGram Mock API

## API Endpoints

### Health Check

GET /health

Returns:

{
  "status": "ok"
}

### Create Rule

POST /rules

Example request:

{
  "keyword": "PRICE",
  "dm_message": "Here is your price information!"
}

### Webhook

POST /webhook

The webhook endpoint receives PseudoGram events and verifies the HMAC-SHA256 signature before processing them.

### Statistics

GET /stats

Returns live DM statistics:

{
  "sent": 0,
  "failed": 0,
  "queued": 0,
  "duplicates_blocked": 0
}

## Webhook Processing Flow

PseudoGram Webhook
        |
        v
HMAC Signature Verification
        |
        v
Duplicate Event Check
        |
        v
Persist Event
        |
        v
Match Keyword Rules
        |
        v
Create Persistent DM Job
        |
        v
In-Memory Queue
        |
        v
Background DM Worker
        |
        v
Rate Limiter + Retry Logic
        |
        v
PseudoGram API
        |
        v
Delivery Reconciliation

## Reliability

### Webhook Security

Incoming webhook requests use HMAC-SHA256 signatures.

The signature is calculated from the raw request body using the PseudoGram API key and compared using a constant-time comparison.

Invalid signatures return:

401 Unauthorized

### Duplicate Events

Every webhook event has a unique event_id.

Repeated deliveries of the same event are detected and do not create another DM job.

### Duplicate DMs

A database uniqueness constraint prevents multiple DMs from being created for the same:

rule + recipient_user_id

### Retry Handling

The worker handles:

- HTTP 400 as a permanent failure
- HTTP 429 using Retry-After
- HTTP 500 as a temporary failure with retry/backoff

An idempotency key is sent with each DM request.

### Deleted Comments

When a comment.deleted event is received, an existing queued or sending DM for that comment is cancelled.

### Rate Limiting

The worker uses a rolling-window rate limiter to respect the configured PseudoGram API request limit.

## Running the Application

Activate the virtual environment:

.\venv\Scripts\Activate.ps1

Start the server:

python run.py

The API runs on:

http://127.0.0.1:8000

## Environment Variables

Create a .env file based on .env.example.

Important configuration includes:

PSEUDOGRAM_API_KEY
PSEUDOGRAM_BASE_URL
DATABASE_URL
MAX_RETRIES
INITIAL_RETRY_DELAY
RATE_LIMIT_REQUESTS
RATE_LIMIT_WINDOW_SECONDS
DELIVERY_CHECK_INTERVAL_SECONDS
DELIVERY_MAX_ATTEMPTS

Do not commit .env because it contains the API key.

## Testing

The project includes regression and load-testing scripts for:

- Webhook signature verification
- Duplicate event handling
- Retry behavior
- Deleted comments
- Rate limiting
- C3 load testing

The main regression and load-testing scripts are located in the project root.

### C3 Load Test Result

The final clean C3 load test processed 500 concurrent webhook events successfully.

Total events: 500
Successful: 500
Failed: 0
Time taken: 3.93 seconds
Within 10 seconds: True

## Known Limitations

See FAILURES.md for the documented failure modes and remaining edge cases.

## Project Structure

LinkPlease/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rules.py
│   │   ├── stats.py
│   │   └── webhook.py
│   │
│   ├── clients/
│   │   ├── __init__.py
│   │   └── pseudogram_client.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dm.py
│   │   ├── event.py
│   │   ├── rule.py
│   │   └── stats.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── dm_repository.py
│   │   ├── event_repository.py
│   │   └── rule_repository.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── delivery_service.py
│   │   ├── dm_service.py
│   │   ├── duplicate_service.py
│   │   ├── event_service.py
│   │   ├── rule_service.py
│   │   ├── stats_service.py
│   │   
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py
│   │   ├── retry.py
│   │   └── signature.py
│   │
│   └── workers/
│       ├── __init__.py
│       ├── dm_worker.py
│       └── queue.py
│
├── tests/
│   ├── __init__.py
│   ├── test_deleted_comments.py
│   ├── test_delivery.py
│   ├── test_duplicates.py
│   ├── test_load.py
│   ├── test_rate_limit.py
│   ├── test_retry.py
│   ├── test_rules.py
│   ├── test_signature.py
│   └── test_webhook.py
│
├── test_valid_webhook.py
├── test_c1_retry.py
├── test_c2_deleted.py
├── test_c2_regression.py
├── test_c3_load.py
├── test_c3_rate_limiter.py
│
├── .env.example
├── .gitignore
├── FAILURES.md
├── README.md
├── requirements.txt
└── run.py