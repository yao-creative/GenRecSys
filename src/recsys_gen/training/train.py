from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl
import typer

from recsys_gen.data.sequences import histories_to_training_examples, sample_negative_items
from recsys_gen.evaluation.metrics import (
    coverage_at_k,
    diversity_at_k,
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    recall_at_k,
)
from recsys_gen.models.baselines import ItemKNNRecommender, MatrixFactorizationRecommenderWrapper
from recsys_gen.models.sasrec import SASRec, SASRecTrainer
from recsys_gen.tracking.mlflow import log_run_summary
from recsys_gen.utils.io import ensure_dir, load_yaml

app = typer.Typer(add_completion=False)


def _load_prepared(prepared_dir: str | Path) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame | None]:
    prepared = Path(prepared_dir)
    train = pl.read_parquet(prepared / "train.parquet")
    validation = pl.read_parquet(prepared / "validation.parquet")
    test = pl.read_parquet(prepared / "test.parquet")
    sequences_path = prepared / "sequences.parquet"
    sequences = pl.read_parquet(sequences_path) if sequences_path.exists() else None
    return train, validation, test, sequences


def _evaluate_model(model: Any, validation: pl.DataFrame, *, cutoffs: list[int], histories: dict[int, list[int]] | None = None) -> dict[str, float]:
    actual_by_user: dict[int, list[int]] = {}
    for row in validation.iter_rows(named=True):
        actual_by_user.setdefault(int(row["user_id"]), []).append(int(row["item_id"]))

    recommendations: list[list[int]] = []
    recall_scores: list[float] = []
    ndcg_scores: list[float] = []
    mrr_scores: list[float] = []
    hit_scores: list[float] = []

    top_k = max(cutoffs)
    for user_id, actual in actual_by_user.items():
        if histories is not None:
            predicted = model.recommend(histories.get(user_id, []), k=top_k)
        else:
            predicted = model.recommend(user_id, k=top_k)
        recommendations.append(predicted)
        recall_scores.append(recall_at_k(actual, predicted, top_k))
        ndcg_scores.append(ndcg_at_k(actual, predicted, top_k))
        mrr_scores.append(mean_reciprocal_rank(actual, predicted))
        hit_scores.append(hit_rate_at_k(actual, predicted, top_k))

    catalog_size = len(set(validation["item_id"].to_list()))
    return {
        f"recall@{top_k}": sum(recall_scores) / max(1, len(recall_scores)),
        f"ndcg@{top_k}": sum(ndcg_scores) / max(1, len(ndcg_scores)),
        "mrr": sum(mrr_scores) / max(1, len(mrr_scores)),
        f"hitrate@{top_k}": sum(hit_scores) / max(1, len(hit_scores)),
        f"coverage@{top_k}": coverage_at_k(recommendations, catalog_size, top_k),
        f"diversity@{top_k}": diversity_at_k(recommendations, top_k),
    }


@app.command()
def main(config: str = typer.Option(..., "--config")) -> None:
    payload = load_yaml(config)
    train, validation, _, sequences = _load_prepared(payload["dataset"]["prepared_dir"])
    artifact_dir = ensure_dir(payload["tracking"]["artifact_dir"])
    model_cfg = payload["model"]
    model_name = model_cfg["name"]
    cutoffs = payload["evaluation"]["cutoffs"]

    if model_name == "itemknn":
        model = ItemKNNRecommender(top_k=model_cfg.get("top_k", 100)).fit(train)
        metrics = _evaluate_model(model, validation, cutoffs=cutoffs)
    elif model_name == "mf":
        model = MatrixFactorizationRecommenderWrapper(
            embedding_dim=model_cfg.get("embedding_dim", 64),
            learning_rate=model_cfg.get("learning_rate", 0.01),
            epochs=model_cfg.get("epochs", 3),
        ).fit(train)
        metrics = _evaluate_model(model, validation, cutoffs=cutoffs)
    elif model_name == "sasrec":
        if sequences is None:
            raise ValueError("SASRec config requires prepared sequences.parquet")
        negatives = sample_negative_items(train, num_negatives=50)
        examples = histories_to_training_examples(sequences, negatives)
        num_items = max(train["item_id"].max(), validation["item_id"].max())
        trainer = SASRecTrainer(
            model=SASRec(
                num_items=int(num_items),
                max_sequence_length=model_cfg["max_sequence_length"],
                hidden_dim=model_cfg["hidden_dim"],
                num_heads=model_cfg["num_heads"],
                num_blocks=model_cfg["num_blocks"],
                dropout=model_cfg["dropout"],
            ),
            learning_rate=model_cfg["learning_rate"],
            batch_size=model_cfg["batch_size"],
            epochs=model_cfg["epochs"],
        )
        model = trainer.fit(examples, model_cfg["max_sequence_length"])
        histories = {int(row["user_id"]): list(row["history"]) for row in sequences.iter_rows(named=True)}
        metrics = _evaluate_model(trainer, validation, cutoffs=cutoffs, histories=histories)
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    run_id = log_run_summary(
        run_name=payload["tracking"]["run_name"],
        experiment_name=payload["tracking"]["experiment_name"],
        params={"config": config, "model_name": model_name},
        metrics=metrics,
        artifact_dir=artifact_dir,
    )
    output = {"run_id": run_id, "metrics": metrics}
    (Path(artifact_dir) / "metrics.json").write_text(json.dumps(output, indent=2), encoding="utf-8")


if __name__ == "__main__":
    app()
