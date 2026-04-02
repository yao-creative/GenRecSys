from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import polars as pl
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
import typer

from recsys_gen.data.retrieval import build_catalog_item_indices
from recsys_gen.models.torchrec_two_tower import TORCHREC_AVAILABLE, TwoTowerRetrievalModel
from recsys_gen.utils.io import ensure_dir, load_yaml

app = typer.Typer(add_completion=False)


class RetrievalDataset(Dataset):
    def __init__(self, frame: pl.DataFrame, max_history_length: int) -> None:
        self.rows = list(frame.iter_rows(named=True))
        self.max_history_length = max_history_length

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[int, list[int], int]:
        row = self.rows[index]
        return (
            int(row["user_idx"]),
            [int(value) for value in row["history_item_indices"]][-self.max_history_length :],
            int(row["target_item_idx"]),
        )


def _collate_batch(batch: list[tuple[int, list[int], int]]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    user_ids = torch.tensor([row[0] for row in batch], dtype=torch.long)
    max_len = max((len(row[1]) for row in batch), default=1)
    histories = []
    for _, history, _ in batch:
        pad = [0] * max(0, max_len - len(history))
        histories.append((pad + history) if history else ([0] * max_len))
    history_tensor = torch.tensor(histories, dtype=torch.long)
    target_ids = torch.tensor([row[2] for row in batch], dtype=torch.long)
    return user_ids, history_tensor, target_ids


@dataclass
class TrainArtifacts:
    checkpoint_path: Path
    item_embeddings_path: Path
    metadata_path: Path


def train_model(config: dict[str, object]) -> TrainArtifacts:
    dataset_cfg = config["dataset"]
    model_cfg = config["model"]
    training_cfg = config["training"]
    tracking_cfg = config["tracking"]

    assert isinstance(dataset_cfg, dict)
    assert isinstance(model_cfg, dict)
    assert isinstance(training_cfg, dict)
    assert isinstance(tracking_cfg, dict)

    prepared_dir = Path(str(dataset_cfg["prepared_dir"]))
    train_frame = pl.read_parquet(prepared_dir / "retrieval_train.parquet")
    item_vocab = pl.read_parquet(prepared_dir / "item_vocab.parquet")
    user_vocab = pl.read_parquet(prepared_dir / "user_vocab.parquet")

    model = TwoTowerRetrievalModel(
        num_users=user_vocab.height,
        num_items=int(item_vocab["index"].max()) + 1 if item_vocab.height else 1,
        embedding_dim=int(model_cfg["embedding_dim"]),
        query_hidden_dim=int(model_cfg["query_hidden_dim"]),
        item_hidden_dim=int(model_cfg["item_hidden_dim"]),
    )
    artifact_dir = ensure_dir(str(tracking_cfg["artifact_dir"]))

    if train_frame.height > 0:
        loader = DataLoader(
            RetrievalDataset(train_frame, max_history_length=int(model_cfg["max_history_length"])),
            batch_size=int(training_cfg["batch_size"]),
            shuffle=True,
            collate_fn=_collate_batch,
        )
        optimizer = torch.optim.Adam(model.parameters(), lr=float(training_cfg["learning_rate"]))
        loss_fn = nn.CrossEntropyLoss()
        model.train()
        for _ in range(int(training_cfg["epochs"])):
            for user_ids, histories, target_ids in loader:
                optimizer.zero_grad()
                scores = model(user_ids, histories, target_ids)
                labels = torch.arange(scores.size(0), dtype=torch.long, device=scores.device)
                loss = loss_fn(scores, labels)
                loss.backward()
                optimizer.step()

    item_indices = build_catalog_item_indices(item_vocab)
    item_tensor = torch.tensor(item_indices, dtype=torch.long)
    with torch.no_grad():
        item_embeddings = model.encode_items(item_tensor).cpu()

    checkpoint_path = artifact_dir / "model.pt"
    item_embeddings_path = artifact_dir / "item_embeddings.pt"
    metadata_path = artifact_dir / "model_metadata.json"
    torch.save(model.state_dict(), checkpoint_path)
    torch.save({"item_indices": item_indices, "embeddings": item_embeddings}, item_embeddings_path)
    metadata_path.write_text(
        json.dumps(
            {
                "torchrec_available": TORCHREC_AVAILABLE,
                "num_users": user_vocab.height,
                "num_items": item_vocab.height,
                "embedding_dim": int(model_cfg["embedding_dim"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return TrainArtifacts(
        checkpoint_path=checkpoint_path,
        item_embeddings_path=item_embeddings_path,
        metadata_path=metadata_path,
    )


@app.command()
def main(config: str = typer.Option(..., "--config")) -> None:
    train_model(load_yaml(config))


if __name__ == "__main__":
    app()
