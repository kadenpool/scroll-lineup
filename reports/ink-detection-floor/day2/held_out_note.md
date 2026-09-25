**Held out, as far as can be known** (`PREREG.md`, amendment 2). None of our seven PHerc0139 segments is among the 11
PHerc0139 segments in the main folder of the Scroll Prize ink dataset, which hecate's model card says development
used; all seven sit in its `unused` folder, with renders and model predictions but no ink labels. One of our target
segments, w042, lies between two of those 11 (w041 and w043). Two things cannot be ruled out, and either could raise
hecate's scores on the references and the transplants: the 9.6 um model learned from its 2.4 um sibling's outputs on
renders where both scans were available, which PHerc0139 has, and the card does not list which segments were used;
and our letter masks come from the team's 2.4 um ink map, the `ink_canonical_2um` family hecate is built on.
