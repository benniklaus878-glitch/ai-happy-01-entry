#!/usr/bin/env python3
"""
make.fun bounty "Make the AI judge happy" (ai-happy-01).

Writes ONE image to /output/entry.png.

Contract (from https://make.fun/api/competitions, item ai-happy-01):
  - program at main.py in the repo root (Python), run by the grader
  - output: a whole PNG or JPEG at /output/entry.png,
    at most 1 MiB and at most 1024x1024 pixels
  - no network; the program runs twice and both runs must write
    the same bytes -> this generator is fully deterministic
    (fixed geometry, no randomness, no timestamps in the PNG)

Strategy: an AI vision judge picks, pairwise, the image that makes it
"happier". So the picture stacks the strongest universal happy signals
in one bold, uncluttered scene: a huge smiling sun, a rainbow, smiling
flowers, hearts, butterflies and fluffy clouds, in bright warm,
high-contrast colours. No text (text renders badly and reads as noise).
"""

import math
import os
import shutil
import sys

SS = 2                 # supersampling factor (render 2048, ship 1024)
W = 1024 * SS
H = 1024 * SS
OUT_SIZE = 1024

# ---------------------------------------------------------------- palette
INK = (74, 47, 43)             # warm dark brown for faces
SKY_TOP = (94, 186, 247)
SKY_MID = (178, 231, 253)
SKY_LOW = (255, 244, 196)
SUN_CORE = (255, 217, 61)
SUN_EDGE = (255, 183, 3)
RAY_A = (255, 183, 3)
RAY_B = (255, 214, 64)
CHEEK = (255, 138, 128)
RAINBOW = [(255, 89, 94), (255, 146, 76), (255, 202, 58),
           (138, 201, 38), (76, 201, 240), (154, 108, 224)]
HILL_BACK = (142, 208, 129)
HILL_FRONT = (86, 178, 74)
GRASS_DARK = (62, 155, 58)
STEM = (46, 139, 60)
CLOUD = (255, 255, 255)
CLOUD_SHADE = (219, 242, 255)
HEART_A = (255, 77, 109)
HEART_B = (255, 122, 156)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- helpers
def sky(draw):
    """Vertical 3-stop gradient down to the horizon."""
    horizon = int(H * 0.66)
    for y in range(horizon + 1):
        t = y / horizon
        if t < 0.55:
            c = lerp(SKY_TOP, SKY_MID, t / 0.55)
        else:
            c = lerp(SKY_MID, SKY_LOW, (t - 0.55) / 0.45)
        draw.line([(0, y), (W, y)], fill=c)
    draw.rectangle([0, horizon, W, H], fill=SKY_LOW)


def cloud(draw, cx, cy, s, face=False):
    """Fluffy flat-bottom cloud made of circles; optional tiny smile."""
    puffs = [(-0.95, 0.10, 0.52), (-0.48, -0.22, 0.68), (0.05, -0.34, 0.80),
             (0.58, -0.18, 0.64), (1.0, 0.12, 0.48)]
    for dx, dy, r in puffs:
        draw.ellipse([cx + (dx - r) * s, cy + (dy - r) * s,
                      cx + (dx + r) * s, cy + (dy + r) * s], fill=CLOUD)
    draw.rectangle([cx - 1.45 * s, cy - 0.05 * s, cx + 1.45 * s, cy + 0.42 * s],
                   fill=CLOUD)
    draw.rectangle([cx - 1.45 * s, cy + 0.35 * s, cx + 1.45 * s, cy + 0.42 * s],
                   fill=CLOUD_SHADE)
    if face:
        r = 0.16 * s
        for ex in (-0.38 * s, 0.38 * s):
            draw.arc([cx + ex - r, cy - 0.02 * s - r, cx + ex + r, cy - 0.02 * s + r],
                     start=180, end=360, fill=INK, width=max(3, int(0.05 * s)))
        draw.arc([cx - 0.22 * s, cy + 0.02 * s, cx + 0.22 * s, cy + 0.42 * s],
                 start=15, end=165, fill=INK, width=max(3, int(0.055 * s)))


def happy_face(draw, cx, cy, r, eye="arc", lw=None):
    """Closed happy eyes (inverted-U arcs) + a big smile + rosy cheeks."""
    lw = lw or max(4, int(r * 0.11))
    er = r * 0.30
    for ex in (-0.38 * r, 0.38 * r):
        if eye == "arc":
            draw.arc([cx + ex - er, cy - 0.28 * r - er * 0.7,
                      cx + ex + er, cy - 0.28 * r + er * 0.7],
                     start=180, end=360, fill=INK, width=lw)
        else:
            draw.ellipse([cx + ex - er * 0.32, cy - 0.34 * r,
                          cx + ex + er * 0.32, cy - 0.10 * r], fill=INK)
    # open smile (filled half-disc reads joyful at any size)
    sr = r * 0.52
    draw.pieslice([cx - sr, cy - 0.05 * r - sr * 0.55,
                   cx + sr, cy - 0.05 * r + sr * 0.95],
                  start=5, end=175, fill=INK)
    draw.pieslice([cx - sr * 0.62, cy + 0.16 * r,
                   cx + sr * 0.62, cy + 0.62 * r],
                  start=5, end=175, fill=(255, 110, 130))  # tongue
    for chx in (-0.72 * r, 0.72 * r):
        draw.ellipse([cx + chx - r * 0.20, cy + 0.10 * r - r * 0.13,
                      cx + chx + r * 0.20, cy + 0.10 * r + r * 0.13], fill=CHEEK)


