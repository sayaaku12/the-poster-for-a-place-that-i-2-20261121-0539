#!/usr/bin/env python3
"""Draw a travel poster for SOLMARA, a place that isn't there.

The program writes one 1024x1024 PNG to /output/entry.png (or to the
directory named by MAKEFUN_OUTPUT_DIR). Everything is drawn in code
with Pillow: no network, no external assets, deterministic output.

The poster: a golden dusk over a turquoise lagoon, two moons in an
indigo sky, and one landmark -- a lighthouse standing on a rock islet
beneath a natural stone arch. The place name SOLMARA is set large in
the navy title band, with the tagline "WHERE THE SEA HOLDS THE SKY".
"""

import hashlib
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
HORIZON = 640          # sky/sea boundary
TITLE_TOP = 800        # top of the navy title band

# Palette
INK_NAVY = (14, 26, 51)
SKY_TOP = (24, 30, 74)
SKY_MID = (94, 66, 124)
SKY_LOW = (242, 166, 90)
SEA_TOP = (42, 127, 143)
SEA_LOW = (18, 70, 92)
CREAM = (250, 240, 214)
GOLD = (232, 184, 96)
PALE_MOON = (244, 238, 220)
ROCK = (38, 44, 66)
LIGHTHOUSE_WHITE = (248, 244, 232)
LIGHTHOUSE_RED = (198, 74, 60)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(draw, top, bottom, y0, y1, c_top, c_bot):
    """Vertical gradient band from y0 to y1."""
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        draw.line([(0, y), (W, y)], fill=lerp(c_top, c_bot, t))


