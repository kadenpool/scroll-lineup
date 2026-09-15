# The same pairs, on a second software stack

Every run in `results/` and `robustness/` was made on machine A:
Python 3.12.3 with numpy 2.5.3 and scipy 1.18.1, on x86-64 Linux.

The `transform.json` files here are the same pairs run again on
machine B: Python 3.9.6 with numpy 2.0.2 and scipy 1.13.1, on arm64
macOS. Nothing else changed. No versions were pinned in either case;
each set is what a plain `pip install numpy scipy fsspec s3fs Pillow`
resolved to on that interpreter.

They are committed so the cross-stack claim in `VALIDATION.md` can be
checked from this repository alone, with no network and no scan data.
`tests/test_offline.py` re-derives it on every run: for each pair it
takes the two matrices, maps the eight corners of the moving volume
through both, and requires the largest disagreement to be under
0.01 um.

The md5s differ. The answers do not.
