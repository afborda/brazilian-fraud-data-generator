"""
Redis Streams connection for SaaS streaming.

Writes events to a Redis Stream (XADD) so the API can read them
via XREAD and re-emit as SSE to the end user.

Each event is stored as a hash entry in the stream key:
    stream:{stream_id}  →  { data: "<json>" }

A counter key tracks total events sent:
    stream:{stream_id}:count  →  integer (INCRBY)

A status key allows external kill-switch:
    stream:{stream_id}:status  →  "running" | "stop"
"""

import json
import os
from typing import Any, Dict, List, Optional

from .base import ConnectionProtocol


class RedisStreamConnection(ConnectionProtocol):
    """
    Connection that writes events to a Redis Stream (XADD).

    Requires: pip install redis
    """

    name = "Redis Stream"

    def __init__(self):
        self._client = None
        self._stream_key: str = ""
        self._count_key: str = ""
        self._status_key: str = ""
        self._connected = False
        self._maxlen: int = 10_000
        self._batch: List[Dict[str, Any]] = []
        self._batch_size: int = 1
        self._pipe = None

    @classmethod
    def is_available(cls) -> bool:
        try:
            import redis  # noqa: F401
            return True
        except ImportError:
            return False

    def connect(
        self,
        redis_url: Optional[str] = None,
        stream_id: Optional[str] = None,
        maxlen: int = 10_000,
        batch_size: int = 50,
        **kwargs,
    ) -> None:
        """
        Connect to Redis and configure the target stream.

        Args:
            redis_url:  Redis connection URL (default: env REDIS_URL)
            stream_id:  Unique stream identifier (default: env STREAM_ID)
            maxlen:     Max entries kept in the stream (XTRIM MAXLEN ~)
            batch_size: Number of events to pipeline before flushing
        """
        if not self.is_available():
            raise ImportError(
                "redis is not installed. Install with: pip install redis"
            )

        import redis as _redis

        url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        sid = stream_id or os.environ.get("STREAM_ID", "default")

        self._client = _redis.Redis.from_url(url, decode_responses=True)
        self._stream_key = f"stream:{sid}"
        self._count_key = f"stream:{sid}:count"
        self._status_key = f"stream:{sid}:status"
        self._maxlen = maxlen
        self._batch_size = max(1, batch_size)
        self._connected = True

        # Mark stream as running
        self._client.set(self._status_key, "running", ex=86400)
        # Initialise counter
        self._client.setnx(self._count_key, 0)
        self._client.expire(self._count_key, 86400)

    # ── send / batch ─────────────────────────────────────────────────────

    def send(self, data: Dict[str, Any], **kwargs) -> bool:
        if not self._connected or self._client is None:
            return False

        try:
            # Check external kill-switch every 500 events (cheap GET)
            self._batch.append(data)

            if len(self._batch) >= self._batch_size:
                return self._flush()
            return True
        except Exception:
            return False

    def _flush(self) -> bool:
        """Pipeline-flush buffered events to Redis."""
        if not self._batch:
            return True
        try:
            pipe = self._client.pipeline(transaction=False)
            for evt in self._batch:
                pipe.xadd(
                    self._stream_key,
                    {"data": json.dumps(evt, default=str)},
                    maxlen=self._maxlen,
                    approximate=True,
                )
            pipe.incrby(self._count_key, len(self._batch))
            pipe.expire(self._count_key, 86400)
            pipe.execute()
            self._batch.clear()
            return True
        except Exception:
            self._batch.clear()
            return False

    def send_batch(self, records: List[Dict[str, Any]], **kwargs) -> int:
        ok = 0
        for r in records:
            if self.send(r):
                ok += 1
        self._flush()
        return ok

    def should_stop(self) -> bool:
        """Check if an external process requested a stop."""
        if not self._connected or self._client is None:
            return False
        try:
            val = self._client.get(self._status_key)
            return val == "stop"
        except Exception:
            return False

    # ── lifecycle ────────────────────────────────────────────────────────

    def close(self) -> None:
        self._flush()
        if self._client:
            try:
                self._client.set(self._status_key, "completed", ex=3600)
            except Exception:
                pass
            try:
                self._client.close()
            except Exception:
                pass
        self._connected = False

    def get_stats(self) -> Dict[str, Any]:
        """Return stream stats (for monitoring)."""
        if not self._connected or self._client is None:
            return {}
        try:
            length = self._client.xlen(self._stream_key)
            count = int(self._client.get(self._count_key) or 0)
            status = self._client.get(self._status_key) or "unknown"
            return {
                "stream_length": length,
                "total_events": count,
                "status": status,
            }
        except Exception:
            return {}
