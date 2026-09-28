"""Rate limiter configuration"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi import FastAPI

"""
    Limit configuration with count in-memory per process.
    Request parameter on the endpoint is required for the limit to be applied.
    
    Note: if the API is ever set to run as multiple workers, limitting must be
    configured to use redis for shared count between processes.
"""
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour"],
)

def register_rate_limiter(app: FastAPI) -> None:
    """Registers the limiter and its exception handler on the app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
