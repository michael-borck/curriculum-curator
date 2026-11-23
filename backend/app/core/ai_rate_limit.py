"""A small per-user limiter for AI endpoints.

SlowAPI decorators require the request body parameter to be named `request`,
which most AI routes already use. A router-level dependency gives the same
protection without renaming those bodies. The limiter is process-local, like
SlowAPI's default in-memory storage; a shared Redis backend can replace it
later without changing callers.
"""

from __future__ import annotations

import time
from collections import deque
from threading import Lock

from fastapi import Depends, HTTPException, Request, status

from app.api import deps
from app.schemas.user import UserResponse  # noqa: TC001 - FastAPI resolves annotation at runtime
from app.utils.request_ip import get_client_ip

_WINDOW_SECONDS = 60
_MAX_REQUESTS = 30

_requests: dict[str, deque[float]] = {}
_lock = Lock()


def enforce_ai_rate_limit(
    request: Request,
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> None:
    now = time.monotonic()
    key = f"{current_user.id}:{get_client_ip(request)}"
    with _lock:
        bucket = _requests.setdefault(key, deque())
        while bucket and now - bucket[0] > _WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= _MAX_REQUESTS:
            retry = max(1, int(_WINDOW_SECONDS - (now - bucket[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many AI requests. Please wait a moment.",
                headers={"Retry-After": str(retry)},
            )
        bucket.append(now)
