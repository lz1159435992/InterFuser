# Contributing

Thanks for your interest in improving IntuitionTester.

## Scope

This repository contains:

- paper-aligned experiment scripts (RQ1/RQ2/RQ3)
- reproducibility wrappers and result aggregation scripts
- provenance and mapping documents for artifact traceability

## Development Rules

1. Keep mirrored upstream sources read-only.
2. Prefer adding adapters/wrappers instead of editing upstream snapshots directly.
3. Record source-to-target decisions in `docs/MERGE_MAP.md`.
4. Keep run outputs under `results/raw/<rq>/<run_id>/`.
5. Keep generated table/figure artifacts under `results/tables` and `results/figures`.

## Pull Request Checklist

1. Explain which RQ pipeline is affected.
2. Update `docs/EXPERIMENT_MATRIX.md` if table/figure mapping changes.
3. Add or update command examples in `README.md` if run interfaces change.
4. Add reproducibility notes when new dependencies are introduced.

## Reporting Issues

For bug reports, please include:

- command used
- environment (Python, CUDA, OS)
- stack trace or error log
- expected vs actual behavior
