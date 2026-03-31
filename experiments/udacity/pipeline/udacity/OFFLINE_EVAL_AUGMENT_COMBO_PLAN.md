# Offline Evaluation Augmentation Combo Plan (CH2)

This file defines the publication-oriented plan for CH2 augmentation-combination experiments.

## Scope

- Dataset generation script: `experiments/udacity/pipeline/udacity/tools/gen_combo_dataset.py`
- Evaluation script: `experiments/udacity/pipeline/udacity/tools/run_combo_eval.py`
- Process method source root (published name): `third_party/process_methods`
- Output root (recommended): `results/raw/rq2`

## Pipeline Set

- Noise baselines: `GN8`, `GN16`
- Single methods: `A`, `B`, `C`
- Ordered pairs: `A->B`, `B->A`, `A->C`, `C->A`, `B->C`, `C->B`
- Ordered triples: `A->B->C`, `A->C->B`, `B->A->C`, `B->C->A`, `C->A->B`, `C->B->A`

## Data Layout (Repo-Relative)

- CH2 input: `data/ch2/input`
- Generated combo input: `data/ch2/input_combo`
- Model weights: `data/community-models`
- Evaluation outputs: `results/raw/rq2/ch2_main` or `results/raw/rq2/ch2_variant`

## Recommended Commands

Generate combo datasets:

```bash
bash scripts/data/prepare_augmented_inputs.sh --task ch2 --ch2-root ./data/ch2
```

Run CH2 offline evaluation matrix:

```bash
bash scripts/run/run_rq2_udacity.sh --profile paper-ch2-main -- \
  --ch2-root ./data/ch2 \
  --weights-root ./data/community-models \
  --pipelines all \
  --segments 1,2,3,4,5,6 \
  --resume
```

## Notes

- Keep this plan path-neutral for anonymized release.
- Do not use host-specific absolute paths in this document.
