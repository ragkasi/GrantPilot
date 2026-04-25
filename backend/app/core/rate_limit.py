"""Simple in-memory rate limiter for auth endpoints.

Uses a sliding window algorithm with a thread-safe dict. No external
dependencies required. For high-traffic production deployments, replace
this with a Redis-backed implementation (e.g. slowapi + Redis).

Usage:
    from app.core.rate_limit import RateLimiter
    limiter = RateLimiter(max_requests=10, window_seconds=60)

    @router.post("/login")
    def login(request: Request, ...):
        limiter.check(request.client.host or "unknown", raise_on_limit=True)
        ...
"""
import threading
import time
from fastapi import HTTPException, Request, status


class RateLimiter:
    """Sliding-window rate limiter backed by an in-memory dict."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        # key -> list of timestamps
        self._buckets: dict[str, list[float]] = {}

    def _clean_old(self, timestamps: list[float], now: float) -> list[float]:
        cutoff = now - self.window_seconds
        return [t for t in timestamps if t > cutoff]

    def is_allowed(self, key: str) -> bool:
        """Return True if the request is within the rate limit."""
        now = time.monotonic()
        with self._lock:
            timestamps = self._clean_old(self._buckets.get(key, []), now)
            if len(timestamps) >= self.max_requests:
                self._buckets[key] = timestamps
                return False
            timestamps.append(now)
            self._buckets[key] = timestamps
            return True

    def check(self, key: str, raise_on_limit: bool = True) -> bool:
        """Check the rate limit; optionally raise HTTP 429 if exceeded.

        Does nothing when settings.rate_limit_enabled is False (test mode).
        """
        from app.core.config import settings
        if not settings.rate_limit_enabled:
            return True
        allowed = self.is_allowed(key)
        if not allowed and raise_on_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Too many requests. Maximum {self.max_requests} "
                    f"per {self.window_seconds} seconds."
                ),
                headers={"Retry-After": str(self.window_seconds)},
            )
        return allowed


def get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting common proxy headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


# Module-level limiters for auth endpoints
login_limiter = RateLimiter(max_requests=10, window_seconds=60)
register_limiter = RateLimiter(max_requests=5, window_seconds=3600)  # 5/hour