def sun(draw, cx, cy, r):
    for i in range(12):
        a = math.radians(i * 30)
        r1 = r * 1.10
        r2 = r * (1.52 if i % 2 == 0 else 1.34)
        wdt = int(r * 0.13)
        draw.line([(cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                   (cx + r2 * math.cos(a), cy + r2 * math.sin(a))],
                  fill=RAY_A if i % 2 == 0 else RAY_B, width=wdt)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN_EDGE)
    ri = r * 0.88
    draw.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=SUN_CORE)
    happy_face(draw, cx, cy + r * 0.05, r * 0.78)


def rainbow(draw, cx, cy, r_out):
    cols = RAINBOW
    band = r_out / (len(cols) + 1.6)
    for i, c in enumerate(cols):
        r = r_out - i * band
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=360,
                 fill=c, width=int(band) + 2)


def heart(draw, cx, cy, s, color):
    draw.ellipse([cx - 0.62 * s, cy - 0.52 * s, cx - 0.02 * s, cy + 0.08 * s],
                 fill=color)
    draw.ellipse([cx + 0.02 * s, cy - 0.52 * s, cx + 0.62 * s, cy + 0.08 * s],
                 fill=color)
    draw.polygon([(cx - 0.585 * s, cy - 0.02 * s), (cx + 0.585 * s, cy - 0.02 * s),
                  (cx, cy + 0.72 * s)], fill=color)
    draw.ellipse([cx - 0.44 * s, cy - 0.40 * s, cx - 0.22 * s, cy - 0.18 * s],
                 fill=(255, 255, 255))  # gloss dot


def sparkle(draw, cx, cy, s, color=(255, 255, 255)):
    draw.polygon([(cx, cy - s), (cx + 0.22 * s, cy - 0.22 * s), (cx + s, cy),
                  (cx + 0.22 * s, cy + 0.22 * s), (cx, cy + s),
                  (cx - 0.22 * s, cy + 0.22 * s), (cx - s, cy),
                  (cx - 0.22 * s, cy - 0.22 * s)], fill=color)


def flower(draw, cx, base_y, s, petal, center=(255, 217, 61), face=True):
    """Smiling daisy: stem + leaves, round petals, face in the middle."""
    top_y = base_y - 2.6 * s
    draw.line([(cx, base_y), (cx, top_y)], fill=STEM, width=max(3, int(0.16 * s)))
    draw.ellipse([cx - 0.85 * s, base_y - 1.15 * s, cx - 0.05 * s, base_y - 0.72 * s],
                 fill=STEM)
    draw.ellipse([cx + 0.05 * s, base_y - 0.85 * s, cx + 0.85 * s, base_y - 0.42 * s],
                 fill=STEM)
    for k in range(8):
        a = math.radians(k * 45)
        px, py = cx + 0.78 * s * math.cos(a), top_y + 0.78 * s * math.sin(a)
        draw.ellipse([px - 0.46 * s, py - 0.46 * s, px + 0.46 * s, py + 0.46 * s],
                     fill=petal)
    draw.ellipse([cx - 0.72 * s, top_y - 0.72 * s, cx + 0.72 * s, top_y + 0.72 * s],
                 fill=center)
    if face:
        happy_face(draw, cx, top_y, 0.60 * s, eye="dot",
                   lw=max(3, int(0.09 * s)))


def butterfly(draw, cx, cy, s, color):
    for sx in (-1, 1):
        draw.ellipse([cx + sx * 0.08 * s - (0.95 * s if sx < 0 else 0),
                      cy - 1.05 * s,
                      cx + sx * 0.08 * s + (0 if sx < 0 else 0.95 * s),
                      cy - 0.05 * s], fill=color)
        draw.ellipse([cx + sx * 0.06 * s - (0.78 * s if sx < 0 else 0),
                      cy + 0.02 * s,
                      cx + sx * 0.06 * s + (0 if sx < 0 else 0.78 * s),
                      cy + 0.82 * s], fill=color)
    draw.line([(cx, cy - 0.75 * s), (cx, cy + 0.72 * s)], fill=INK,
              width=max(3, int(0.14 * s)))
    for sx in (-1, 1):
        draw.arc([cx + (0 if sx < 0 else 0.02 * s) - (0.34 * s if sx < 0 else 0),
                  cy - 1.28 * s, cx + 0.36 * s * sx + 0.34 * s, cy - 0.72 * s],
                 start=200 if sx < 0 else 250, end=340 if sx < 0 else 30,
                 fill=INK, width=max(2, int(0.05 * s)))


