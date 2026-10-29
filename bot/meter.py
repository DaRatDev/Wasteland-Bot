"""Waste-O-Meter math.

The meter climbs steadily while the server is quiet (90 silent days = 100%)
and every bit of activity knocks it back down a little.
"""

from dataclasses import dataclass

DAYS_TO_FULL_WASTELAND = 90
CLIMB_PER_DAY = 100 / DAYS_TO_FULL_WASTELAND  # ~1.11% per day

# How many activity points knock the meter down by 1%.
POINTS_PER_PERCENT = 4

# Activity points for each kind of activity.
POINTS = {
    "message": 1.0,
    "reaction": 0.25,
    "voice_minute": 0.1,  # per person, per minute in voice
}


@dataclass
class MeterState:
    percent: float
    updated_at: float  # unix timestamp


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def climb(state: MeterState, now: float) -> MeterState:
    """Add the decay for the time that passed since the last update."""
    elapsed_days = max(0.0, now - state.updated_at) / 86400
    return MeterState(clamp(state.percent + elapsed_days * CLIMB_PER_DAY), now)


def knock_down(state: MeterState, points: float) -> MeterState:
    """Lower the meter for activity worth the given points."""
    return MeterState(clamp(state.percent - points / POINTS_PER_PERCENT), state.updated_at)


def from_silence(days_silent: float, now: float) -> MeterState:
    """Starting state for a server that has been silent for this many days."""
    return MeterState(clamp(days_silent * CLIMB_PER_DAY), now)


def milestone(percent: float) -> int:
    """The 10% band the meter is in: 0, 10, 20 ... 100."""
    return int(clamp(percent) // 10) * 10
