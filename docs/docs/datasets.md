# Dataset Overview

`recsys-gen` uses a common dataset contract so different public corpora can flow through the same acquisition, preparation, training, and evaluation pipeline.

## Common contract

Acquisition writes normalized parquet files under `data/raw/`:

- `<dataset>_interactions.parquet`
- `<dataset>_items.parquet` when item metadata is available

The canonical interaction schema is:

- `user_id`
- `item_id`
- `timestamp`
- `target`
- `event_type`

Dataset-specific columns such as ratings, verified-purchase flags, business attributes, or category metadata are preserved as extra columns alongside that core schema.

## Supported datasets

| Dataset | Status | Source files | Acquisition mode | Interaction extras | Item metadata extras |
| --- | --- | --- | --- | --- | --- |
| `movielens25m` | Full acquisition + preparation | `ratings.csv`, `movies.csv`, optional `tags.csv` | Automatic download from GroupLens | `rating` | `title`, `genres`, optional aggregated tag text |
| `amazon_electronics` | Full acquisition + preparation | `Electronics.csv.gz`, `meta_Electronics.jsonl.gz` | Manual file placement | `rating`, `verified_purchase` | `title`, `main_category`, `categories`, `average_rating`, `rating_number`, `store`, `price` |
| `amazon_beauty` | Full acquisition + preparation | `Beauty.csv.gz`, `meta_Beauty.jsonl.gz` | Manual file placement | `rating`, `verified_purchase` | `title`, `main_category`, `categories`, `average_rating`, `rating_number`, `store`, `price` |
| `amazon_sports` | Full acquisition + preparation | `Sports_and_Outdoors.csv.gz`, `meta_Sports_and_Outdoors.jsonl.gz` | Manual file placement | `rating`, `verified_purchase` | `title`, `main_category`, `categories`, `average_rating`, `rating_number`, `store`, `price` |
| `yelp` | Full acquisition + preparation | `yelp_academic_dataset_review.json`, `yelp_academic_dataset_business.json` | Manual file placement | `stars`, `useful`, `funny`, `cool` | `name`, `city`, `state`, `categories`, `stars`, `review_count` |
| `yambda` | Preparation config only | Prebuilt interaction parquet and item embeddings parquet | No acquisition config in repo | depends on supplied parquet | item embeddings via `item_embeddings_path` |

## Dataset notes

### MovieLens 25M

`movielens25m` is the most turnkey dataset in the repo. `training.acquire` can download and extract the archive automatically, then normalize ratings into the canonical interaction table and movies into item metadata. If `tags.csv` is present, tags are aggregated per movie and stored as free-text item metadata.

### Amazon Reviews'23 subsets

The three Amazon datasets share the same generic normalizer and schema shape. They require manual placement of the review CSV and metadata JSONL files under `data/external/<dataset>/` before acquisition runs. Reviews become interaction rows with `event_type=review`, while product catalog attributes are carried into the item metadata parquet for later retrieval or ranking features.

### Yelp Open Dataset

`yelp` is normalized from review and business JSON files. The review table becomes the interaction source, and business attributes become item metadata. This makes Yelp the main local-business style benchmark in the current repo, contrasting with the product-focused Amazon subsets and movie-focused MovieLens.

### Yambda

The repo includes `configs/dataset_yambda.yaml` and TorchRec configs that point at processed Yambda artifacts, but there is no corresponding `acquire_yambda.yaml` or acquisition implementation in `src/recsys_gen/data/acquisition.py`. In practice, that means Yambda is currently treated as an externally prepared dataset input rather than a first-class acquisition target.

## Preparation defaults

All current dataset preparation configs follow the same broad recipe:

- temporal split ratios of `0.8 / 0.1 / 0.1`
- maximum sequence length of `50`
- minimum sequence length of `2`
- `50` negatives per example with seed `7`

The filtering threshold is usually `min_user_interactions=5` and `min_item_interactions=5`. `yambda` is looser on users and items, with `3` and `1` respectively.
