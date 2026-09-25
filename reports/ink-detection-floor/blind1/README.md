# Blind check 1: can a person see the planted letters in the model's output?

Kaden looked at 36 maps of one public ink model's output on PHerc0846B from day 3 (`seed43_step060000`, forward),
shuffled, and answered one question for each: letters, or parts of letters? Twelve had PHerc0139 letters planted at
full strength, twelve at half strength, and twelve were shams of the same shape filled with other PHerc0846B papyrus.
He said "letters" for 8 of the 12 full-strength plants, 5 of the 12 half-strength ones and 6 of the 12 shams: by eye,
the planted letters were not told apart from the shams (one-sided Fisher exact p = 0.34 and 0.79). This fits day 3's
readout for the same checkpoint, which failed its checks on PHerc0846B. With 6 of the 12 shams called letters, 11 or
12 of the 12 plants would have had to be called letters to reach p < 0.05. The page recorded the 36 answers in about
48 seconds (`answer_times.json`). No letters of PHerc0846B's own are claimed here or anywhere in this work: the only
letters put into these pictures were planted.

## Take it yourself

The pictures are `img/01.png` to `img/36.png`: each is 512 by 512 pixels of the model's output, stretched from 0.25
(black) to 0.75 (white). Without opening `key.json` or `score.txt`, write "y" or "n" for each in a file shaped like
`answers.json`, then, from the folder above this one, run `python3 blind1_score.py <your answers .json>
blind1/key.json` (it needs scipy).

## The record

- The design, fixed on 24 Sep at 22:28 AEST, before any of day 3's full run was fetched: `../BLIND1_DESIGN.md`. Day
  3's one-window smoke run, whose output holds the maps behind pictures 04, 16 and 32, had been read by Claude at 21:41
  (its numbers read, not used) and its maps used at 22:33 to test the builder; they were not shown to Kaden. The
  design's "before any day-3 result" means the full run's. By his own account (25 Sep), Kaden had seen none of these
  maps before the check, and had not read the design, which gives 12 of each kind, before answering.
- The key's sha256, recorded at 22:58 AEST that evening, before Kaden saw the page: `KEY_SHA256.txt`. Kaden answered
  on 25 Sep; `key.json` was committed only after that, and its sha256 equals the recorded one. The result as scored:
  `../BLIND1_RESULT.md` (reworded for publication on 25 Sep; its numbers unchanged), and every answer beside the key
  in `score.txt`.
- These times come from our private repository's history, which is not public. What anyone can check: `key.json`'s
  sha256 against `KEY_SHA256.txt`; `score.txt`, from `answers.json` and `key.json` with `../blind1_score.py`; and the
  pictures, which `../blind1_build.py` rebuilds byte for byte (with numpy 2.5.2 and Pillow 12.3.0) from the day-3
  run's window maps for this checkpoint (`maps_seed43_step060000.npz`, in the `ink-floor-day3-maps` release) and
  `../day3/run/results.json`, placed together in a folder's `out/`.
- Limits, from the design: one reader and 36 pictures; each window appears three times, so its three maps can be
  compared; the reader knows the project and what PHerc0139 letters look like.
- The page (`../blind1_page.html`, a template) showed the pictures in the claude.ai app and saved each answer with its
  time in the page's own storage; `answers.json` is those answers.

*Built and written with Claude Code under my direction.*
