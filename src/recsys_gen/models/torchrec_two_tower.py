from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn

try:
    import torchrec  # type: ignore  # noqa: F401

    TORCHREC_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when torchrec is unavailable
    TORCHREC_AVAILABLE = False


class _EmbeddingBackbone(nn.Module):
    def __init__(self, *, count: int, embedding_dim: int) -> None:
        super().__init__()
        self.embedding = nn.Embedding(count, embedding_dim)

    def forward_ids(self, indices: torch.Tensor) -> torch.Tensor:
        return self.embedding(indices)

    def forward_bag(self, indices: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(indices)
        mask = (indices >= 0).unsqueeze(-1)
        summed = (embedded * mask).sum(dim=1)
        denom = mask.sum(dim=1).clamp(min=1)
        return summed / denom


class TwoTowerRetrievalModel(nn.Module):
    def __init__(
        self,
        *,
        num_users: int,
        num_items: int,
        embedding_dim: int,
        query_hidden_dim: int,
        item_hidden_dim: int,
    ) -> None:
        super().__init__()
        self.user_tower = _EmbeddingBackbone(count=num_users, embedding_dim=embedding_dim)
        self.history_tower = _EmbeddingBackbone(count=num_items, embedding_dim=embedding_dim)
        self.item_tower = _EmbeddingBackbone(count=num_items, embedding_dim=embedding_dim)

        self.query_projection = nn.Sequential(
            nn.Linear(embedding_dim * 2, query_hidden_dim),
            nn.ReLU(),
            nn.Linear(query_hidden_dim, embedding_dim),
        )
        self.item_projection = nn.Sequential(
            nn.Linear(embedding_dim, item_hidden_dim),
            nn.ReLU(),
            nn.Linear(item_hidden_dim, embedding_dim),
        )

    def encode_query(self, user_ids: torch.Tensor, history_item_ids: torch.Tensor) -> torch.Tensor:
        user_embedding = self.user_tower.forward_ids(user_ids)
        history_embedding = self.history_tower.forward_bag(history_item_ids)
        return nn.functional.normalize(
            self.query_projection(torch.cat([user_embedding, history_embedding], dim=1)),
            dim=1,
        )

    def encode_items(self, item_ids: torch.Tensor) -> torch.Tensor:
        item_embedding = self.item_tower.forward_ids(item_ids)
        return nn.functional.normalize(self.item_projection(item_embedding), dim=1)

    def forward(self, user_ids: torch.Tensor, history_item_ids: torch.Tensor, item_ids: torch.Tensor) -> torch.Tensor:
        query = self.encode_query(user_ids, history_item_ids)
        items = self.encode_items(item_ids)
        return query @ items.T


@dataclass
class TorchRecArtifactBundle:
    item_embeddings: torch.Tensor
    item_indices: list[int]
