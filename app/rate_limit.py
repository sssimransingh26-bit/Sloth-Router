from __future__ import annotations

import time
from collections import defaultdict, deque

_hits: dict[str, deque[float]] = defaultdict(deque)


def allow(ip: str, limit: int, window_sec: int = 3600) -> bool:
    now = time.time()
    bucket = _hits[ip]
    while bucket and now - bucket[0] > window_sec:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True
