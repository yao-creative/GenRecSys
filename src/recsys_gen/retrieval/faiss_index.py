from __future__ import annotations

import faiss
import numpy as np


class FaissCandidateIndex:
    def __init__(self, dim: int) -> None:
        self.index = faiss.IndexFlatIP(dim)
        self.item_ids: list[int] = []

    def build(self, item_ids: list[int], embeddings: np.ndarray) -> None:
        if embeddings.ndim != 2:
            raise ValueError("Expected 2D embeddings matrix")
        self.item_ids = list(item_ids)
        self.index.reset()
        self.index.add(embeddings.astype("float32"))

    def search(self, query_embedding: np.ndarray, k: int) -> list[int]:
        scores, indices = self.index.search(query_embedding.astype("float32"), k)
        return [self.item_ids[idx] for idx in indices[0] if idx >= 0]
