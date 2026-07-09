"""Redis caching helper. Caches read-heavy metric queries under a short TTL."""
from __future__ import annotations

import functools
import hashlib
import json
import os
from typing import Callable

import redis

_client = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    socket_timeout=1,  # never let a slow cache stall the request
)

DEFAULT_TTL_S = 60


def _key(prefix: str, *parts: object) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str)
    digest = hashlib.sha1(raw.encode()).hexdigest()[:16]
    return f"sm:{prefix}:{digest}"


def cached(prefix: str, ttl: int = DEFAULT_TTL_S) -> Callable:
    """Cache-aside decorator: try Redis, fall through to the function, store."""

    def wrap(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            key = _key(prefix, args, kwargs)
            try:
                hit = _client.get(key)
                if hit is not None:
                    return json.loads(hit)
            except redis.RedisError:
                pass  # cache down: degrade to the DB, don't fail the request
            value = fn(*args, **kwargs)
            try:
                _client.setex(key, ttl, json.dumps(value, default=str))
            except redis.RedisError:
                pass
            return value

        return inner

    return wrap
