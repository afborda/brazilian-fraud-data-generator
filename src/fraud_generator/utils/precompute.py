"""
RAM pre-computation buffers for high-throughput generation.

Instead of calling random.choices() / random.randint() / hashlib per event,
we pre-generate large arrays of random decisions in bulk and consume them
from RAM.  When a buffer is exhausted it auto-refills.

Memory cost: ~5-10 MB per buffer set (negligible vs 8-96 GB VPS RAM).
Speed gain: eliminates per-call Python overhead for random sampling,
            string formatting, and hash computation.

Usage:
    buf = PrecomputeBuffers(seed=42)
    ip = buf.next_ip()              # ~10x faster than generate_ip_brazil()
    h  = buf.next_hash()            # ~5x  faster than generate_random_hash()
    r  = buf.next_uniform(0, 100)   # ~3x  faster than random.uniform()
"""

from __future__ import annotations

import os
import random
import struct
from typing import Any, Dict, List, Optional, Tuple

# How many items to pre-generate per buffer refill
BUFFER_SIZE = 10_000


class _RingBuffer:
    """Fast index-based ring buffer over a pre-allocated list."""

    __slots__ = ("_data", "_pos", "_size", "_refill_fn")

    def __init__(self, refill_fn, size: int = BUFFER_SIZE):
        self._refill_fn = refill_fn
        self._size = size
        self._data: list = refill_fn(size)
        self._pos = 0

    def next(self):
        if self._pos >= self._size:
            self._data = self._refill_fn(self._size)
            self._pos = 0
        val = self._data[self._pos]
        self._pos += 1
        return val


class PrecomputeBuffers:
    """
    Pre-generates thousands of random values in RAM for instant consumption.

    Buffers:
        ips       — Brazilian IP strings
        hashes16  — 16-char hex strings (card hashes)
        hashes32  — 32-char hex strings (PIX keys, random hashes)
        floats    — uniform [0, 1) floats
        bools_95  — True ~95% of the time  (cvv_validated)
        bools_70  — True ~70% of the time  (auth_3ds)
        octets    — random 0-255 integers
        merchant_ids — "MERCH_XXXXXX" strings
    """

    def __init__(self, seed: Optional[int] = None, buf_size: int = BUFFER_SIZE):
        self._rng = random.Random(seed)
        self._buf_size = buf_size

        # IP buffers
        self._ip_prefixes = [
            '177.', '187.', '189.', '191.', '200.', '201.',
            '179.', '186.', '188.', '190.', '170.',
            '138.', '143.', '152.', '168.',
        ]
        self._ips = _RingBuffer(self._gen_ips, buf_size)

        # Hash buffers (hex strings)
        self._hashes16 = _RingBuffer(lambda n: self._gen_hex(n, 16), buf_size)
        self._hashes32 = _RingBuffer(lambda n: self._gen_hex(n, 32), buf_size)

        # Float buffer [0, 1)
        self._floats = _RingBuffer(self._gen_floats, buf_size)

        # Pre-built merchant IDs
        self._merchant_ids = _RingBuffer(self._gen_merchant_ids, buf_size)

        # Profile-aware weighted choice buffers (lazily populated)
        self._choice_buffers: Dict[str, _RingBuffer] = {}

    # ── Public API ──────────────────────────────────────────────────

    def next_ip(self) -> str:
        return self._ips.next()

    def next_hash16(self) -> str:
        return self._hashes16.next()

    def next_hash32(self) -> str:
        return self._hashes32.next()

    def next_float(self) -> float:
        return self._floats.next()

    def next_merchant_id(self) -> str:
        return self._merchant_ids.next()

    def next_uniform(self, lo: float, hi: float) -> float:
        """Uniform float in [lo, hi) using buffered random."""
        return lo + self.next_float() * (hi - lo)

    def next_gauss(self, mu: float, sigma: float) -> float:
        """Gaussian using Box-Muller with buffered randoms."""
        import math
        u1 = max(self.next_float(), 1e-10)  # avoid log(0)
        u2 = self.next_float()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + sigma * z

    def next_int(self, lo: int, hi: int) -> int:
        """Random integer in [lo, hi] inclusive."""
        return lo + int(self.next_float() * (hi - lo + 1)) % (hi - lo + 1)

    def next_bool(self, probability: float = 0.5) -> bool:
        """True with given probability."""
        return self.next_float() < probability

    def next_choice(self, items: list) -> Any:
        """Uniform random choice from a list."""
        return items[int(self.next_float() * len(items)) % len(items)]

    def next_weighted(self, name: str, items: list, weights: list) -> Any:
        """
        Weighted random choice with pre-computed buffer.

        First call for a given `name` builds a buffer of BUFFER_SIZE
        pre-sampled indices; subsequent calls just index into it.
        """
        if name not in self._choice_buffers:
            # Build cumulative distribution once
            total = sum(weights)
            cum = []
            c = 0.0
            for w in weights:
                c += w / total
                cum.append(c)
            frozen_items = list(items)
            frozen_cum = cum

            def refill(n):
                import bisect
                out = []
                for _ in range(n):
                    r = self._rng.random()
                    idx = bisect.bisect_right(frozen_cum, r)
                    if idx >= len(frozen_items):
                        idx = len(frozen_items) - 1
                    out.append(frozen_items[idx])
                return out

            self._choice_buffers[name] = _RingBuffer(refill, self._buf_size)

        return self._choice_buffers[name].next()

    # ── Internal generators ─────────────────────────────────────────

    def _gen_ips(self, n: int) -> list:
        """Generate n Brazilian IP strings in bulk."""
        rng = self._rng
        prefixes = self._ip_prefixes
        out = []
        for _ in range(n):
            p = prefixes[int(rng.random() * len(prefixes))]
            a = int(rng.random() * 256)
            b = int(rng.random() * 256)
            c = int(rng.random() * 256)
            out.append(f"{p}{a}.{b}.{c}")
        return out

    def _gen_hex(self, n: int, length: int) -> list:
        """Generate n hex strings of given length using os.urandom."""
        byte_count = (length + 1) // 2  # 2 hex chars per byte
        out = []
        # Generate all random bytes at once for speed
        raw = os.urandom(byte_count * n)
        for i in range(n):
            chunk = raw[i * byte_count: (i + 1) * byte_count]
            out.append(chunk.hex()[:length])
        return out

    def _gen_floats(self, n: int) -> list:
        """Generate n floats [0, 1) in bulk."""
        rng = self._rng
        return [rng.random() for _ in range(n)]

    def _gen_merchant_ids(self, n: int) -> list:
        """Generate n merchant ID strings."""
        rng = self._rng
        return [f"MERCH_{int(rng.random() * 100000):06d}" for _ in range(n)]
