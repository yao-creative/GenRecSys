from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


class SequenceDataset(Dataset):
    def __init__(self, examples: list[dict[str, object]], max_sequence_length: int) -> None:
        self.examples = examples
        self.max_sequence_length = max_sequence_length

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        row = self.examples[index]
        history = list(row["history"])
        target = int(row["target_item_id"])
        history = history[-self.max_sequence_length:]
        padding = [0] * (self.max_sequence_length - len(history))
        sequence = torch.tensor(padding + history, dtype=torch.long)
        return sequence, torch.tensor(target, dtype=torch.long)


class SASRec(nn.Module):
    def __init__(
        self,
        *,
        num_items: int,
        max_sequence_length: int,
        hidden_dim: int,
        num_heads: int,
        num_blocks: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.item_embedding = nn.Embedding(num_items + 1, hidden_dim, padding_idx=0)
        self.position_embedding = nn.Embedding(max_sequence_length, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_blocks)
        self.output = nn.Linear(hidden_dim, num_items + 1)

    def forward(self, sequences: torch.Tensor) -> torch.Tensor:
        positions = torch.arange(sequences.size(1), device=sequences.device).unsqueeze(0)
        hidden = self.item_embedding(sequences) + self.position_embedding(positions)
        hidden = self.dropout(hidden)
        encoded = self.encoder(hidden)
        pooled = encoded[:, -1, :]
        return self.output(pooled)


@dataclass
class SASRecTrainer:
    model: SASRec
    learning_rate: float
    batch_size: int
    epochs: int

    def fit(self, examples: list[dict[str, object]], max_sequence_length: int) -> SASRec:
        if not examples:
            return self.model
        dataset = SequenceDataset(examples, max_sequence_length)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        loss_fn = nn.CrossEntropyLoss()
        self.model.train()
        for _ in range(self.epochs):
            for sequences, targets in loader:
                optimizer.zero_grad()
                logits = self.model(sequences)
                loss = loss_fn(logits, targets)
                loss.backward()
                optimizer.step()
        return self.model

    def recommend(self, history: list[int], *, k: int) -> list[int]:
        self.model.eval()
        max_sequence_length = self.model.position_embedding.num_embeddings
        history = history[-max_sequence_length:]
        padding = [0] * (max_sequence_length - len(history))
        sequence = torch.tensor([padding + history], dtype=torch.long)
        with torch.no_grad():
            scores = self.model(sequence)[0]
        top_items = torch.topk(scores[1:], k=k).indices + 1
        return top_items.tolist()
