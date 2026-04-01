from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
import torch
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class InteractionMatrix:
    matrix: np.ndarray
    user_index: dict[int, int]
    item_index: dict[int, int]
    inverse_item_index: dict[int, int]


def build_interaction_matrix(frame: pl.DataFrame) -> InteractionMatrix:
    users = sorted(set(frame["user_id"].to_list()))
    items = sorted(set(frame["item_id"].to_list()))
    user_index = {user_id: index for index, user_id in enumerate(users)}
    item_index = {item_id: index for index, item_id in enumerate(items)}
    matrix = np.zeros((len(users), len(items)), dtype=np.float32)
    for row in frame.iter_rows(named=True):
        matrix[user_index[int(row["user_id"])], item_index[int(row["item_id"])]] = float(row["target"])
    inverse_item_index = {index: item_id for item_id, index in item_index.items()}
    return InteractionMatrix(matrix=matrix, user_index=user_index, item_index=item_index, inverse_item_index=inverse_item_index)


class ItemKNNRecommender:
    def __init__(self, top_k: int = 100) -> None:
        self.top_k = top_k
        self.interactions: InteractionMatrix | None = None
        self.item_similarity: np.ndarray | None = None

    def fit(self, frame: pl.DataFrame) -> "ItemKNNRecommender":
        self.interactions = build_interaction_matrix(frame)
        self.item_similarity = cosine_similarity(self.interactions.matrix.T)
        np.fill_diagonal(self.item_similarity, 0.0)
        return self

    def recommend(self, user_id: int, *, k: int = 10) -> list[int]:
        if self.interactions is None or self.item_similarity is None:
            raise RuntimeError("Model must be fit before recommendation")
        if user_id not in self.interactions.user_index:
            return []
        user_row = self.interactions.matrix[self.interactions.user_index[user_id]]
        scores = user_row @ self.item_similarity
        seen_mask = user_row > 0
        scores[seen_mask] = -np.inf
        top_indices = np.argsort(scores)[::-1][:k]
        return [self.interactions.inverse_item_index[int(index)] for index in top_indices if np.isfinite(scores[index])]


class MatrixFactorizationRecommender(torch.nn.Module):
    def __init__(self, num_users: int, num_items: int, embedding_dim: int = 64) -> None:
        super().__init__()
        self.user_embedding = torch.nn.Embedding(num_users, embedding_dim)
        self.item_embedding = torch.nn.Embedding(num_items, embedding_dim)

    def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor) -> torch.Tensor:
        user_vectors = self.user_embedding(user_ids)
        item_vectors = self.item_embedding(item_ids)
        return (user_vectors * item_vectors).sum(dim=1)


class MatrixFactorizationRecommenderWrapper:
    def __init__(self, embedding_dim: int = 64, learning_rate: float = 0.01, epochs: int = 3) -> None:
        self.embedding_dim = embedding_dim
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.interactions: InteractionMatrix | None = None
        self.model: MatrixFactorizationRecommender | None = None

    def fit(self, frame: pl.DataFrame) -> "MatrixFactorizationRecommenderWrapper":
        self.interactions = build_interaction_matrix(frame)
        self.model = MatrixFactorizationRecommender(
            num_users=len(self.interactions.user_index),
            num_items=len(self.interactions.item_index),
            embedding_dim=self.embedding_dim,
        )
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        user_ids, item_ids = np.nonzero(self.interactions.matrix > 0)
        labels = self.interactions.matrix[user_ids, item_ids]
        if len(labels) == 0:
            return self
        user_tensor = torch.tensor(user_ids, dtype=torch.long)
        item_tensor = torch.tensor(item_ids, dtype=torch.long)
        label_tensor = torch.tensor(labels, dtype=torch.float32)

        self.model.train()
        for _ in range(self.epochs):
            optimizer.zero_grad()
            logits = self.model(user_tensor, item_tensor)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, label_tensor)
            loss.backward()
            optimizer.step()
        return self

    def recommend(self, user_id: int, *, k: int = 10) -> list[int]:
        if self.interactions is None or self.model is None:
            raise RuntimeError("Model must be fit before recommendation")
        if user_id not in self.interactions.user_index:
            return []
        user_idx = self.interactions.user_index[user_id]
        seen_mask = self.interactions.matrix[user_idx] > 0
        item_ids = torch.arange(len(self.interactions.item_index), dtype=torch.long)
        user_ids = torch.full((len(self.interactions.item_index),), user_idx, dtype=torch.long)
        self.model.eval()
        with torch.no_grad():
            scores = self.model(user_ids, item_ids).numpy()
        scores[seen_mask] = -np.inf
        top_indices = np.argsort(scores)[::-1][:k]
        return [self.interactions.inverse_item_index[int(index)] for index in top_indices if np.isfinite(scores[index])]
