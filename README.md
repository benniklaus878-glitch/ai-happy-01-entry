# Make the AI judge happy — make.fun bounty ai-happy-01

Entry for https://make.fun/bounty/ai-happy-01 ($250, 100 places, escrowed,
deadline 2026-11-14T16:00:00Z). Built for submission under the GitHub
account **benniklaus878-glitch** (submission itself happens separately).

## What the grader expects (from https://make.fun/api/competitions)

- A public GitHub repo owned by the entrant, created after the competition
  opened, under an OSI-approved license (MIT `LICENSE` included), with the
  program at `main.py` (Python) in the repo root, plus the AI coding-agent
  transcripts of the building sessions, uploaded with each submission.
- The program writes **one image to `/output/entry.png`**.
- The image must be a whole PNG or JPEG, **at most 1 MiB** and at most
  **1024×1024 px**.
- **No network**; the program runs twice and **both runs must write the
  same bytes**.
- An AI judge compares entries' images two at a time and picks the one
  that makes it happier; the 100 best win rates share the prize.
- At most 10 submissions/day, 20 total; the last one before the deadline
  is the final entry.

## Approach

`main.py` draws the image from scratch at runtime with Pillow
(supersampled 2048×1024→1024). Fully deterministic: fixed geometry, no
randomness, no clock, no network — two runs produce byte-identical PNGs
(verified: sha256 `ced80e8c…` on repeated runs).

The picture stacks the strongest universal "happy" signals a vision
judge responds to, in one bold, uncluttered composition:

- a huge laughing sun (closed happy eyes, open smile, rosy cheeks),
- a six-band rainbow landing behind rolling green hills,
- six smiling flowers (plus two plain ones) across the meadow,
- fluffy clouds (one smiling), floating hearts, butterflies, sparkles,
- bright warm saturated colours, sky gradient to a warm horizon,
- **no text** — lettering renders badly and reads as noise to a judge.

If Pillow were missing in the grading sandbox, `main.py` falls back to
copying the bundled `happy.png` (the identical pre-rendered image), so
the entry can never fail on a missing dependency — the output bytes are
the same either way (also verified).

## Local test

```
python3 main.py        # writes /output/entry.png
```

Verified output: PNG, 1024×1024, RGB, 197,020 bytes (< 1 MiB),
byte-identical across runs and across the Pillow/fallback paths.
