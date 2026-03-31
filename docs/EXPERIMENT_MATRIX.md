# Experiment Matrix (Paper Traceability)

This file links paper claims/tables to scripts, configs, and result artifacts.

## RQ1: KITTI Detection Consistency

| Paper Artifact | Section/Table | Script Entry | Configs | Raw Results | Final Output |
|---|---|---|---|---|---|
| Viol.(Det) summary | `eval.tex` Table RQ1 | `scripts/run/run_rq1_kitti.sh` (`original` / `paper-kitti-*`) | `configs/kitti/*.yaml` | `results/raw/rq1/...` | `results/tables/rq1_*.tex` |

## RQ2: Udacity Control Consistency

| Paper Artifact | Section/Table | Script Entry | Configs | Raw Results | Final Output |
|---|---|---|---|---|---|
| AUC + Viol.(Ctrl)\_1 summary | `eval.tex` Table RQ2 | `scripts/run/run_rq2_udacity.sh` (`original` / `paper-ch2-*`) | `configs/udacity/*.yaml` | `results/raw/rq2/...` | `results/tables/rq2_*.tex` |

## RQ3: CARLA System Consistency

| Paper Artifact | Section/Table | Script Entry | Configs | Raw Results | Final Output |
|---|---|---|---|---|---|
| Viol.(Path/Time/Safe/Sys) | `eval.tex` Table RQ3 | `scripts/run/run_rq3_carla.sh` (`original` / `paper-carla-*`) including InterFuser native and LMDrive native/sweep | `configs/carla/*.yaml` | `results/raw/rq3/...` (including `lmdrive/native_sweep/fullcover_native_20260320`) | `results/tables/rq3_*.tex` |

## Appendix Traceability

| Appendix Item | Source Script | Processed File | Note |
|---|---|---|---|
| Supplemental sensitivity curves | `scripts/plot/...` | `results/figures/...` | TODO |
