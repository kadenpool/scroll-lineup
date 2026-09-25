# Blind check 1: can a person see the planted letters in the models' output? (design, fixed before any day-3 result)

Written 24 Sep 2026 while the day-3 full run (Kaggle `squiffymccat/ink-floor-day3`, version 1) was still running and
before any of its output was fetched or opened. Kaden asked for it the same evening ("yes do all of that").

## Question

On PHerc0846B, the day-3 floor says how strong the planted ink must be before the models' AUC passes 0.70 and 0.80.
An AUC is not what a reader sees. This check asks the reader's question directly: shown the model's output map of a
window, does Kaden see letters or parts of letters, when letters were planted at full strength, at half strength, or
not at all (a sham of the same shape, filled with blank papyrus)?

## Material (fixed now)

- The day-3 full run's kept maps (`maps_<checkpoint>.npz`: the 512 x 512 core of each scored job's map), checkpoint
  `seed43_step060000` (the higher day-1 reference median, 0.782), forward direction (its primary direction).
- For each of the 12 targets, three maps: planted at s = 1, planted at s = 0.5, and the PHerc0846B sham at s = 1.
  36 images.
- Each shown as the job's own previews are: value 0.25 to 0.75 stretched to black to white, grey, 512 x 512, no mask
  outline, no label but a number.
- Order: numpy `default_rng(20260925).permutation(36)`. The key (number to target and condition) is written to a
  private file and its sha256 recorded before the images are shown; the page holds only the numbers.
- If the run fails, or its readout is not read for this checkpoint, the check is still run on whatever maps exist,
  and that is stated; no other checkpoint or direction is substituted.

## Procedure

- One sitting, no time limit, no going back. For each image: "Do you see letters, or parts of letters?" yes or no.
- Kaden has not seen any of these maps, and is told only that some have letters and some do not, not how many.

## Readout (fixed now)

- Hits at s = 1 and at s = 0.5: the share of the 12 planted images answered yes. False alarms: the share of the 12
  shams answered yes.
- For each strength, a one-sided Fisher exact test of hits against false alarms (12 against 12); p below 0.05 means
  a person sees the planted letters at that strength more often than in shams.
- Reported beside the day-3 floor for the same checkpoint, with every answer and the key.

## Limits (stated now)

- One reader, 36 images: this shows whether the letters are visible to one careful person, not how often.
- Each window appears three times, so the reader can compare its three maps; a check with one map per window would
  be cleaner, but gives only 4 of each kind.
- The reader knows the project and what PHerc0139 letters look like.
