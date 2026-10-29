from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from bot.main import WastelandBot

TZ = ZoneInfo("America/New_York")


def slot(now, day=0, hour=12):
    fake = SimpleNamespace(cfg=SimpleNamespace(weekly_day=day, weekly_hour=hour))
    return WastelandBot._last_weekly_slot(fake, now)


def test_slot_later_in_the_week():
    # Wednesday -> the Monday before
    assert slot(datetime(2026, 10, 28, 9, tzinfo=TZ)) == datetime(2026, 10, 26, 12, tzinfo=TZ)


def test_slot_same_day_before_the_hour_is_last_week():
    assert slot(datetime(2026, 10, 26, 11, 59, tzinfo=TZ)) == datetime(2026, 10, 19, 12, tzinfo=TZ)


def test_slot_same_day_after_the_hour():
    assert slot(datetime(2026, 10, 26, 12, 5, tzinfo=TZ)) == datetime(2026, 10, 26, 12, tzinfo=TZ)
