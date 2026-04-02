from pathlib import Path

import polars as pl

from recsys_gen.data.retrieval import (
    build_retrieval_examples,
    build_seen_items,
    build_vocab,
    build_index_lookup,
    encode_split,
    invert_vocab,
    remap_indices,
    write_parquet,
)


def test_build_retrieval_examples_uses_prefix_histories() -> None:
    history_frame = pl.DataFrame(
        {
            "user_idx": [0, 0],
            "item_idx": [3, 4],
            "timestamp": [1, 2],
        }
    )
    target_frame = pl.DataFrame(
        {
            "user_idx": [0, 0],
            "item_idx": [5, 6],
            "timestamp": [3, 4],
        }
    )
    examples = build_retrieval_examples(history_frame, target_frame, max_history_length=3)
    assert examples["history_item_indices"].to_list() == [[3, 4], [3, 4, 5]]
    assert examples["target_item_idx"].to_list() == [5, 6]


def test_build_seen_items_groups_items_by_user() -> None:
    frame = pl.DataFrame(
        {
            "user_idx": [0, 0, 1],
            "item_idx": [3, 4, 6],
            "timestamp": [1, 2, 1],
        }
    )
    seen = build_seen_items(frame)
    assert seen["seen_item_indices"].to_list() == [[3, 4], [6]]


def test_vocab_and_remap_round_trip() -> None:
    frame = pl.DataFrame({"item_id": [10, 20, 10]})
    vocab = build_vocab(frame, "item_id")
    lookup = build_index_lookup(vocab)
    inverse = invert_vocab(vocab)
    encoded = [lookup[10], lookup[20]]
    assert remap_indices(encoded, inverse) == [10, 20]


def test_encode_split_adds_dense_indices() -> None:
    frame = pl.DataFrame(
        {
            "user_id": [1],
            "item_id": [10],
            "timestamp": [1],
            "target": [1],
            "event_type": ["click"],
        }
    )
    encoded = encode_split(frame, user_lookup={1: 0}, item_lookup={10: 3})
    assert encoded["user_idx"].to_list() == [0]
    assert encoded["item_idx"].to_list() == [3]


def test_write_parquet_writes_output(tmp_path: Path) -> None:
    frame = pl.DataFrame({"raw_id": [1], "index": [0]})
    output_path = tmp_path / "vocab.parquet"
    write_parquet(frame, output_path)
    round_trip = pl.read_parquet(output_path)
    assert round_trip.to_dict(as_series=False) == {"raw_id": [1], "index": [0]}
