"""Draws the Waste-O-Meter as a wasteland scene with a rusty gauge.

The scene gets bleaker as the percentage rises: the sky turns from blue to
dusty orange to toxic brown, plants die off, and bones and tumbleweeds appear.
"""

import io
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 900, 500
HORIZON = 330

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _palette(t: float):
    """Sky top, sky bottom and ground colours for bleakness t (0..1)."""
    stops = [
        (0.0, (70, 130, 200), (190, 220, 235), (150, 140, 80)),
        (0.4, (190, 120, 60), (240, 190, 120), (170, 130, 80)),
        (0.7, (140, 70, 40), (220, 140, 70), (150, 100, 60)),
        (1.0, (60, 40, 30), (150, 100, 50), (90, 70, 50)),
    ]
    for (t0, *c0), (t1, *c1) in zip(stops, stops[1:]):
        if t <= t1:
            k = (t - t0) / (t1 - t0)
            return [_mix(c0[i], c1[i], k) for i in range(3)]
    return stops[-1][1:]


def _sky(draw, top, bottom):
    for y in range(HORIZON):
        draw.line([(0, y), (WIDTH, y)], fill=_mix(top, bottom, y / HORIZON))


def _sun(img, t):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    x, y, r = 720, 110 + int(t * 60), 46
    color = _mix((255, 240, 180), (230, 120, 60), t)
    g.ellipse([x - r * 2, y - r * 2, x + r * 2, y + r * 2], fill=color + (60,))
    glow = glow.filter(ImageFilter.GaussianBlur(25))
    img.alpha_composite(glow)
    ImageDraw.Draw(img).ellipse([x - r, y - r, x + r, y + r], fill=color + (255,))


def _ground(draw, rng, color):
    # Distant mesas
    mesa = _mix(color, (60, 40, 40), 0.45)
    draw.polygon([(0, HORIZON), (60, 270), (190, 265), (230, HORIZON)], fill=mesa)
    draw.polygon([(420, HORIZON), (470, 285), (560, 280), (600, HORIZON)], fill=mesa)
    draw.rectangle([0, HORIZON, WIDTH, HEIGHT], fill=color)
    # Cracks in the dirt
    crack = _mix(color, (40, 25, 15), 0.5)
    for _ in range(18):
        x, y = rng.randint(0, WIDTH), rng.randint(HORIZON + 15, HEIGHT)
        for _ in range(4):
            nx, ny = x + rng.randint(-35, 35), y + rng.randint(-8, 8)
            draw.line([(x, y), (nx, ny)], fill=crack, width=2)
            x, y = nx, ny


