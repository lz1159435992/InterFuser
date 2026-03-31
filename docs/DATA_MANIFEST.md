# Data Manifest

This document defines where each dataset/artifact should live, whether it can be redistributed, and how it maps to paper experiments.

## Scope Mapping

- RQ1: KITTI perception consistency (`experiments/kitti/*`)
- RQ2: Udacity CH2 control consistency (`experiments/udacity/*`)
- RQ3: CARLA system consistency (`experiments/carla/*`, `third_party/interfuser_project`, `third_party/lmdrive`)
- Appendix: Image quality validation (`experiments/common/image_quality_validation/*`)

## Distribution Policy

- `GitHub`:
  - Include code, configs, wrappers, docs, table/figure generation scripts.
  - Include only small sample artifacts where necessary.
  - Do not include large raw/derived datasets.
- `Zenodo`:
  - Include reproducibility artifacts that are large but redistributable by project policy.
  - Include manifest + checksums for every uploaded bundle.
- Third-party official datasets (e.g., KITTI/Udacity raw data):
  - Prefer download instructions and path conventions.
  - Do not re-upload unless license explicitly allows redistribution.

## Path-Level Manifest

| Path | Category | Expected Content | Publish to GitHub | Publish to Zenodo |
|---|---|---|---|---|
| `data/kitti/raw/` | external dataset | KITTI raw/offical data | No | Usually No (license-sensitive) |
| `data/ch2/raw/` | external dataset | Udacity CH2 raw data | No | Usually No (license-sensitive) |
| `data/**/augmented/` | derived data | generated enhanced inputs | No | Yes (if needed for reproducibility) |
| `experiments/kitti/pipeline/tools_py/` | code | KITTI generation/eval scripts from source mirrors | Yes | Optional |
| `experiments/udacity/pipeline/udacity/` | code/config | Udacity eval scripts + docker configs (without outputs) | Yes | Optional |
| `experiments/common/image_quality_validation/tools_py_2026/` | code | 2026 image-quality validation scripts | Yes | Optional |
| `third_party/process_methods/` | code | SR/FI/DN method integrations (without heavy artifacts) | Yes | Optional |
| `results/raw/` | run output | raw run outputs | No (except tiny samples) | Yes |
| `results/processed/` | processed output | merged csv/json used for tables/figures | Yes | Yes |
| `results/tables/`, `results/figures/` | paper artifacts | final table/figure assets | Yes | Yes |
| `provenance/` | metadata | commit/env/hardware/run metadata | Yes | Yes |

## Required Files Before Release

- `docs/ZENODO_RELEASE_PLAN.md`
- `SHA256SUMS` for each Zenodo bundle
- `MANIFEST.csv` with:
  - relative path
  - bytes
  - sha256
  - source category (`raw`, `derived`, `code`, `result`)
  - linked RQ (`RQ1`, `RQ2`, `RQ3`, `Appendix-IQV`)
