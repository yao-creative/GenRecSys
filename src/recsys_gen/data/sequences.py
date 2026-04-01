from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import numpy as np
import polars as pl


def build_user_sequences(
    frame: pl.DataFrame,
    *,
    max_length: int,
    min_length: int = 2,
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for user_frame in frame.partition_by("user_id", maintain_order=True):
        user_id = int(user_frame["user_id"][0])
        item_ids = user_frame["item_id"].to_list()
        timestamps = user_frame["timestamp"].to_list()
        for index in range(1, len(item_ids)):
            history = item_ids[max(0, index - max_length):index]
            if len(history) < min_length:
                continue
            rows.append(
                {
                    "user_id": user_id,
                    "history": history,
                    "target_item_id": int(item_ids[index]),
                    "target_timestamp": int(timestamps[index]),
                }
            )
    return pl.DataFrame(rows, schema={"user_id": pl.Int64, "history": pl.List(pl.Int64), "target_item_id": pl.Int64, "target_timestamp": pl.Int64})


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
