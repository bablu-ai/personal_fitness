from datetime import date
import pytest
import json
from app.services.scheduler import _is_scheduled_today, is_necessary_supplement


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


def test_is_necessary_supplement_active_category_b():
    class T:
        pillar = "supplements"
        extra_metadata = json.dumps({"status": "Active", "category": "B"})
    assert is_necessary_supplement(T()) is True


@pytest.mark.parametrize("pillar,meta", [
    ("supplements", {"status": "Discuss", "category": "B"}),
    ("supplements", {"status": "Active", "category": "A"}),
    ("nutrition", {"status": "Active", "category": "B"}),
])
def test_is_necessary_supplement_rejects_non_required_rows(pillar, meta):
    class T:
        pass
    t = T()
    t.pillar = pillar
    t.extra_metadata = json.dumps(meta)
    assert is_necessary_supplement(t) is False
