# Seventh independent review: the day-2 job (hecate) and a first draft of amendment 2 (25 Sep 2026)

Reviewer: a separate Claude Code agent, read-only, asked whether only the model changed from the day-1 job, whether
the resampling and the masks line up, whether the job refuses anything but the pinned model, and whether the draft
states the held-out evidence fairly. Verdict and findings as returned (lightly shortened, private paths removed), each
followed by what was done.

NOT READY

1. BLOCKER. The smoke run scores the six reference windows, which the full run's G0 reads, and the watcher would
   print its gate table: reading it before the rules are published breaks "fixed before any day-2 model output is
   seen". **Done:** the smoke outputs were read only by a script that prints no score (status, errors, counts,
   shapes, timings); the amendment says so.
2. BLOCKER. The run is far longer than "about an hour": about 426 GFLOP a patch, 1,922 patches a job, 174 jobs,
   roughly 5 hours on two T4s at full float32 speed, more with bfloat16, which T4s only emulate; and a run stopped
   by Kaggle's 12-hour limit saves nothing. **Done:** float32 (the card's default), 32 patches a batch; the full run
   waits for a timed smoke, and is split by target if it would run past about 10 hours.
3. SHOULD. `ndimage.zoom` pins the end voxels, so the depth step was 9.72 um, not 9.6, and the last plane, row and
   column came out 0. **Done:** `affine_transform` with output voxel i at input i x 9.6 / 9.362, on a 27 x 998 x 998
   grid wholly inside the input; tested: a test block lands where expected, masks within a pixel, edges not zero.
4. SHOULD. The day-1 windows' measured sheets are at layers 10 to 14, not on plane 14, so the letters sit off the
   middle of both of hecate's windows. **Done:** stated (about 2 planes forward, 3 reversed, inside both).
5. SHOULD. The held-out caveat was too soft: our segments' folders hold 2.4 um renders and model predictions; the
   9.6 um model learned from the 2.4 um model's outputs; and our masks come from the `ink_canonical_2um` family,
   hecate's base model. **Done:** all three stated.
6. SHOULD. The day-1 reader cannot score the kept 499 px maps with its 512 px masks. **Done:** each job's core masks
   on the new grid are kept beside its maps, and the amendment says the kept maps are 499 px.
7. SHOULD. The job recorded its inputs' sha256 but did not stop on a mismatch. **Done:** it stops unless they are
   day 1's.
8. NOTE. Leftovers: the runner skips the command line's spacing and uint8 checks (harmless as built); the clipped
   share and `layers` still use day 1's [4, 25); the preview stretch assumes ink_9um's range; the push script built
   the smoke and the full run in one folder. **Done:** the push script uses one folder per kind of run; the rest
   stated here.

Checked and right: only the model, its input format and the scoring grid change, and `make_day2.py` regenerates the
job byte for byte; the pushed notebook holds the job; `hecate.py` matches the pinned revision and the checkpoint's
sha256 and size match Hugging Face's; the image and mask grids align within half a pixel; the plane windows match
`predict`; the runner matches the command line's path (divide by 255, stride 32, reverse); the gates work with one
checkpoint. The smoke had not finished; no number was read.
