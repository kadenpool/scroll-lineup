# Which mesh a segment is rendered from: the picture

`mesh_choice.png` shows where each of two published meshes of PHerc0139 segment
`20250108000004-w029_2025010827` finds the challenge's labelled ink, in the 2.399 um scan, with the same
model and the same depth window. Only the mesh differs:

- coarse: the mesh made on the 9.362 um scan (187 um grid), carried into the 2.399 um scan by the
  catalogue's transform: AUC 0.857, finds 54.4 % of the labelled ink;
- fine: the mesh made on the 2.399 um scan (48 um grid), already in that scan's frame: AUC 0.897,
  finds 72.2 % of the labelled ink.

The four inputs are the two prediction maps for layers 40 to 61 (the window both arms score best at in
the depth sweep) and the labels mapped onto each render. `python3 plot_mesh_choice.py` redraws the picture
from them and refuses to write it unless the ink it finds matches those two percentages. The full result,
with the per-block test and the arm that separates the grid from the transform, is in `../README.md` and
in [ScrollPrize/villa#1845](https://github.com/ScrollPrize/villa/issues/1845).
