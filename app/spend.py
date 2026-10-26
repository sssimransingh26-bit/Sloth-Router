from __future__ import annotations

import threading
from datetime import UTC, date

_lock = threading.Lock()
_day: date | None = None
_spent = 0.0


def add_and_check(amount: float, cap: float) -> tuple[bool, float]:
    global _day, _spent
    today = date.today()
    with _lock:
        if _day != today:
            _day = today
            _spent = 0.0
        if _spent + amount > cap:
            return False, _spent
        _spent += amount
        return True, _spent


def current() -> float:
    add_and_check(0.0, cap=1e9)
    return _spent
