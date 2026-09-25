# Blind check 1: result (scored 13:46 AEST, 03:46 UTC, 25 Sep 2026, exactly as BLIND1_DESIGN.md fixed it)

Kaden answered all 36 pictures on the private page (answers as the page saved them, `blind1/answers.json`). The
key's sha256 equals the one recorded before he saw the page (`f32b594e...`), and the key was committed, privately,
only after the answers.

| pictures (seed43_step060000, forward) | said "letters" |
|---|---|
| sham at s = 1 (no letters, the same shape) | 6 of 12 |
| planted at s = 1 | 8 of 12 (one-sided Fisher exact against the shams, p = 0.34) |
| planted at s = 0.5 | 5 of 12 (p = 0.79) |

By eye, the planted letters in this checkpoint's output were not told apart from shams of the same shape at either
strength. This fits day 3's readout for the same checkpoint: seed43_step060000 failed its checks on PHerc0846B (no
floor), and its planted letters read at median AUC 0.664 even at full strength. The checkpoint was fixed in the
design before day 3's full run was seen (its one-window smoke run had been read). One reader, 36
pictures; every answer is in `blind1/score.txt`.

(Reworded for publication on 25 Sep: the time zone, and "before any day-3 result" narrowed to the full run's;
the numbers are unchanged.)
