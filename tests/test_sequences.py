import polars as pl

from recsys_gen.data.sequences import build_user_sequences, sample_negative_items


def test_build_user_sequences_creates_histories() -> None:
    frame = pl.DataFrame(
        {
            "user_id": [1, 1, 1, 1],
            "item_id": [10, 11, 12, 13],
            "timestamp": [1, 2, 3, 4],
            "target": [1, 1, 1, 1],
            "event_type": ["listen"] * 4,
        }
    )
    sequences = build_user_sequences(frame, max_length=3, min_length=2)
    assert sequences.height == 2
    assert sequences["history"].to_list()[0] == [10, 11]
    assert sequences["target_item_id"].to_list() == [12, 13]


def test_negative_sampling_excludes_seen_items() -> None:
    frame = pl.DataFrame(
        {
            "user_id": [1, 1, 2, 2],
            "item_id": [10, 11, 11, 12],
            "timestamp": [1, 2, 1, 2],
            "target": [1, 1, 1, 1],
            "event_type": ["listen"] * 4,
        }
    )
    negatives = sample_negative_items(frame, num_negatives=10, seed=1)
    assert 10 not in negatives[1]
    assert 11 not in negatives[1]
