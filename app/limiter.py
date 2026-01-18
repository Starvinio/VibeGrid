from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.exceptions import RateLimitError

def ratelimit_handler(e):
    raise RateLimitError(e.message)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    storage_options={},
    strategy="fixed-window",
    default_limits=["1000 per day", "300 per hour"],
    on_breach=ratelimit_handler
)