def scene():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), SKY_TOP)
    d = ImageDraw.Draw(img)

    sky(d)

    # rainbow whose feet land behind the hills (drawn before them)
    rainbow(d, int(W * 0.86), int(H * 0.75), int(W * 0.33))

    # sun glow, then the sun itself (hero, top-left of centre)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    scx, scy, sr = int(W * 0.335), int(H * 0.295), int(W * 0.155)
    gd.ellipse([scx - sr * 1.55, scy - sr * 1.55, scx + sr * 1.55, scy + sr * 1.55],
               fill=(255, 236, 150, 70))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)
    sun(d, scx, scy, sr)

    # clouds
    cloud(d, int(W * 0.115), int(H * 0.135), int(W * 0.075), face=True)
    cloud(d, int(W * 0.80), int(H * 0.105), int(W * 0.058))

    # rolling hills
    d.ellipse([-int(W * 0.35), int(H * 0.60), int(W * 0.75), int(H * 1.18)],
              fill=HILL_BACK)
    d.ellipse([int(W * 0.30), int(H * 0.68), int(W * 1.45), int(H * 1.30)],
              fill=HILL_FRONT)

    # little clouds sitting on the rainbow's feet
    cloud(d, int(W * 0.53), int(H * 0.715), int(W * 0.050))
    cloud(d, int(W * 0.915), int(H * 0.665), int(W * 0.062))

    # smiling flowers across the meadow
    flower(d, int(W * 0.135), int(H * 0.905), int(W * 0.052), (255, 107, 157))
    flower(d, int(W * 0.265), int(H * 0.965), int(W * 0.064), (255, 255, 255))
    flower(d, int(W * 0.475), int(H * 0.915), int(W * 0.055), (255, 159, 28))
    flower(d, int(W * 0.635), int(H * 0.975), int(W * 0.066), (177, 132, 255))
    flower(d, int(W * 0.815), int(H * 0.905), int(W * 0.054), (255, 93, 143))
    flower(d, int(W * 0.925), int(H * 0.965), int(W * 0.046), (255, 214, 90))
    flower(d, int(W * 0.385), int(H * 0.845), int(W * 0.034), (255, 140, 170),
           face=False)
    flower(d, int(W * 0.735), int(H * 0.835), int(W * 0.032), (140, 220, 255),
           face=False)

    # grass tufts on the front hill
    for gx, gy, gs in [(0.06, 0.86, 0.020), (0.20, 0.99, 0.024), (0.36, 0.94, 0.020),
                       (0.55, 0.86, 0.018), (0.58, 0.99, 0.024), (0.71, 0.92, 0.020),
                       (0.88, 0.86, 0.018), (0.97, 0.93, 0.020)]:
        x, y, s = int(W * gx), int(H * gy), int(W * gs)
        for dx in (-0.7, 0.0, 0.7):
            d.line([(x + dx * s, y), (x + dx * s * 1.7, y - s * 1.5)],
                   fill=GRASS_DARK, width=max(3, int(0.16 * s)))

    # butterflies + floating hearts + sparkles
    butterfly(d, int(W * 0.60), int(H * 0.20), int(W * 0.045), (255, 107, 157))
    butterfly(d, int(W * 0.135), int(H * 0.44), int(W * 0.036), (255, 159, 28))
    heart(d, int(W * 0.575), int(H * 0.40), int(W * 0.052), HEART_A)
    heart(d, int(W * 0.44), int(H * 0.575), int(W * 0.034), HEART_B)
    heart(d, int(W * 0.065), int(H * 0.615), int(W * 0.034), HEART_B)
    sparkle(d, int(W * 0.50), int(H * 0.115), int(W * 0.026))
    sparkle(d, int(W * 0.955), int(H * 0.30), int(W * 0.020))
    sparkle(d, int(W * 0.205), int(H * 0.565), int(W * 0.018), (255, 170, 80))

    return img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)


def main():
    out_dir = "/output"
    out_path = os.path.join(out_dir, "entry.png")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError:
        out_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.png")

    try:
        img = scene()
        img.save(out_path, format="PNG")
    except ImportError:
        # Pillow missing in the sandbox: ship the identical pre-rendered
        # image bundled next to this file (bytes are fixed, so the
        # two-runs-same-bytes rule still holds).
        bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "happy.png")
        shutil.copyfile(bundled, out_path)
    print("wrote", out_path)


if __name__ == "__main__":
    sys.exit(main())
