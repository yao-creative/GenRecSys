import polars as pl

from recsys_gen.models.baselines import ItemKNNRecommender
from recsys_gen.models.sasrec import SASRec, SASRecTrainer


def test_itemknn_recommendations_exclude_seen_items() -> None:
    frame = pl.DataFrame(
        {
            "user_id": [1, 1, 2, 2, 3, 3],
            "item_id": [10, 11, 10, 12, 11, 12],
            "timestamp": [1, 2, 1, 2, 1, 2],
            "target": [1] * 6,
            "event_type": ["listen"] * 6,
        }
    )
    model = ItemKNNRecommender().fit(frame)
    recs = model.recommend(1, k=2)
    assert 10 not in recs
    assert 11 not in recs


def test_sasrec_forward_and_recommend() -> None:
    trainer = SASRecTrainer(
        model=SASRec(
            num_items=20,
            max_sequence_length=4,
            hidden_dim=8,
            num_heads=2,
            num_blocks=1,
            dropout=0.1,
        ),
        learning_rate=0.001,
        batch_size=2,
        epochs=1,
    )
    examples = [
        {"history": [1, 2], "target_item_id": 3},
        {"history": [2, 3], "target_item_id": 4},
    ]
    trainer.fit(examples, max_sequence_length=4)
    recs = trainer.recommend([1, 2, 3], k=3)
    assert len(recs) == 3
