from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

import polars as pl

VOCAB_SCHEMA = {
    "raw_id": pl.Int64,
    "index": pl.Int64,
}

RETRIEVAL_SCHEMA = {
    "user_idx": pl.Int64,
    "history_item_indices": pl.List(pl.Int64),
    "target_item_idx": pl.Int64,
    "target_timestamp": pl.Int64,
}

SEEN_SCHEMA = {
    "user_idx": pl.Int64,
    "seen_item_indices": pl.List(pl.Int64),
}


def build_vocab(frame: pl.DataFrame, column: str, *, start_index: int = 0) -> pl.DataFrame:
    values = sorted(int(value) for value in frame[column].unique().to_list())
    rows = [{"raw_id": value, "index": idx} for idx, value in enumerate(values, start=start_index)]
    return pl.DataFrame(rows, schema=VOCAB_SCHEMA) if rows else pl.DataFrame(schema=VOCAB_SCHEMA)


def build_index_lookup(vocab: pl.DataFrame) -> dict[int, int]:
    return {int(row["raw_id"]): int(row["index"]) for row in vocab.iter_rows(named=True)}


def encode_split(
    frame: pl.DataFrame,
    *,
    user_lookup: dict[int, int],
    item_lookup: dict[int, int],
) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("user_id").replace_strict(user_lookup).cast(pl.Int64).alias("user_idx"),
        pl.col("item_id").replace_strict(item_lookup).cast(pl.Int64).alias("item_idx"),
    )


def build_retrieval_examples(
    history_frame: pl.DataFrame,
    target_frame: pl.DataFrame,
    *,
    max_history_length: int,
) -> pl.DataFrame:
    history_by_user: dict[int, list[int]] = defaultdict(list)
    for row in history_frame.sort(["user_idx", "timestamp", "item_idx"]).iter_rows(named=True):
        history_by_user[int(row["user_idx"])].append(int(row["item_idx"]))

    rows: list[dict[str, object]] = []
    for row in target_frame.sort(["user_idx", "timestamp", "item_idx"]).iter_rows(named=True):
        user_idx = int(row["user_idx"])
        target_item_idx = int(row["item_idx"])
        history = history_by_user.get(user_idx, [])
        if history:
            rows.append(
                {
                    "user_idx": user_idx,
                    "history_item_indices": history[-max_history_length:],
                    "target_item_idx": target_item_idx,
                    "target_timestamp": int(row["timestamp"]),
                }
            )
        history_by_user[user_idx].append(target_item_idx)

    return pl.DataFrame(rows, schema=RETRIEVAL_SCHEMA) if rows else pl.DataFrame(schema=RETRIEVAL_SCHEMA)


def build_seen_items(frame: pl.DataFrame) -> pl.DataFrame:
    grouped = (
        frame.group_by("user_idx", maintain_order=True)
        .agg(pl.col("item_idx").sort().alias("seen_item_indices"))
        .sort("user_idx")
    )
    rows = [
        {
            "user_idx": int(row["user_idx"]),
            "seen_item_indices": [int(value) for value in row["seen_item_indices"]],
        }
        for row in grouped.iter_rows(named=True)
    ]
    return pl.DataFrame(rows, schema=SEEN_SCHEMA) if rows else pl.DataFrame(schema=SEEN_SCHEMA)


def write_parquet(frame: pl.DataFrame, output_path: str | Path) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(target)


def build_catalog_item_indices(train_frame: pl.DataFrame) -> list[int]:
    return sorted(int(value) for value in train_frame["index"].to_list())


def build_seen_item_lookup(seen_frame: pl.DataFrame) -> dict[int, set[int]]:
    return {
        int(row["user_idx"]): {int(value) for value in row["seen_item_indices"]}
        for row in seen_frame.iter_rows(named=True)
    }


def build_history_lookup(examples: pl.DataFrame) -> dict[int, list[int]]:
    history_lookup: dict[int, list[int]] = {}
    for row in examples.iter_rows(named=True):
        history_lookup[int(row["user_idx"])] = [int(value) for value in row["history_item_indices"]]
    return history_lookup


def invert_vocab(vocab: pl.DataFrame) -> dict[int, int]:
    return {int(row["index"]): int(row["raw_id"]) for row in vocab.iter_rows(named=True)}


def remap_indices(values: Iterable[int], lookup: dict[int, int]) -> list[int]:
    return [lookup[int(value)] for value in values if int(value) in lookup]
