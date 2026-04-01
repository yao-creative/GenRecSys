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

    user_counts = (
        frame.group_by("user_id")
        .len()
        .rename({"len": "user_count"})
        .with_columns(pl.col("user_count").cast(pl.Int64))
    )
    count_boundaries = _build_split_boundaries(
        user_counts["user_count"].unique().to_list(),
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
    )
    indexed = (
        frame.join(user_counts, on="user_id", how="left")
        .with_columns(
            (pl.col("user_id").cum_count().over("user_id") - 1).cast(pl.Int64).alias("__user_row"),
        )
        .join(count_boundaries, on="user_count", how="left")
    )

    train_cutoff = pl.col("train_count")
    validation_cutoff = pl.col("train_count") + pl.col("validation_count")

    train = (
        indexed.filter(pl.col("__user_row") < train_cutoff)
        .drop(["user_count", "__user_row", "train_count", "validation_count", "test_count"])
        .sort(["user_id", "timestamp", "item_id"])
    )
    validation = (
        indexed.filter((pl.col("__user_row") >= train_cutoff) & (pl.col("__user_row") < validation_cutoff))
        .drop(["user_count", "__user_row", "train_count", "validation_count", "test_count"])
        .sort(["user_id", "timestamp", "item_id"])
    )
    test = (
        indexed.filter(pl.col("__user_row") >= validation_cutoff)
        .drop(["user_count", "__user_row", "train_count", "validation_count", "test_count"])
        .sort(["user_id", "timestamp", "item_id"])
    )
    return train, validation, test


def _build_split_boundaries(
    user_counts: list[int],
    *,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> pl.DataFrame:
    rows = [
        {
            "user_count": int(user_count),
            "train_count": train_count,
            "validation_count": validation_count,
            "test_count": test_count,
        }
        for user_count in sorted(set(int(count) for count in user_counts))
        for train_count, validation_count, test_count in [
            _compute_split_counts(
                int(user_count),
                train_ratio=train_ratio,
                validation_ratio=validation_ratio,
                test_ratio=test_ratio,
            )
        ]
    ]
    return pl.DataFrame(rows)


def _compute_split_counts(
    user_count: int,
    *,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> tuple[int, int, int]:
    train_count = max(1, int(user_count * train_ratio))
    validation_end = max(train_count + 1, int(user_count * (train_ratio + validation_ratio)))
    validation_count = max(0, validation_end - train_count)
    test_count = max(0, user_count - validation_end)

    if validation_count == 0 and test_count > 1:
        validation_count = 1
        test_count -= 1
    elif validation_count == 0 and train_count > 1:
        validation_count = 1
        train_count -= 1

    if test_count == 0 and validation_count > 1:
        test_count = 1
        validation_count -= 1
    elif test_count == 0 and train_count > 1:
        test_count = 1
        train_count -= 1

    return train_count, validation_count, test_count
