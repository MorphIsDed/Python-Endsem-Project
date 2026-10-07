"""Calendar utilities using business-day semantics and holiday calendars."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

import numpy as np


def normalize_holidays(holidays: Iterable[date] | None) -> set[date]:
    return {h for h in (holidays or [])}


def business_days_between(start: date, end: date, holidays: Iterable[date] | None = None) -> int:
    """Return the number of working days between start and end, inclusive."""
    if end < start:
        return 0
    holiday_dates = normalize_holidays(holidays)
    weekdays = np.array([1, 2, 3, 4, 5], dtype=int)
    date_range = np.arange(start.toordinal(), end.toordinal() + 1, dtype='int64')
    dates = np.array([date.fromordinal(int(v)) for v in date_range])
    dts = np.array([d.weekday() + 1 for d in dates], dtype=int)
    mask = np.isin(dts, weekdays)
    holiday_mask = np.array([d in holiday_dates for d in dates])
    workdays = np.count_nonzero(mask & ~holiday_mask)
    return int(workdays)


def add_business_days(start: date, days: int, holidays: Iterable[date] | None = None) -> date:
    """Add business days to a date, skipping weekends and holidays."""
    if days == 0:
        return start
    holiday_dates = normalize_holidays(holidays)
    current = start
    step = 1 if days > 0 else -1
    moved = 0
    while moved < abs(days):
        current += timedelta(days=step)
        if current.weekday() < 5 and current not in holiday_dates:
            moved += 1
    return current


def working_days_in_range(start: date, end: date, holidays: Iterable[date] | None = None) -> int:
    """Compatibility wrapper for task-duration calculations."""
    return business_days_between(start, end, holidays)


def weekend_dates(start: date, end: date) -> list[date]:
    dates: list[date] = []
    current = start
    while current <= end:
        if current.weekday() >= 5:
            dates.append(current)
        current += timedelta(days=1)
    return dates
