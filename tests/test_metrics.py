from recsys_gen.evaluation.metrics import (
    coverage_at_k,
    diversity_at_k,
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    recall_at_k,
)


def test_ranking_metrics() -> None:
    actual = [2, 4]
    predicted = [1, 2, 3, 4]
    assert recall_at_k(actual, predicted, 4) == 1.0
    assert hit_rate_at_k(actual, predicted, 2) == 1.0
    assert mean_reciprocal_rank(actual, predicted) == 0.5
    assert ndcg_at_k(actual, predicted, 4) > 0.0


def test_coverage_and_diversity() -> None:
    recs = [[1, 2, 3], [3, 4, 4]]
    assert coverage_at_k(recs, catalog_size=5, k=3) == 0.8
    assert diversity_at_k(recs, k=3) < 1.0
