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

Strategy (three-strategy championship winner, fused): a vision judge
compares entries pairwise and picks the one that makes it "happier",
so the picture bets everything on the fastest, strongest happiness
signal there is: ONE enormous laughing sun-face (giant open laugh,
huge rosy cheeks, closed happy eyes) filling the frame on a bold,
saturated orange sunburst that radiates warmth. Grafted in from the
runner-up strategies: a small spray of hearts bubbling up beside the
face (joy overflowing, from the baby-elephant entry) and one tiny
smiling daisy on a green mound in each bottom corner (from the meadow
entry) for charm. No text (text renders badly and reads as noise).
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
INK = (80, 44, 30)             # warm dark brown for the face
CORE = (255, 216, 60)          # sun-face gold
EDGE = (255, 176, 0)           # sun-face rim
RAY_A = (255, 190, 32)
RAY_B = (255, 214, 74)
CHEEK = (255, 104, 116)
CHEEK_HI = (255, 152, 160)
BURST_A = (255, 132, 48)       # deep warm orange
BURST_B = (255, 162, 66)       # lighter warm orange
HEART_A = (255, 64, 100)
HEART_B = (255, 112, 150)
MOUND = (86, 178, 74)
STEM = (40, 134, 54)


# ---------------------------------------------------------------- helpers
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


def mini_flower(draw, cx, base_y, s, petal):
    """One tiny smiling daisy (from the meadow strategy), stem + face."""
    top_y = base_y - 2.6 * s
    draw.line([(cx, base_y), (cx, top_y)], fill=STEM, width=max(3, int(0.16 * s)))
    draw.ellipse([cx - 0.80 * s, base_y - 1.05 * s, cx - 0.05 * s, base_y - 0.68 * s],
                 fill=STEM)
    draw.ellipse([cx + 0.05 * s, base_y - 0.80 * s, cx + 0.80 * s, base_y - 0.42 * s],
                 fill=STEM)
    for k in range(8):
        a = math.radians(k * 45)
        px, py = cx + 0.78 * s * math.cos(a), top_y + 0.78 * s * math.sin(a)
        draw.ellipse([px - 0.46 * s, py - 0.46 * s, px + 0.46 * s, py + 0.46 * s],
                     fill=petal)
    draw.ellipse([cx - 0.72 * s, top_y - 0.72 * s, cx + 0.72 * s, top_y + 0.72 * s],
                 fill=(255, 217, 61))
    # dot eyes + tiny smile
    for ex in (-0.24 * s, 0.24 * s):
        draw.ellipse([cx + ex - 0.075 * s, top_y - 0.20 * s,
                      cx + ex + 0.075 * s, top_y - 0.02 * s], fill=INK)
    draw.arc([cx - 0.26 * s, top_y - 0.02 * s, cx + 0.26 * s, top_y + 0.34 * s],
             start=10, end=170, fill=INK, width=max(3, int(0.08 * s)))
    for chx in (-0.44 * s, 0.44 * s):
        draw.ellipse([cx + chx - 0.13 * s, top_y + 0.10 * s,
                      cx + chx + 0.13 * s, top_y + 0.26 * s], fill=CHEEK)


