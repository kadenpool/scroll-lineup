# Do published surfaces sit inside the volume they name?

The survey behind the "243 of the 833" in [ScrollPrize/villa#1717](https://github.com/ScrollPrize/villa/pull/1717).

Each transformed surface in the open-data catalogue is named `<segment>-on-<volume>-<voxel>um.tifxyz`: its
own filename says which volume its x/y/z grids are in. `surface_in_volume.py` reads every such surface's
grids (every fourth point on each axis, missing points excluded) and checks each point against the shape
of that volume. A point outside is a published coordinate that addresses no published voxel.

## The result, 8 Sep 2026

838 surface/volume pairs; 833 measured, 5 not (fetch errors). **243 of the 833 have more than 0.1 % of their
points outside the volume they name (29 %).** The run's output is in `results_2026-09-08/`, three shards
(`--shard 0/1/2 --nshards 3`), and this re-counts the figure from it:

```
python3 surface_in_volume.py --count results_2026-09-08/*.jsonl
```

## Checking it against today's data

`--only SAMPLE SEGMENT VOLUME` runs the check on one pair. On 22 Sep it was run on two, the smallest surface
that sits inside (PHerc0814 `20260226110425` on `20250804134230`) and the smallest that does not (PHerc1447
`20250502180748` on `20250521151220`, 5.3 % outside); both matched the 8 Sep record exactly. The full
survey downloads every transformed surface's grids, so it is slow; that is why it ran in three shards.

The catalogue's own `overlap_ratio` is a different measure of the same question; #1717 gives both and
says which is which. Needs numpy and Pillow; everything is read anonymously from the public bucket.
