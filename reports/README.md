# Reports

Write-ups of work done with this tool and around it, each with its data and a script that re-derives
its numbers from that data (`python3 trace_numbers.py` inside the folder, or the readers named below).

- [`ink-negative-controls/`](ink-negative-controls/): four controls that tell a real ink reading from
  papyrus texture, tested on PHerc0846A, PHerc0813 and PHerc0211. No letters were found on any of them.
- [`pherc1203-first-letters/`](pherc1203-first-letters/): a First Letters attempt on PHerc1203, a scroll
  with two scans and no published transform between them. No letters were found.
- [`ink-detection-floor/`](ink-detection-floor/): plants real PHerc0139 ink into papyrus to measure the weakest ink
  the public 9 um models still recover, pre-registered before any result was seen. On PHerc0846B one checkpoint
  detects PHerc0139-like ink from 0.87 of its full strength (median AUC 0.70) but does not read it clearly (0.80)
  even at full strength; the other fails its checks there. On PHerc0139 (day 2), the Vesuvius Challenge team's
  newer hecate 9.6 um model passes day 1's gates with the swap plant only narrowly (leaving out one window can flip
  it); whether its training saw these segments cannot be ruled out, and our letter masks come from the same family
  of models. Day 4, the floor on PHerc0483B at two scales, is pre-registered and its run pending. A blind check by
  eye is there too. `read_day1.py`, `read_day3.py` and `read_day4.py` recompute every gate and floor from the runs'
  own output.
- [`pherc0846b-surfaces/`](pherc0846b-surfaces/), [`pherc0490b-surfaces/`](pherc0490b-surfaces/) and
  [`pherc0483b-surfaces/`](pherc0483b-surfaces/): the first published surfaces on three First Letters scrolls with
  none in the open-data catalogue: twelve on PHerc0846B (97.30 cm2), three on PHerc0490B (23.42 cm2) and five on
  PHerc0483B (35.42 cm2), with previews and a script in each folder that re-derives its numbers. (gmDevi had
  screened a spiral fit of PHerc0483B with an ink model on 11 Sep, publishing its renders but not the surfaces.)

*Written with Claude Code under my direction.*
