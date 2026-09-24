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
  even at full strength; the other fails its checks there. `read_day1.py` and `read_day3.py` recompute every gate and floor from the runs' own output.
- [`pherc0846b-surfaces/`](pherc0846b-surfaces/): seven surfaces grown on PHerc0846B, a First Letters scroll with
  no surfaces in the open-data catalogue: 57 cm2 in all, with previews.

*Written with Claude Code under my direction.*
