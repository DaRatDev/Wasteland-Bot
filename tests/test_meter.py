from bot import meter
from bot.meter import MeterState

DAY = 86400


def test_ninety_silent_days_is_full_wasteland():
    state = meter.climb(MeterState(0, 0), 90 * DAY)
    assert round(state.percent, 6) == 100


def test_meter_never_goes_past_100():
    state = meter.climb(MeterState(95, 0), 30 * DAY)
    assert state.percent == 100


def test_activity_knocks_it_down_a_bit():
    state = meter.knock_down(MeterState(50, 0), meter.POINTS["message"])
    assert 49 < state.percent < 50


def test_activity_never_goes_below_zero():
    state = meter.knock_down(MeterState(1, 0), 1000)
    assert state.percent == 0


def test_starting_value_from_silence():
    assert round(meter.from_silence(45, 0).percent) == 50


def test_milestones():
    assert meter.milestone(0) == 0
    assert meter.milestone(9.99) == 0
    assert meter.milestone(10) == 10
    assert meter.milestone(57) == 50
    assert meter.milestone(100) == 100


def test_store_round_trip(tmp_path):
    from bot.store import Store

    store = Store(tmp_path)
    assert store.load() is None
    store.save(MeterState(42.5, 123), 40)
    assert store.load() == (MeterState(42.5, 123), 40)
    store.log_activity("message", 1, ts=200)
    store.log_activity("message", 1, ts=300)
    store.log_activity("reaction", 0.25, ts=50)
    assert store.activity_since(100) == {"message": 2}


def test_announces_rising_marks():
    assert meter.next_announced_mark(30.0, 20) == 30
    assert meter.next_announced_mark(29.9, 20) is None
    assert meter.next_announced_mark(55, 30) == 50  # skipped 40, jumps straight to 50


def test_falling_needs_margin_so_it_does_not_flip_flop():
    assert meter.next_announced_mark(39.8, 40) is None   # one message under the line
    assert meter.next_announced_mark(37.5, 40) is None
    assert meter.next_announced_mark(36.9, 40) == 30
