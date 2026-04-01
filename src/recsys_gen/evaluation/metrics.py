from __future__ import annotations

import math
from collections.abc import Sequence


def recall_at_k(actual: Sequence[int], predicted: Sequence[int], k: int) -> float:
    if not actual:
        return 0.0
    hits = len(set(actual).intersection(predicted[:k]))
    return hits / len(set(actual))


def ndcg_at_k(actual: Sequence[int], predicted: Sequence[int], k: int) -> float:
    if not actual:
        return 0.0
    gains = 0.0
    for rank, item in enumerate(predicted[:k], start=1):
        if item in actual:
            gains += 1.0 / math.log2(rank + 1)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(k, len(set(actual))) + 1))
    return gains / ideal if ideal else 0.0


def mean_reciprocal_rank(actual: Sequence[int], predicted: Sequence[int]) -> float:
    actual_set = set(actual)
    for rank, item in enumerate(predicted, start=1):
        if item in actual_set:
            return 1.0 / rank
    return 0.0


def hit_rate_at_k(actual: Sequence[int], predicted: Sequence[int], k: int) -> float:
    return float(any(item in set(actual) for item in predicted[:k]))


def coverage_at_k(recommendations: Sequence[Sequence[int]], catalog_size: int, k: int) -> float:
    if catalog_size <= 0:
        return 0.0
    recommended = {item for recs in recommendations for item in recs[:k]}
    return len(recommended) / catalog_size


def diversity_at_k(recommendations: Sequence[Sequence[int]], k: int) -> float:
    if not recommendations:
        return 0.0
    uniqueness = [len(set(recs[:k])) / max(1, min(k, len(recs))) for recs in recommendations]
    return sum(uniqueness) / len(uniqueness)
