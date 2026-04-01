# recsys-gen Overview

`recsys-gen` is organized as a small recommender-system research pipeline with three runtime surfaces:

- dataset preparation via `python -m recsys_gen.training.prepare`
- model training and offline evaluation via `python -m recsys_gen.training.train`
- a minimal serving stub via `recsys_gen.serving.api:app`

The package is intentionally layered:

1. Input data is loaded from parquet and normalized into a canonical interaction schema.
2. Temporal splits and user histories are derived from that normalized interaction table.
3. Models consume either interaction matrices (`ItemKNN`, matrix factorization) or sequence examples (`SASRec`).
4. Offline ranking metrics summarize recommendation quality on the validation split.
5. MLflow records parameters, metrics, and exported artifacts.

## Pipeline summary with maths

Let the normalized interaction table be

```text
X = {(u_i, v_i, t_i, y_i, e_i)}_{i=1}^N
```

where:

- `u_i` is a user id
- `v_i` is an item id
- `t_i` is a timestamp
- `y_i` is a binary target
- `e_i` is an event type

After filtering, each user's interactions are sorted by time and split into

```text
X_u = X_u^train ∪ X_u^val ∪ X_u^test
```

with

```text
|X_u^train| : |X_u^val| : |X_u^test| ≈ 0.8 : 0.1 : 0.1
```

subject to guardrails that ensure validation and test are non-empty when possible.

For sequence modeling, each user history produces supervised examples of the form

```text
h_u^{(j)} = [v_{u, j-L}, ..., v_{u, j-1}],   target = v_{u, j}
```

where `L <= 50` in the current config.

For matrix-based recommenders, the interaction matrix is

```text
R in {0,1}^{|U| x |V|}
```

with `R_uv = 1` when user `u` interacted with item `v`.

The current evaluation layer computes ranking metrics on top-`K` predictions:

```text
Recall@K(u) = |A_u ∩ P_u^K| / |A_u|
NDCG@K(u) = DCG@K(u) / IDCG@K(u)
MRR(u) = 1 / rank_u
Coverage@K = |∪_u P_u^K| / |V_val|
```

where:

- `A_u` is the set of held-out relevant items for user `u`
- `P_u^K` is the top-`K` predicted list
- `rank_u` is the first rank at which a relevant item appears
- `|V_val|` is the number of distinct validation items used as the coverage catalog

## Current execution surfaces

- `dvc.yaml` orchestrates `prepare_yambda`, `train_itemknn`, and `train_sasrec`
- `Makefile` provides convenience wrappers for training and `dvc repro`
- `scripts/bootstrap_sample_data.py` creates a tiny parquet dataset for local smoke runs

The package currently behaves more like a benchmark harness than a production service. The API layer exists, but the compute-heavy path is still the offline training and evaluation pipeline.
