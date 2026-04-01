from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import polars as pl
import pyarrow.parquet as pq

SEQUENCE_SCHEMA = {
    "user_id": pl.Int64,
    "history": pl.List(pl.Int64),
    "target_item_id": pl.Int64,
    "target_timestamp": pl.Int64,
}
DEFAULT_SEQUENCE_BATCH_ROWS = 100_000


def build_user_sequences(
    frame: pl.DataFrame,
    *,
    max_length: int,
    min_length: int = 2,
) -> pl.DataFrame:
    batches = list(
        _iter_sequence_batches(
            frame,
            max_length=max_length,
            min_length=min_length,
            batch_rows=DEFAULT_SEQUENCE_BATCH_ROWS,
        )
    )
    if not batches:
        return _empty_sequences_frame()
    return pl.concat(batches, rechunk=False)


def write_user_sequences(
    frame: pl.DataFrame,
    *,
    max_length: int,
    min_length: int = 2,
    output_path: str | Path,
    batch_rows: int = DEFAULT_SEQUENCE_BATCH_ROWS,
) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    writer: pq.ParquetWriter | None = None
    try:
        for batch in _iter_sequence_batches(
            frame,
            max_length=max_length,
            min_length=min_length,
            batch_rows=batch_rows,
        ):
            table = batch.to_arrow()
            if writer is None:
                writer = pq.ParquetWriter(target, table.schema, compression="zstd")
            writer.write_table(table)
    finally:
        if writer is not None:
            writer.close()

    if writer is None:
        _empty_sequences_frame().write_parquet(target)


def build_seen_item_index(frame: pl.DataFrame) -> dict[int, set[int]]:
    seen: dict[int, set[int]] = defaultdict(set)
    for row in frame.iter_rows(named=True):
        seen[int(row["user_id"])].add(int(row["item_id"]))
    return seen


def sample_negative_items(
    frame: pl.DataFrame,
    *,
    num_negatives: int,
    seed: int = 7,
) -> dict[int, list[int]]:
    rng = np.random.default_rng(seed)
    seen = build_seen_item_index(frame)
    all_items = np.array(sorted(set(frame["item_id"].to_list())), dtype=np.int64)
    negatives: dict[int, list[int]] = {}

    for user_id, seen_items in seen.items():
        candidates = np.array([item for item in all_items if item not in seen_items], dtype=np.int64)
        if candidates.size == 0:
            negatives[user_id] = []
            continue
        take = min(num_negatives, candidates.size)
        sampled = rng.choice(candidates, size=take, replace=False)
        negatives[user_id] = sampled.tolist()
    return negatives


def histories_to_training_examples(
    sequences: pl.DataFrame,
    negatives: dict[int, Iterable[int]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in sequences.iter_rows(named=True):
        user_id = int(row["user_id"])
        rows.append(
            {
                "user_id": user_id,
                "history": row["history"],
                "target_item_id": int(row["target_item_id"]),
                "negative_item_ids": list(negatives.get(user_id, [])),
            }
        )
    return rows


def _iter_sequence_batches(
    frame: pl.DataFrame,
    *,
    max_length: int,
    min_length: int,
    batch_rows: int,
) -> Iterator[pl.DataFrame]:
    grouped = (
        frame.group_by("user_id", maintain_order=True)
        .agg(
            pl.col("item_id"),
            pl.col("timestamp"),
        )
        .sort("user_id")
    )

    batch: list[tuple[int, list[int], int, int]] = []
    for row in grouped.iter_rows(named=True):
        user_id = int(row["user_id"])
        item_ids = [int(item_id) for item_id in row["item_id"]]
        timestamps = [int(timestamp) for timestamp in row["timestamp"]]
        for index in range(min_length, len(item_ids)):
            history_start = max(0, index - max_length)
            batch.append(
                (
                    user_id,
                    item_ids[history_start:index],
                    item_ids[index],
                    timestamps[index],
                )
            )
            if len(batch) >= batch_rows:
                yield pl.DataFrame(batch, schema=SEQUENCE_SCHEMA, orient="row")
                batch = []

    if batch:
        yield pl.DataFrame(batch, schema=SEQUENCE_SCHEMA, orient="row")


def _empty_sequences_frame() -> pl.DataFrame:
    return pl.DataFrame(schema=SEQUENCE_SCHEMA)
