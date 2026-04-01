from pathlib import Path

import polars as pl

from recsys_gen.data.dataset import normalize_interactions, train_test_split_temporal


def test_normalize_interactions_maps_columns() -> None:
    frame = pl.DataFrame(
        {
            "uid": [1, 1, 2],
            "iid": [10, 11, 10],
            "ts": [1, 2, 3],
            "label": [1, 1, 1],
            "kind": ["listen", "like", "listen"],
        }
    )
    normalized = normalize_interactions(
        frame,
        {"user_id": "uid", "item_id": "iid", "timestamp": "ts", "target": "label", "event_type": "kind"},
    )
    assert normalized.columns[:5] == ["user_id", "item_id", "timestamp", "target", "event_type"]
    assert normalized["user_id"].to_list() == [1, 1, 2]


def test_train_test_split_temporal_preserves_user_order() -> None:
    frame = pl.DataFrame(
        {
            "user_id": [1, 1, 1, 2, 2, 2],
            "item_id": [10, 11, 12, 20, 21, 22],
            "timestamp": [1, 2, 3, 1, 2, 3],
            "target": [1] * 6,
            "event_type": ["listen"] * 6,
        }
    )
    train, validation, test = train_test_split_temporal(
        frame,
        train_ratio=0.6,
        validation_ratio=0.2,
        test_ratio=0.2,
    )
    assert train.filter(pl.col("user_id") == 1)["item_id"].to_list() == [10]
    assert validation.filter(pl.col("user_id") == 1)["item_id"].to_list() == [11]
    assert test.filter(pl.col("user_id") == 1)["item_id"].to_list() == [12]


def test_train_test_split_temporal_keeps_validation_and_test_when_possible() -> None:
    frame = pl.DataFrame(
        {
            "user_id": [1, 1, 2, 2],
            "item_id": [10, 11, 20, 21],
            "timestamp": [1, 2, 1, 2],
            "target": [1] * 4,
            "event_type": ["listen"] * 4,
        }
    )
    train, validation, test = train_test_split_temporal(
        frame,
        train_ratio=0.8,
        validation_ratio=0.1,
        test_ratio=0.1,
    )
    assert train.height == 2
    assert validation.height == 2
    assert test.height == 0
    assert validation["item_id"].to_list() == [11, 21]
