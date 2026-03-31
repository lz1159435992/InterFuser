# Release Checklist

Use this checklist before publishing a public artifact release.

## Attribution

1. Confirm `CITATION.cff` repository URL and metadata.
2. Confirm third-party attribution notes for `experiments/*/pipeline` and `third_party/*`.

## Reproducibility

1. Verify `scripts/run/reproduce_main_results.sh` works for the intended release profiles.
2. Verify `scripts/merge/merge_results.py` produces processed indexes.
3. Ensure `docs/EXPERIMENT_MATRIX.md` maps paper tables/figures to scripts and outputs.
4. Ensure run metadata/provenance guidance is documented.

## Data and Artifacts

1. Confirm no large private datasets/checkpoints are committed.
2. Confirm `docs/DATA_ACCESS.md` and external data paths are up to date.
3. Include representative sample outputs in `results/processed` or `results/tables` if needed.

## Paper Source

1. Verify `paper/tex` compiles (`build.sh` or `build.ps1`).
2. Ensure references and class files required for build are present.
