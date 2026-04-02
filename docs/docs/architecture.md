# Architecture Compute Graph

The repo now has a single recommender path: split-safe retrieval prep feeding a TorchRec-oriented two-tower trainer and offline evaluator.

## Pipeline

1. `training.acquire` downloads or validates source datasets and normalizes them into raw parquet tables.
2. `training.prepare` converts raw interactions into canonical train/validation/test splits, contiguous ID vocabularies, encoded splits, retrieval examples, and seen-item masks.
3. `training.train_torchrec` trains a two-tower retriever and writes checkpoints plus item embedding artifacts.
4. `training.eval_torchrec` scores the full catalog offline, logs ranking metrics to MLflow, and writes `metrics.json`.
5. `serving.api` remains isolated and only exposes a health endpoint.

## Data contract

`prepare` now writes:

- `train.parquet`, `validation.parquet`, `test.parquet`
- `user_vocab.parquet`, `item_vocab.parquet`
- `train_encoded.parquet`, `validation_encoded.parquet`, `test_encoded.parquet`
- `retrieval_train.parquet`, `retrieval_validation.parquet`, `retrieval_test.parquet`
- `seen_train.parquet`

The important invariant is that evaluation examples are built from prefix histories only:

- retrieval train uses train history only
- retrieval validation uses train history only
- retrieval test uses train plus validation history only

That keeps temporal comparability while removing future-history leakage from model training and offline evaluation.