def _cactus(draw, x, y, h, alive):
    color = (60, 130, 60) if alive else (110, 90, 60)
    w = 14
    draw.rounded_rectangle([x - w // 2, y - h, x + w // 2, y], radius=7, fill=color)
    draw.rounded_rectangle([x - 30, y - h * 0.6, x - 20, y - h * 0.35], radius=5, fill=color)
    draw.rectangle([x - 30, y - h * 0.4, x, y - h * 0.33], fill=color)
    draw.rounded_rectangle([x + 20, y - h * 0.8, x + 30, y - h * 0.5], radius=5, fill=color)
    draw.rectangle([x, y - h * 0.57, x + 30, y - h * 0.5], fill=color)


def _skull(draw, x, y):
    bone = (230, 220, 195)
    draw.ellipse([x - 16, y - 28, x + 16, y], fill=bone)
    draw.rectangle([x - 9, y - 6, x + 9, y + 6], fill=bone)
    draw.ellipse([x - 10, y - 20, x - 2, y - 11], fill=(40, 30, 25))
    draw.ellipse([x + 2, y - 20, x + 10, y - 11], fill=(40, 30, 25))
    draw.line([(x - 26, y + 10), (x + 26, y + 2)], fill=bone, width=5)


def _tumbleweed(draw, rng, x, y, r):
    for _ in range(26):
        a, b = rng.uniform(0, math.tau), rng.uniform(0, math.tau)
        draw.line(
            [(x + r * math.cos(a), y + r * math.sin(a)), (x + r * math.cos(b), y + r * math.sin(b))],
            fill=(95, 65, 35), width=3,
        )


def _gauge(draw, percent):
    cx, cy, r = 250, 300, 170
    # Rusty housing
    draw.pieslice([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], 180, 360, fill=(70, 50, 40))
    draw.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=(235, 225, 200))
    # Coloured bands: green -> yellow -> orange -> red
    bands = [(0, 30, (90, 160, 80)), (30, 60, (220, 190, 60)), (60, 85, (225, 120, 50)), (85, 100, (190, 50, 40))]
    for lo, hi, color in bands:
        draw.arc([cx - r + 12, cy - r + 12, cx + r - 12, cy + r - 12], 180 + lo * 1.8, 180 + hi * 1.8, fill=color, width=22)
    # Ticks every 10%
    tick_font = _font(16)
    for p in range(0, 101, 10):
        a = math.radians(180 + p * 1.8)
        x1, y1 = cx + (r - 40) * math.cos(a), cy + (r - 40) * math.sin(a)
        x2, y2 = cx + (r - 54) * math.cos(a), cy + (r - 54) * math.sin(a)
        draw.line([(x1, y1), (x2, y2)], fill=(50, 40, 35), width=3)
        tx, ty = cx + (r - 72) * math.cos(a), cy + (r - 72) * math.sin(a)
        draw.text((tx, ty), str(p), font=tick_font, fill=(50, 40, 35), anchor="mm")
    # Needle
    a = math.radians(180 + percent * 1.8)
    draw.line([(cx, cy), (cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a))], fill=(150, 30, 25), width=7)
    draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(70, 50, 40))
    # Radiation symbol in the hub area
    draw.text((cx, cy - 55), "☢", font=_font(34), fill=(70, 50, 40), anchor="mm")


def label(percent: float) -> str:
    if percent < 10:
        return "THRIVING OASIS"
    if percent < 30:
        return "SIGNS OF LIFE"
    if percent < 50:
        return "DUST SETTLING"
    if percent < 70:
        return "TUMBLEWEED COUNTRY"
    if percent < 90:
        return "BONE DRY"
    if percent < 100:
        return "NEARLY BARREN"
    return "TOTAL WASTELAND"


def render(percent: float) -> bytes:
    """Return a PNG of the Waste-O-Meter at this percentage."""
    percent = max(0.0, min(100.0, percent))
    t = percent / 100
    rng = random.Random(42)  # same layout every time, only the bleakness changes

    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    sky_top, sky_bottom, ground = _palette(t)
    _sky(draw, sky_top, sky_bottom)
    _sun(img, t)
    draw = ImageDraw.Draw(img)
    _ground(draw, rng, ground)

    # Scenery: cacti die and disappear, bones and tumbleweeds show up
    if t < 0.85:
        _cactus(draw, 520, 400, 110, alive=t < 0.5)
    if t < 0.6:
        _cactus(draw, 820, 360, 70, alive=t < 0.3)
    if t >= 0.3:
        _tumbleweed(draw, rng, 640, 430, 26)
    if t >= 0.6:
        _skull(draw, 780, 455)
        _tumbleweed(draw, rng, 860, 410, 18)
    if t >= 0.85:
        _skull(draw, 470, 470)

    # Dust haze
    haze = Image.new("RGBA", img.size, (200, 150, 90, int(90 * t)))
    img.alpha_composite(haze)
    draw = ImageDraw.Draw(img)

    _gauge(draw, percent)

    # Title and reading
    shadow = (30, 20, 15)
    title = _font(34)
    draw.text((452, 32), "WASTE-O-METER", font=title, fill=shadow, anchor="mt")
    draw.text((450, 30), "WASTE-O-METER", font=title, fill=(245, 225, 180), anchor="mt")
    big = _font(64)
    draw.text((250, 350), f"{percent:.0f}%", font=big, fill=shadow, anchor="mt", stroke_width=0)
    draw.text((248, 348), f"{percent:.0f}%", font=big, fill=(245, 225, 180), anchor="mt")
    tag = _font(24)
    draw.text((250, 425), label(percent), font=tag, fill=(245, 225, 180), anchor="mt", stroke_width=2, stroke_fill=shadow)

    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()
