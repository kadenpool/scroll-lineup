# Third independent review of the ink detection floor, day 1 (24 Sep 2026, before publication)

Reviewer: a separate Claude Code agent, read-only, asked to check the fixes made after the second review, whether
they add a new problem, and whether the rules text matches the code. Verdict and findings as returned (lightly
shortened: file-and-line pointers kept, private paths removed); the response to each is in PREREG.md's "Revisions".

NOT READY

1. BLOCKER: day 1 can say GO when the planted letters read at chance. The transplant has the same k, depth shift,
   background and core cut as the plants. If moving the letters loses them, plants and transplant both read near
   0.5, so G1 passes; G0 passes on the references, and G2 and G3 pass on a flat curve. Run on made-up AUCs
   (reference 0.80, transplant and planted s = 1 0.53, shams 0.50), the kernel's gate code and read_day1.py both
   said GO on all four checkpoint/plant pairs. So "G0 and G1 together require the letters to read at s = 1" is
   false. Fix: add "median planted AUC at s = 1 at least 0.70" to G3, and reword section 1.
2. BLOCKER: the new windows did not exist yet: the re-pick had died on an S3 503 error, windows.json and masks.npz
   were still the 23 Sep files, yet the rules already said targets and shams were chosen again and donors did not
   change. Fix: finish the re-pick; then run check_windows.py, check_blank_registered.py and a byte-for-byte
   comparison of the donor records and masks against 23 Sep.
3. SHOULD: at the registered shifts the code tested only the core with its border, not the core alone, which the
   rules also promise. On the old windows the core alone was higher in 10 of 22, by up to 0.06 points. Fix: also
   take the inner share at each shift.
4. SHOULD: G1 can fail high for a reason unrelated to the letters (the transplant's negatives carry any ink the map
   missed; the plants' negatives do not). "G1 is read with that in mind" is not a rule, and the letters-only
   number was not pre-registered. The staging script published neither read_day1.py nor REVIEW2.md. Fix: say the
   AUC rule alone decides G1 and the letters-only number is reported beside it; stage both files.
5. SHOULD: the header ("before any planted run exists", "an independent review") contradicts the Revisions
   section. The smoke-run paragraph matches the record. Add that its output holds all six references, which are
   G0's numbers.
6. NOTE: provenance holds (Hugging Face public, not gated; revision 7109667e2607, the same as the copy saved on
   22 Sep). But the rules say "pinned, not main" with no exception, and the download has no retry. Fix:
   pre-register the revision and each checkpoint's sha256; add a retry.
7. NOTE: the clipped share counts the right voxels, reproduced from the raw chunks (0.0470, 0.0143, 0.0157 for
   additive s = 1, swap s = 1, transplant), but includes 7 layers the model never reads (over its 21 layers:
   0.0468, 0.0125, 0.0151). The rules quoted review 2's figure, which has a different denominator.
8. NOTE: the depth shift fills emptied layers with zero residual. A shift of -4 or less, or +5 or more, flattens a
   model layer across the transplant's whole core but only under the letters in the plants. The old windows'
   largest shift was 3.

Checked and right: the dry-run transplant equals swap s = 1 wherever the soft mask is 1 and equals the clean target
outside the core; pairing by target name in both the kernel and the reader; the swap weights at s = 0, 0.25, 0.5, 1;
the self-test passes and fails on the v3 swap and on a broken clip share; section 2's segment lists match villa's
config; no em or en dashes and no private paths in the rules.