def scene():
    from PIL import Image, ImageDraw
    cx, cy = int(W * 0.5), int(H * 0.50)
    img = Image.new("RGB", (W, H), BURST_A)
    d = ImageDraw.Draw(img)

    # radiating sunburst wedges
    R = int(W * 0.78)
    for i in range(16):
        a0 = i * 22.5 - 11.25
        d.pieslice([cx - R, cy - R, cx + R, cy + R], start=a0, end=a0 + 22.5,
                   fill=BURST_B if i % 2 == 0 else BURST_A)

    # warm glow halo behind the face
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    fr = int(W * 0.375)
    for k, alpha in [(1.30, 40), (1.18, 56), (1.08, 72)]:
        gd.ellipse([cx - fr * k, cy - fr * k, cx + fr * k, cy + fr * k],
                   fill=(255, 240, 170, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)

    # short, fat rays hugging the face
    for i in range(12):
        a = math.radians(i * 30 + 15)
        r1, r2 = fr * 1.05, fr * (1.30 if i % 2 == 0 else 1.20)
        d.line([(cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                (cx + r2 * math.cos(a), cy + r2 * math.sin(a))],
               fill=RAY_A if i % 2 == 0 else RAY_B, width=int(fr * 0.115))

    # the enormous face
    d.ellipse([cx - fr, cy - fr, cx + fr, cy + fr], fill=EDGE)
    ri = int(fr * 0.90)
    d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=CORE)

    # raised joyful brows
    for sx in (-1, 1):
        ex = cx + sx * int(fr * 0.40)
        d.arc([ex - int(fr * 0.21), cy - int(fr * 0.52),
               ex + int(fr * 0.21), cy - int(fr * 0.30)],
              start=195, end=345, fill=INK, width=int(fr * 0.045))

    # huge closed happy eyes (thick inverted-U arcs)
    for sx in (-1, 1):
        ex = cx + sx * int(fr * 0.40)
        ey = cy - int(fr * 0.10)
        d.arc([ex - int(fr * 0.20), ey - int(fr * 0.13),
               ex + int(fr * 0.20), ey + int(fr * 0.13)],
              start=180, end=360, fill=INK, width=int(fr * 0.062))

    # giant rosy cheeks
    for sx in (-1, 1):
        chx = cx + sx * int(fr * 0.66)
        chy = cy + int(fr * 0.24)
        d.ellipse([chx - int(fr * 0.185), chy - int(fr * 0.115),
                   chx + int(fr * 0.185), chy + int(fr * 0.115)], fill=CHEEK)
        d.ellipse([chx - int(fr * 0.11), chy - int(fr * 0.065),
                   chx + int(fr * 0.02), chy + int(fr * 0.005)],
                  fill=CHEEK_HI)

    # the enormous open laugh, tongue and all
    sr = int(fr * 0.50)
    my = cy + int(fr * 0.16)
    d.pieslice([cx - sr, my - int(sr * 0.52), cx + sr, my + int(sr * 0.98)],
               start=4, end=176, fill=INK)
    d.pieslice([cx - int(sr * 0.60), my + int(sr * 0.30),
                cx + int(sr * 0.60), my + int(sr * 0.86)],
               start=4, end=176, fill=(255, 106, 128))

    # hearts bubbling up beside the face (from the elephant strategy)
    heart(d, int(W * 0.888), int(H * 0.345), int(W * 0.026), HEART_B)
    heart(d, int(W * 0.918), int(H * 0.268), int(W * 0.034), HEART_A)
    heart(d, int(W * 0.882), int(H * 0.198), int(W * 0.027), HEART_B)
    heart(d, int(W * 0.922), int(H * 0.140), int(W * 0.021), HEART_A)
    heart(d, int(W * 0.082), int(H * 0.088), int(W * 0.046), HEART_A)

    # tiny smiling daisies on green mounds in the bottom corners
    # (from the meadow strategy)
    d.ellipse([-int(W * 0.16), int(H * 0.90), int(W * 0.20), int(H * 1.10)],
              fill=MOUND)
    d.ellipse([int(W * 0.80), int(H * 0.90), int(W * 1.16), int(H * 1.10)],
              fill=MOUND)
    mini_flower(d, int(W * 0.058), int(H * 0.945), int(W * 0.030), (255, 99, 150))
    mini_flower(d, int(W * 0.942), int(H * 0.945), int(W * 0.030), (255, 154, 20))

    # sparse sparkles
    sparkle(d, int(W * 0.50), int(H * 0.045), int(W * 0.022), (255, 235, 170))
    sparkle(d, int(W * 0.075), int(H * 0.42), int(W * 0.024))
    sparkle(d, int(W * 0.935), int(H * 0.56), int(W * 0.020))

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
