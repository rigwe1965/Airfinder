import os
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

# In-memory storage is per worker process. Set RATELIMIT_STORAGE_URI (e.g. a Redis URL) in
# production so limits are shared across gunicorn workers and survive restarts.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=os.getenv('RATELIMIT_STORAGE_URI', 'memory://'),
)

mail = Mail()


def email_key():
    """Rate-limit key: the account being targeted (falls back to client IP).

    Stops credential stuffing / reset-mail spam against one account from many IPs.
    """
    data = request.get_json(silent=True)
    email = data.get('email') if isinstance(data, dict) else None
    if isinstance(email, str) and email.strip():
        return 'acct:' + email.strip().lower()[:255]
    return get_remote_address()
