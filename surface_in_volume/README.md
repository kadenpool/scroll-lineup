# Do published surfaces sit inside the volume they name?

The survey behind the figure in [ScrollPrize/villa#1717](https://github.com/ScrollPrize/villa/pull/1717): first run on 8 Sep 2026
(243 of 833), and re-run on the whole catalogue on 26 Sep 2026 (252 of 898).

Each transformed surface in the open-data catalogue is named `<segment>-on-<volume>-<voxel>um.tifxyz`: its
own filename says which volume its x/y/z grids are in. `surface_in_volume.py` reads every such surface's
grids (every fourth point on each axis, missing points excluded) and checks each point against the shape
of that volume. A point outside is a published coordinate that addresses no published voxel.

## The result, 26 Sep 2026 (the re-run)

903 surface/volume pairs; 898 measured, 5 not (each has fewer than 50 valid points at this sampling, too few to
measure). **252 of the 898 have more than 0.1 % of their points outside the volume they name (28 %)**, on eight
scrolls, with a median of 77 % of points inside among them and the worst at 29 %. Every one of the 833 pairs
measured on 8 Sep is still published and gives exactly the same fraction inside again; the other 65 are new since,
and 9 of them (7 on PHerc0009B, 2 on PHerc0841) have more than 0.1 % of their points outside. The run used the script in this folder
unchanged (sha256 `eb279f0d47245d44...`), in four shards on a Kaggle CPU session, from 11:55 to 12:14 UTC. Its
output is in `results_2026-09-26/`, and this re-counts the figure from it:

```
python3 surface_in_volume.py --count results_2026-09-26/*.jsonl
```

## The result, 8 Sep 2026 (the first run)

838 surface/volume pairs; 833 measured, 5 not (each has fewer than 50 valid points at this sampling, too few to measure). **243 of the 833 have more than 0.1 % of their
points outside the volume they name (29 %).** The run's output is in `results_2026-09-08/`, three shards
(`--shard 0/1/2 --nshards 3`), and this re-counts the figure from it:

```
python3 surface_in_volume.py --count results_2026-09-08/*.jsonl
```

## Checking it against today's data

`--only SAMPLE SEGMENT VOLUME` runs the check on one pair. On 22 Sep it was run on two, the smallest surface
that sits inside (PHerc0814 `20260226110425` on `20250804134230`) and the smallest that does not (PHerc1447
`20250502180748` on `20250521151220`, 5.3 % outside); both matched the 8 Sep record exactly. The full
survey downloads every transformed surface's grids, so it is slow on a home connection: the 8 Sep run was split into
three shards, and the 26 Sep re-run took 18 minutes in four shards on Kaggle.

The catalogue's own `overlap_ratio` is a different measure of the same question; #1717 gives both and
says which is which. Needs numpy and Pillow; everything is read anonymously from the public bucket.