def tracked_text(draw, cx, y, text, fnt, fill, tracking=6):
    """Draw text centred at cx with letter tracking (px between glyphs)."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking


def draw_sky(img, rng):
    d = ImageDraw.Draw(img, "RGBA")
    vgrad(d, 0, 0, 0, HORIZON, SKY_TOP, SKY_LOW)
    # Stars in the upper sky, fading out toward the horizon.
    for _ in range(90):
        x = rng.randint(20, W - 20)
        y = rng.randint(20, 420)
        r = rng.choice([1, 1, 1, 2])
        a = int(255 * (1 - y / 520.0) * rng.uniform(0.5, 1.0))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 230, a))
    # Big moon, upper right, with craters.
    d.ellipse([742, 92, 858, 208], fill=PALE_MOON + (255,))
    for cx, cy, cr in [(782, 128, 12), (818, 168, 9), (772, 172, 6),
                       (830, 122, 5)]:
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                  fill=(214, 206, 188, 255))
    # Small second moon, upper left of the big one.
    d.ellipse([668, 62, 712, 106], fill=PALE_MOON + (255,))
    d.ellipse([682, 76, 694, 88], fill=(214, 206, 188, 255))
    # Low sun: glow rings, then the disc on the horizon.
    for r, a in [(150, 26), (110, 40), (78, 70)]:
        d.ellipse([512 - r, HORIZON - r, 512 + r, HORIZON + r],
                  fill=(255, 196, 110, a))
    d.ellipse([466, 594, 558, 686], fill=(255, 214, 140, 255))
    # Birds: small dark chevrons in the sky.
    for bx, by, s in [(180, 180, 14), (240, 230, 11), (880, 300, 12),
                      (150, 320, 10), (330, 150, 9)]:
        d.line([(bx - s, by), (bx, by - s // 2), (bx + s, by)],
               fill=(30, 34, 60, 220), width=3)
    return d


def draw_sea(img, rng):
    d = ImageDraw.Draw(img, "RGBA")
    vgrad(d, 0, 0, HORIZON, TITLE_TOP, SEA_TOP, SEA_LOW)
    # Sun path: shimmering horizontal dashes below the sun.
    for i in range(9):
        y = HORIZON + 12 + i * 16
        half = 26 + i * 13
        a = max(30, 190 - i * 18)
        d.line([(512 - half, y), (512 + half, y)],
               fill=(255, 206, 130, a), width=5)
    # Gentle wave strokes.
    for _ in range(46):
        x = rng.randint(10, W - 10)
        y = rng.randint(HORIZON + 8, TITLE_TOP - 12)
        ln = rng.randint(14, 42)
        a = rng.randint(40, 110)
        d.line([(x, y), (x + ln, y)], fill=(200, 235, 240, a), width=2)
    return d

def draw_landmark(img):
    """Stone arch, rock islet and lighthouse -- the one landmark."""
    d = ImageDraw.Draw(img, "RGBA")
    # Natural stone arch on the right, standing in the sea: a full
    # half-arch whose legs reach the water, with rock feet.
    d.arc([680, 560, 980, 860], start=180, end=360, fill=ROCK + (255,),
          width=30)
    d.arc([680, 560, 980, 860], start=185, end=355, fill=(74, 82, 112, 255),
          width=5)
    d.polygon([(658, 706), (700, 706), (694, 734), (664, 734)],
              fill=ROCK + (255,))
    d.polygon([(958, 706), (992, 706), (986, 732), (964, 732)],
              fill=ROCK + (255,))
    # Rock islet: dark silhouette rising from the sea, centre-left.
    d.polygon([(400, 800), (420, 700), (452, 668), (560, 668),
               (592, 700), (612, 800)], fill=ROCK + (255,))
    d.polygon([(452, 668), (560, 668), (548, 640), (464, 640)],
              fill=(52, 58, 84, 255))
    # Lighthouse tower on the islet: white with red bands.
    d.rectangle([486, 470, 526, 640], fill=LIGHTHOUSE_WHITE + (255,))
    d.rectangle([486, 520, 526, 552], fill=LIGHTHOUSE_RED + (255,))
    d.rectangle([486, 588, 526, 616], fill=LIGHTHOUSE_RED + (255,))
    # Lamp room and dome.
    d.rectangle([482, 448, 530, 470], fill=(30, 36, 56, 255))
    d.rectangle([492, 452, 520, 466], fill=(255, 226, 150, 255))
    d.polygon([(478, 448), (534, 448), (506, 428)], fill=ROCK + (255,))
    # Light beam sweeping left over the lagoon.
    d.polygon([(486, 458), (180, 420), (180, 500), (486, 466)],
              fill=(255, 226, 150, 36))
    # Tiny windows on the tower.
    d.rectangle([503, 566, 509, 578], fill=(30, 36, 56, 255))
    return d


def draw_sailboat(img):
    d = ImageDraw.Draw(img, "RGBA")
    # Small sailboat drifting on the lagoon, left of the islet.
    d.polygon([(196, 742), (196, 668), (238, 742)], fill=CREAM + (255,))
    d.polygon([(204, 742), (204, 686), (172, 742)], fill=(232, 184, 96, 255))
    d.polygon([(160, 742), (252, 742), (240, 758), (172, 758)],
              fill=(24, 32, 54, 255))
    d.line([(196, 742), (196, 762)], fill=(24, 32, 54, 255), width=3)
    return d


def draw_title_band(img):
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, TITLE_TOP, W, H], fill=INK_NAVY + (255,))
    # Gold rules framing the band.
    d.line([(0, TITLE_TOP), (W, TITLE_TOP)], fill=GOLD + (255,), width=4)
    d.line([(60, TITLE_TOP + 22), (W - 60, TITLE_TOP + 22)],
           fill=(120, 96, 54, 255), width=1)
    # The place name, large serif, cream with a gold shadow offset.
    title_f = font(SERIF, 112)
    d.text((512, 828), "SOLMARA", font=title_f, fill=(196, 150, 66, 255),
           anchor="ma")
    d.text((510, 826), "SOLMARA", font=title_f, fill=CREAM + (255,),
           anchor="ma")
    # Tagline, letterspaced small caps.
    tracked_text(d, 512, 946, "WHERE THE SEA HOLDS THE SKY",
                 font(SANS_BOLD, 26), CREAM, tracking=7)
    # Footer line.
    tracked_text(d, 512, 978, "THE ISLES BEYOND THE MAP",
                 font(SANS, 15), GOLD, tracking=5)
    # Thin gold frame around the whole poster.
    d.rectangle([18, 18, W - 18, H - 18], outline=GOLD + (255,), width=3)
    d.rectangle([28, 28, W - 28, H - 28], outline=(120, 96, 54, 255),
                width=1)
    return d


def render():
    rng = random.Random(20261121)
    img = Image.new("RGB", (W, H), SKY_TOP)
    draw_sky(img, rng)
    draw_sea(img, rng)
    draw_landmark(img)
    draw_sailboat(img)
    draw_title_band(img)
    return img


def output_path():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, "entry.png")


EXPECTED_SHA256 = "b1d6b13f0f9598475464f6446c3b8a6ea9895a9e034fd4ddb50d43102a0060f1"


def self_test():
    """Run twice, require byte-identical output, valid size/dimensions."""
    import tempfile
    hashes = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as td:
            os.environ["MAKEFUN_OUTPUT_DIR"] = td
            img = render()
            p = output_path()
            img.save(p, format="PNG")
            data = open(p, "rb").read()
            hashes.append(hashlib.sha256(data).hexdigest())
            im = Image.open(p)
            assert im.size == (1024, 1024), f"size {im.size}"
            assert len(data) <= 1_048_576, f"bytes {len(data)}"
    assert hashes[0] == hashes[1], f"nondeterministic: {hashes}"
    if EXPECTED_SHA256:
        assert hashes[0] == EXPECTED_SHA256, (
            f"hash changed: {hashes[0]} (expected {EXPECTED_SHA256})")
    print(f"SELF-TEST PASSED sha256={hashes[0]}")
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    img = render()
    p = output_path()
    img.save(p, format="PNG")
    data = open(p, "rb").read()
    print(f"wrote {p} {len(data)} bytes "
          f"sha256={hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
