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


EXCUSES = [
    "📻 *kshhh* ...can't talk... sandstorm... *kshhh*",
    "Sorry, my radio's full of sand. I'll get back to you after I shake it out.",
    "Can't reply right now. A radscorpion is sitting on my keyboard.",
    "I'd answer, but I'm rationing my words. Only 3 left this week. That was 2. Bye.",
    "My Geiger counter is clicking too loud to hear you.",
    "Out scavenging for batteries. Leave a message after the tumbleweed.",
    "I was going to respond, but the vultures took my last thought.",
    "The signal tower collapsed again. Please try yelling louder into the void.",
    "Busy boiling the last cup of clean water. Ask me again when it's not radioactive.",
    "I traded my ability to chat for a can of beans. No regrets.",
    "Can't talk. Dust devil incoming. Hold onto your hat.",
    "Message received, but it got buried under 3 feet of sand.",
    "I'm conserving power. My solar panel is mostly a mirage.",
    "A raider stole my vocabulary. All I have left is this sentence.",
    "Hold on, there's a tumbleweed stuck in the antenna again.",
    "My response evaporated in the heat before it reached you.",
    "Shhh. If we're quiet the mutants might not find us.",
    "I'd love to help, but my circuits are 40% rust and 60% regret.",
    "Static. Static. More static. Try again after the next acid rain.",
    "Sorry, I only respond to messages delivered by carrier vulture.",
]

_last_excuse: str | None = None


def excuse() -> str:
    """A random excuse, never the same one twice in a row."""
    global _last_excuse
    choice = random.choice([e for e in EXCUSES if e != _last_excuse])
    _last_excuse = choice
    return choice
