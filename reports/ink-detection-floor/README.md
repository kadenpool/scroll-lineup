# An ink detection floor for the public 9 um ink models (pre-registered; runs pending)

When the public 9 um ink models find nothing on an unread scroll, is that "no ink", or "no ink recovered yet"? The
challenge's 2026 Open Problems page asks exactly this for June 2027. This folder measures it directly: real ink from
PHerc0139, where the text is read, is planted into papyrus at graded strength, the same public models are run, and
the weakest ink they still recover is found. Every claim is limited to ink like PHerc0139's.

**Status: pre-registered; the day-1 run has not started.** The rules, the windows and the code below were published
before any result was seen. Results will be added beside them, with any change to the rules as a dated amendment in
`PREREG.md`. The rules were revised before publication, after three independent reviews and a dry run; `PREREG.md`
says what changed and why, and the second and third reviews are here as returned (`REVIEW2.md`, `REVIEW3.md`).
`PREREG.md` also states one mistake: a smoke run of an earlier version of the code was started by accident before
publication; its output has not been opened and is not used.

| file | what it is |
|---|---|
| `PREREG.md` | the rules: data, models, windows, the two plants and their shams, the readout, the gates |
| `prep_day1.py` | chooses every day-1 window by those rules, on segments the models were not trained on |
| `day1/windows.json`, `day1/masks.npz` | the chosen windows, their sheet profiles and registrations, and the letter masks |
| `floor_kernel.py` | the Kaggle job for day 1, byte for byte what runs |
| `read_day1.py` | reads a finished run and recomputes every gate apart from the Kaggle job's own code |
| `REVIEW2.md`, `REVIEW3.md` | the second and third independent reviews, before publication, as returned |
| `day1/plant_check.png` | one dry-run target: the letters in place, the clean target, both plants, the transplant and both shams at s = 1 |

Day 1 asks only whether the method works: do planted letters read at full strength, and read like the same letters
moved whole into the same papyrus, through the same model, while shams of the same shape read like nothing? Nothing is claimed about any other scroll unless the
day-1 gates pass.

*Written with Claude Code under my direction.*
