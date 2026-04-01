from __future__ import annotations

from pathlib import Path

import polars as pl

from recsys_gen.data.schemas import CANONICAL_COLUMNS


def load_dataset(path: str | Path) -> pl.DataFrame:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Dataset not found: {source}")
    if source.suffix == ".parquet":
        return pl.read_parquet(source)
    raise ValueError(f"Unsupported dataset format for {source}")


def normalize_interactions(frame: pl.DataFrame, column_map: dict[str, str]) -> pl.DataFrame:
    missing = [source for source in column_map.values() if source not in frame.columns]
    if missing:
        raise ValueError(f"Missing source columns: {missing}")

    renamed = frame.rename({source: target for target, source in column_map.items()})
    for column in CANONICAL_COLUMNS:
        if column not in renamed.columns:
            if column == "target":
                renamed = renamed.with_columns(pl.lit(1).alias("target"))
            elif column == "event_type":
                renamed = renamed.with_columns(pl.lit("interaction").alias("event_type"))
            else:
                raise ValueError(f"Canonical column missing after normalization: {column}")

    normalized = renamed.select(CANONICAL_COLUMNS + [c for c in renamed.columns if c not in CANONICAL_COLUMNS])
    return normalized.with_columns(
        pl.col("user_id").cast(pl.Int64),
        pl.col("item_id").cast(pl.Int64),
        pl.col("target").cast(pl.Int8),
        pl.col("event_type").cast(pl.Utf8),
        pl.col("timestamp").cast(pl.Int64),
    ).sort(["user_id", "timestamp", "item_id"])


def filter_interactions(
    frame: pl.DataFrame,
    *,
    min_user_interactions: int = 1,
    min_item_interactions: int = 1,
) -> pl.DataFrame:
    user_counts = frame.group_by("user_id").len().rename({"len": "user_count"})
    item_counts = frame.group_by("item_id").len().rename({"len": "item_count"})
    filtered = (
        frame.join(user_counts, on="user_id", how="left")
        .join(item_counts, on="item_id", how="left")
        .filter(pl.col("user_count") >= min_user_interactions)
        .filter(pl.col("item_count") >= min_item_interactions)
        .drop(["user_count", "item_count"])
    )
    return filtered.sort(["user_id", "timestamp", "item_id"])


def train_test_split_temporal(
    frame: pl.DataFrame,
    *,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    total = train_ratio + validation_ratio + test_ratio
    if abs(total - 1.0) > 1e-9:
        raise ValueError("Split ratios must sum to 1.0")

    splits: list[tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]] = []
    for user_frame in frame.partition_by("user_id", maintain_order=True):
        n_rows = user_frame.height
        train_end = max(1, int(n_rows * train_ratio))
        validation_end = max(train_end + 1, int(n_rows * (train_ratio + validation_ratio)))
        train = user_frame.slice(0, train_end)
        validation = user_frame.slice(train_end, max(0, validation_end - train_end))
        test = user_frame.slice(validation_end, max(0, n_rows - validation_end))

        if validation.height == 0 and test.height > 1:
            validation = test.slice(0, 1)
            test = test.slice(1)
        elif validation.height == 0 and train.height > 1:
            validation = train.slice(train.height - 1, 1)
            train = train.slice(0, train.height - 1)

        if test.height == 0 and validation.height > 1:
            test = validation.slice(validation.height - 1, 1)
            validation = validation.slice(0, validation.height - 1)
        elif test.height == 0 and train.height > 1:
            test = train.slice(train.height - 1, 1)
            train = train.slice(0, train.height - 1)

        splits.append((train, validation, test))

    trains = [part[0] for part in splits if part[0].height]
    validations = [part[1] for part in splits if part[1].height]
    tests = [part[2] for part in splits if part[2].height]
    return pl.concat(trains), pl.concat(validations), pl.concat(tests)
