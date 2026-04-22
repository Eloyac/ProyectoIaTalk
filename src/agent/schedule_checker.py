from datetime import datetime, time as dtime
from config.settings import settings


def is_office_hours(now: datetime | None = None) -> bool:
    """Returns True if `now` falls within office hours L-V 9-14h / 16-19h."""
    if now is None:
        now = datetime.now()

    office_days = [int(d) for d in settings.office_days.split(",")]
    if now.weekday() not in office_days:
        return False

    current = now.time()
    start = _t(settings.office_hours_start)
    mid_end = _t(settings.office_hours_mid_end)
    mid_start = _t(settings.office_hours_mid_start)
    end = _t(settings.office_hours_end)

    return (start <= current <= mid_end) or (mid_start <= current <= end)


def _t(hhmm: str) -> dtime:
    h, m = hhmm.split(":")
    return dtime(int(h), int(m))
