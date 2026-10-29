"""What the bot says in #general."""

import random

WEEKLY = [
    (10, [
        "The Wasteland is buzzing. Someone even planted a cactus.",
        "Signs of life everywhere. Almost suspicious.",
    ]),
    (30, [
        "A few footprints in the sand. Somebody's still out there.",
        "The campfire's still warm. Barely.",
    ]),
    (50, [
        "The dust is settling. Nobody's around to kick it up.",
        "A tumbleweed rolled through #general this week. It was the most active member.",
    ]),
    (70, [
        "Tumbleweed traffic is at an all-time high. Human traffic, not so much.",
        "The vultures have started circling the server.",
    ]),
    (90, [
        "Bones are bleaching in the sun. The radio only plays static.",
        "Last survivor spotted: unconfirmed.",
    ]),
    (101, [
        "This place is nearly a barren wasteland. Say something before the sand takes it all.",
        "It's so quiet out here you can hear the Geiger counter ticking.",
    ]),
]

RISING = {
    10: "The first speck of dust has landed.",
    20: "Something's drying up out there.",
    30: "Tumbleweeds have been spotted on the horizon.",
    40: "The wells are running low.",
    50: "Half a wasteland. The cacti are starting to wilt.",
    60: "The vultures have noticed us.",
    70: "Bones are turning up in the sand.",
    80: "The radio's gone to static.",
    90: "Final warning: The Wasteland is almost completely barren.",
    100: "It's official. The Wasteland is a COMPLETELY BARREN WASTELAND. ☠️",
}

FALLING = [
    "Signs of life detected! Someone's been watering the cacti.",
    "Rain in the Wasteland! Activity has pushed the dust back.",
    "Survivors spotted! The wasteland is retreating.",
]


def weekly(percent: float) -> str:
    for limit, lines in WEEKLY:
        if percent < limit:
            flavour = random.choice(lines)
            break
    return f"📻 **Weekly Waste-O-Meter report: {percent:.1f}%**\n{flavour}"


def mark_reached(mark: int, previous: int) -> str:
    if mark > previous:
        return f"☢️ **Waste-O-Meter hit {mark}%!** {RISING.get(mark, '')}".strip()
    return f"🌱 **Waste-O-Meter dropped below {previous}%.** {random.choice(FALLING)}"
