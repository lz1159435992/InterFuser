# Zenodo Release Plan

This plan defines how to publish a complete reproducibility package while keeping GitHub lightweight.

## Release Model

1. Create a GitHub release tag (`vX.Y.Z`) for code.
2. Upload matching Zenodo bundles tied to that release.
3. Keep one-to-one mapping:
   - GitHub tag -> Zenodo record version -> paper appendix references.

## Recommended Bundles

- `intuitiontester-code-vX.Y.Z.tar.gz`
  - Source code snapshot (same commit as GitHub release).
- `intuitiontester-rq1-rq2-derived-data-vX.Y.Z.tar.gz`
  - KITTI/Udacity generated inputs + processed outputs.
- `intuitiontester-rq3-derived-data-vX.Y.Z.tar.gz`
  - CARLA processed outputs and route-level summaries.
- `intuitiontester-reference-results-vX.Y.Z.tar.gz`
  - Final CSV/JSON for tables and figures.

Split by size if any single archive becomes too large.

## Pre-Publish Checklist

- Verify all scripts run with relative paths.
- Ensure no host/user/IP identifiers remain in public docs/scripts.
- Ensure no restricted raw datasets are bundled.
- Generate checksums and manifest:
  - `SHA256SUMS`
  - `MANIFEST.csv`
- Confirm `docs/DATA_MANIFEST.md` matches actual bundle contents.

## Citation and Traceability

- Add Zenodo DOI badge to `README.md` after publication.
- Record:
  - Git commit hash
  - release tag
  - Zenodo DOI
  - bundle checksum
in `provenance/`.

## Legal/Licensing Caution

- Do not redistribute third-party raw datasets without explicit permission.
- For external datasets, publish:
  - fetch instructions
  - expected folder layout
  - checksum verification commands.
