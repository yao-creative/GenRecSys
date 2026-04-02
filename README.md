# recsys-gen

`recsys-gen` is an open recommender-system benchmark scaffold for large-scale interaction datasets such as Yambda, MovieLens, Amazon Reviews, and Yelp. The current implementation focuses on a TorchRec-oriented retrieval core: reproducible dataset acquisition, normalization, temporal splits, retrieval example generation, two-tower training, offline ranking metrics, and MLflow/DVC experiment wiring.

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

## Current scope

- Acquisition and canonical interaction schema normalization
- Temporal train/validation/test splitting
- Retrieval example generation with split-safe user histories
- TorchRec-oriented two-tower retrieval training
- `Recall@K`, `NDCG@K`, `MRR`, `HitRate`, `Coverage`, and `Diversity`
- MLflow tracking and DVC stages

## Quick start

```bash
make requirements
make test
uv run python -m recsys_gen.training.acquire --config configs/acquire_movielens25m.yaml
uv run python -m recsys_gen.training.prepare --config configs/dataset_movielens25m.yaml
uv run python -m recsys_gen.training.train_torchrec --config configs/torchrec_yambda.yaml
uv run python -m recsys_gen.training.eval_torchrec --config configs/torchrec_yambda.yaml
```

## Dataset assumptions

The repo does not vendor large public datasets. Acquisition configs materialize source files into `data/external/<dataset>/` and normalized parquet files into `data/raw/`.

Canonical interaction columns are:

- `user_id`
- `item_id`
- `timestamp`
- `target`
- `event_type`

Additional item metadata is materialized into parallel `*_items.parquet` files for later hybrid retrieval/ranking work.

## Supported acquisition targets

- `movielens25m`: automatic download from GroupLens and normalization into ratings plus movie metadata parquet files
- `amazon_electronics`, `amazon_beauty`, `amazon_sports`: manual placement of Amazon Reviews'23 review and metadata files, then normalization into parquet
- `yelp`: manual placement of the Yelp Open Dataset review and business files, then normalization into parquet

## Worktree workflow

Use a separate worktree for dataset-ingestion work so large-data plumbing does not interfere with the main checkout:

```bash
git worktree add -b feat-dataset-ingestion-core3 /tmp/ml-playground-datasets main
cd /tmp/ml-playground-datasets
```

## Next milestones

- Add hybrid item/context features on top of the current retrieval contract
- Add ANN index build and online retrieval serving
- Add a downstream ranking stage
