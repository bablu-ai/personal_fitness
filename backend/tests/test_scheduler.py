from datetime import date
import pytest
from app.services.scheduler import _is_scheduled_today


@pytest.mark.parametrize("schedule,weekday,expected", [
    (None, 0, True),
    ("daily", 3, True),
    ("every day", 6, True),
    ("weekly", 0, True),       # Monday
    ("weekly", 2, False),      # Wednesday
    ("weekdays", 0, True),
    ("weekdays", 4, True),
    ("weekdays", 5, False),    # Saturday
    ("weekends", 5, True),
    ("weekends", 0, False),
    ("mon,wed,fri", 0, True),  # Monday
    ("mon,wed,fri", 2, True),  # Wednesday
    ("mon,wed,fri", 1, False), # Tuesday
    ("unknown_value", 0, True),  # unknown defaults to True
])
def test_schedule_logic(schedule, weekday, expected):
    # Use a Monday=0 ... Sunday=6 mapping
    # Find a real date that matches the weekday
    base = date(2026, 5, 18)  # Monday
    target = base.replace(day=base.day + weekday)
    assert _is_scheduled_today(schedule, target) == expected
