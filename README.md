# recsys-gen

`recsys-gen` is an open recommender-system benchmark scaffold for large-scale interaction datasets such as Yambda. The current implementation focuses on the v0.1 research core: reproducible dataset preparation, temporal splits, negative sampling, baseline recommenders, SASRec, offline ranking metrics, and MLflow/DVC experiment wiring.

## Project layout

```text
.
├── configs/                # Dataset and experiment configs
├── data/                   # External/raw/interim/processed artifacts
├── docs/                   # Benchmark documentation
├── experiments/            # Run manifests and notes
├── scripts/                # Small developer helpers
├── src/recsys_gen/         # Benchmark package
├── tests/                  # Unit and smoke tests
└── dvc.yaml                # Reproducible benchmark pipeline
```

## v0.1 scope

- Canonical interaction schema normalization
- Temporal train/validation/test splitting
- Sequence building and negative sampling
- `ItemKNN`, matrix factorization, and `SASRec`
- `Recall@K`, `NDCG@K`, `MRR`, `HitRate`, `Coverage`, and `Diversity`
- MLflow tracking and DVC stages

## Quick start

```bash
make requirements
make test
uv run python -m recsys_gen.training.train --config configs/sasrec_yambda.yaml
```

## Dataset assumptions

The repo does not vendor Yambda. Point configs at local parquet files with interaction columns that can be mapped into the canonical schema:

- `user_id`
- `item_id`
- `timestamp`
- `target`
- `event_type`
- optional `item_embedding`

## Next milestones

- v0.2: FAISS candidate retrieval and a minimal recommendation API
- v0.3: Additional sequential and generative recommenders
