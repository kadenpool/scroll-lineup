| arm | checkpoint | dir | control (largest reference change) | clean | 0.25 | 0.5 | 1 | sham 0.25 / 0.5 / 1 | PHerc0139 sham 0.25 / 0.5 / 1 | checks | detection floor | clear floor |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a | seed42_step010000 | forward | 0.0000 (ok) | 0.484 | 0.509 | 0.555 | 0.661 | 0.476 / 0.491 / 0.519 | 0.485 / 0.492 / 0.413 | pass | above 1 | above 1 |
| a | seed43_step060000 | forward | 0.0000 (ok) | 0.520 | 0.519 | 0.504 | 0.603 | 0.497 / 0.483 / 0.540 | 0.476 / 0.460 / 0.339 | FAIL | not read | not read |
| b | seed42_step010000 | forward | 0.0000 (ok) | 0.494 | 0.500 | 0.539 | 0.691 | 0.491 / 0.487 / 0.513 | 0.473 / 0.470 / 0.439 | pass | above 1 | above 1 |
| b | seed43_step060000 | forward | 0.0000 (ok) | 0.472 | 0.473 | 0.525 | 0.604 | 0.451 / 0.453 / 0.524 | 0.458 / 0.480 / 0.334 | FAIL | not read | not read |

| arm A minus arm B, median over targets | dir | s = 0 | s = 0.25 | s = 0.5 | s = 1 | targets |
|---|---|---|---|---|---|---|
| seed42_step010000 | forward | -0.005 | +0.015 | +0.025 | -0.008 | 8 |
| seed43_step060000 | not read in both arms (A not read, B not read): no difference |

| scale references (arm B; not a gate) | dir | median AUC at 9.362 um | median AUC at 8.64 um | median A minus B |
|---|---|---|---|---|
| seed42_step010000 | forward | 0.754 | 0.774 | +0.008 |
| seed43_step060000 | forward | 0.782 | 0.775 | +0.007 |
