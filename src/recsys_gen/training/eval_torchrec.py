from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import torch
import typer

from recsys_gen.data.retrieval import build_seen_item_lookup, invert_vocab
from recsys_gen.evaluation.metrics import (
    coverage_at_k,
    diversity_at_k,
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    recall_at_k,
)
from recsys_gen.models.torchrec_two_tower import TwoTowerRetrievalModel
from recsys_gen.tracking.mlflow import log_run_summary
from recsys_gen.utils.io import ensure_dir, load_yaml

app = typer.Typer(add_completion=False)


def _load_model(config: dict[str, object]) -> tuple[TwoTowerRetrievalModel, dict[str, object]]:
    dataset_cfg = config["dataset"]
    model_cfg = config["model"]
    tracking_cfg = config["tracking"]
    assert isinstance(dataset_cfg, dict)
    assert isinstance(model_cfg, dict)
    assert isinstance(tracking_cfg, dict)

    prepared_dir = Path(str(dataset_cfg["prepared_dir"]))
    item_vocab = pl.read_parquet(prepared_dir / "item_vocab.parquet")
    user_vocab = pl.read_parquet(prepared_dir / "user_vocab.parquet")
    artifact_dir = Path(str(tracking_cfg["artifact_dir"]))
    model = TwoTowerRetrievalModel(
        num_users=user_vocab.height,
        num_items=int(item_vocab["index"].max()) + 1 if item_vocab.height else 1,
        embedding_dim=int(model_cfg["embedding_dim"]),
        query_hidden_dim=int(model_cfg["query_hidden_dim"]),
        item_hidden_dim=int(model_cfg["item_hidden_dim"]),
    )
    model.load_state_dict(torch.load(artifact_dir / "model.pt", map_location="cpu"))
    model.eval()
    item_bundle = torch.load(artifact_dir / "item_embeddings.pt", map_location="cpu")
    return model, item_bundle


def evaluate_model(config: dict[str, object]) -> dict[str, float]:
    dataset_cfg = config["dataset"]
    tracking_cfg = config["tracking"]
    evaluation_cfg = config["evaluation"]
    assert isinstance(dataset_cfg, dict)
    assert isinstance(tracking_cfg, dict)
    assert isinstance(evaluation_cfg, dict)

    prepared_dir = Path(str(dataset_cfg["prepared_dir"]))
    artifact_dir = ensure_dir(str(tracking_cfg["artifact_dir"]))

    model, item_bundle = _load_model(config)
    validation = pl.read_parquet(prepared_dir / "retrieval_validation.parquet")
    seen_train = pl.read_parquet(prepared_dir / "seen_train.parquet")
    item_vocab = pl.read_parquet(prepared_dir / "item_vocab.parquet")
    raw_item_lookup = invert_vocab(item_vocab)
    seen_lookup = build_seen_item_lookup(seen_train)
    item_indices = torch.tensor(item_bundle["item_indices"], dtype=torch.long)
    item_embeddings = item_bundle["embeddings"]
    cutoffs = [int(value) for value in evaluation_cfg["cutoffs"]]
    top_k = max(cutoffs)

    actual_by_user: dict[int, list[int]] = {}
    predicted_lists: list[list[int]] = []
    recall_scores: list[float] = []
    ndcg_scores: list[float] = []
    mrr_scores: list[float] = []
    hit_scores: list[float] = []

    for row in validation.iter_rows(named=True):
        user_idx = int(row["user_idx"])
        actual_by_user.setdefault(user_idx, []).append(int(row["target_item_idx"]))

    for user_idx, actual in actual_by_user.items():
        history = validation.filter(pl.col("user_idx") == user_idx).sort("target_timestamp").tail(1)["history_item_indices"][0]
        history_tensor = torch.tensor([[int(value) for value in history]], dtype=torch.long)
        user_tensor = torch.tensor([user_idx], dtype=torch.long)
        with torch.no_grad():
            query = model.encode_query(user_tensor, history_tensor)
            scores = torch.matmul(query, item_embeddings.T)[0]
        for seen_item in seen_lookup.get(user_idx, set()):
            matches = (item_indices == seen_item).nonzero(as_tuple=False)
            if matches.numel() > 0:
                scores[matches[0][0]] = float("-inf")
        top_indices = torch.topk(scores, k=min(top_k, scores.size(0))).indices.tolist()
        predicted = [raw_item_lookup[int(item_bundle["item_indices"][index])] for index in top_indices]
        actual_raw = [raw_item_lookup[item] for item in actual]
        predicted_lists.append(predicted)
        recall_scores.append(recall_at_k(actual_raw, predicted, top_k))
        ndcg_scores.append(ndcg_at_k(actual_raw, predicted, top_k))
        mrr_scores.append(mean_reciprocal_rank(actual_raw, predicted))
        hit_scores.append(hit_rate_at_k(actual_raw, predicted, top_k))

    metrics = {
        f"recall@{top_k}": sum(recall_scores) / max(1, len(recall_scores)),
        f"ndcg@{top_k}": sum(ndcg_scores) / max(1, len(ndcg_scores)),
        "mrr": sum(mrr_scores) / max(1, len(mrr_scores)),
        f"hitrate@{top_k}": sum(hit_scores) / max(1, len(hit_scores)),
        f"coverage@{top_k}": coverage_at_k(predicted_lists, item_vocab.height, top_k),
        f"diversity@{top_k}": diversity_at_k(predicted_lists, top_k),
    }
    run_id = log_run_summary(
        run_name=str(tracking_cfg["run_name"]),
        experiment_name=str(tracking_cfg["experiment_name"]),
        params={"config": "torchrec", "model_name": "torchrec_two_tower"},
        metrics=metrics,
        artifact_dir=artifact_dir,
    )
    (Path(artifact_dir) / "metrics.json").write_text(
        json.dumps({"run_id": run_id, "metrics": metrics}, indent=2),
        encoding="utf-8",
    )
    return metrics


@app.command()
def main(config: str = typer.Option(..., "--config")) -> None:
    evaluate_model(load_yaml(config))


if __name__ == "__main__":
    app()
