from datetime import datetime, timedelta
from src.agent.schedule_checker import is_office_hours


def _dt(weekday: int, hour: int, minute: int = 0) -> datetime:
    """Creates datetime with given weekday and time. 0=Monday."""
    base = datetime(2024, 1, 1)  # This is a Monday
    offset = (weekday - base.weekday()) % 7
    return (base + timedelta(days=offset)).replace(hour=hour, minute=minute, second=0)


def test_monday_morning_is_office_hours():
    assert is_office_hours(_dt(0, 10)) is True


def test_monday_afternoon_is_office_hours():
    assert is_office_hours(_dt(0, 17)) is True


def test_midday_gap_is_not_office_hours():
    assert is_office_hours(_dt(0, 15)) is False


def test_before_morning_is_not_office_hours():
    assert is_office_hours(_dt(0, 8, 59)) is False


def test_after_closing_is_not_office_hours():
    assert is_office_hours(_dt(0, 19, 1)) is False


def test_saturday_is_not_office_hours():
    assert is_office_hours(_dt(5, 10)) is False


def test_sunday_is_not_office_hours():
    assert is_office_hours(_dt(6, 10)) is False


def test_friday_afternoon_is_office_hours():
    assert is_office_hours(_dt(4, 17)) is True
