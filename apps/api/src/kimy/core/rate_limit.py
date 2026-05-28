"""SlowAPI rate limiter wiring.

The limiter is shared by every endpoint that needs throttling. We key by
remote IP — JWT-based keying would require a request-time lookup we'd rather
avoid on hot paths. Defaults are intentionally conservative.

Setting ``RATE_LIMIT_DISABLED=1`` (used by pytest) disables all throttling.
"""
from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_DISABLED = os.environ.get("RATE_LIMIT_DISABLED", "").lower() in {"1", "true", "yes"}

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    enabled=not _DISABLED,
)


# Per-route limits — values match what the brief calls out.
LIMIT_LOGIN = "5/minute"
LIMIT_REGISTER = "5/minute"
LIMIT_REFRESH = "20/minute"
LIMIT_UPLOAD = "10/minute"
LIMIT_BULK = "5/minute"
