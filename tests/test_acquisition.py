import csv
import gzip
import json
import zipfile
from pathlib import Path

import polars as pl
import pytest

from recsys_gen.data.acquisition import acquire_dataset


def test_acquire_movielens_from_local_zip(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive_src" / "ml-25m"
    archive_root.mkdir(parents=True)
    _write_csv(
        archive_root / "ratings.csv",
        ["userId", "movieId", "rating", "timestamp"],
        [
            [1, 10, 4.5, 100],
            [1, 11, 3.5, 200],
            [2, 10, 5.0, 150],
        ],
    )
    _write_csv(
        archive_root / "movies.csv",
        ["movieId", "title", "genres"],
        [
            [10, "First Movie", "Drama"],
            [11, "Second Movie", "Comedy"],
        ],
    )
    _write_csv(
        archive_root / "tags.csv",
        ["userId", "movieId", "tag", "timestamp"],
        [
            [1, 10, "moody", 110],
            [2, 10, "classic", 130],
        ],
    )

    archive_path = tmp_path / "ml-25m.zip"
    with zipfile.ZipFile(archive_path, "w") as handle:
        for path in archive_root.rglob("*"):
            handle.write(path, path.relative_to(archive_root.parent))

    payload = {
        "name": "movielens25m",
        "normalizer": "movielens",
        "external_dir": str(tmp_path / "external"),
        "raw_interactions_path": str(tmp_path / "raw" / "movielens25m_interactions.parquet"),
        "raw_items_path": str(tmp_path / "raw" / "movielens25m_items.parquet"),
        "download": {"mode": "auto", "urls": [archive_path.as_uri()]},
        "sources": {
            "ratings": "ml-25m/ratings.csv",
            "movies": "ml-25m/movies.csv",
            "tags": "ml-25m/tags.csv",
        },
    }

    manifest = acquire_dataset(payload)

    assert manifest["row_counts"]["interactions"] == 3
    interactions = pl.read_parquet(payload["raw_interactions_path"])
    items = pl.read_parquet(payload["raw_items_path"])
    assert interactions.columns[:5] == ["user_id", "item_id", "timestamp", "target", "event_type"]
    assert interactions["event_type"].to_list() == ["rating", "rating", "rating"]
    assert items.filter(pl.col("item_id") == 10)["tag_text"].item() == "classic | moody"


def test_acquire_amazon_generic_sources(tmp_path: Path) -> None:
    external_dir = tmp_path / "external"
    external_dir.mkdir()
    _write_gzip_text(
        external_dir / "Electronics.csv.gz",
        "\n".join(
            [
                "user_id,parent_asin,timestamp,rating,verified_purchase",
                "u1,p1,1000,5,true",
                "u1,p2,2000,4,false",
                "u2,p1,3000,5,true",
            ]
        )
        + "\n",
    )
    _write_gzip_text(
        external_dir / "meta_Electronics.jsonl.gz",
        "\n".join(
            [
                json.dumps(
                    {
                        "parent_asin": "p1",
                        "title": "Phone",
                        "main_category": "Electronics",
                        "categories": ["Phones"],
                        "average_rating": 4.5,
                        "rating_number": 100,
                        "store": "StoreA",
                        "price": 499.0,
                    }
                ),
                json.dumps(
                    {
                        "parent_asin": "p2",
                        "title": "Headphones",
                        "main_category": "Electronics",
                        "categories": ["Audio"],
                        "average_rating": 4.1,
                        "rating_number": 50,
                        "store": "StoreB",
                        "price": 199.0,
                    }
                ),
            ]
        )
        + "\n",
    )

    payload = {
        "name": "amazon_electronics",
        "normalizer": "generic",
        "external_dir": str(external_dir),
        "raw_interactions_path": str(tmp_path / "raw" / "amazon_electronics_interactions.parquet"),
        "raw_items_path": str(tmp_path / "raw" / "amazon_electronics_items.parquet"),
        "download": {"mode": "skip"},
        "sources": {"reviews": "Electronics.csv.gz", "meta": "meta_Electronics.jsonl.gz"},
        "normalization": {
            "interactions": {
                "source": "reviews",
                "user_id": "user_id",
                "item_id": "parent_asin",
                "timestamp": "timestamp",
                "event_type": "review",
                "extra_columns": ["rating", "verified_purchase"],
            },
            "items": {
                "source": "meta",
                "item_id": "parent_asin",
                "extra_columns": {
                    "title": "title",
                    "main_category": "main_category",
                    "categories": "categories",
                },
            },
        },
    }

    acquire_dataset(payload)

    interactions = pl.read_parquet(payload["raw_interactions_path"])
    items = pl.read_parquet(payload["raw_items_path"])
    assert set(interactions["source_user_id"].to_list()) == {"u1", "u2"}
    assert set(interactions["source_item_id"].to_list()) == {"p1", "p2"}
    assert items.columns == ["item_id", "source_item_id", "title", "main_category", "categories"]
    assert items.height == 2


def test_acquire_yelp_requires_manual_files(tmp_path: Path) -> None:
    payload = {
        "name": "yelp",
        "normalizer": "generic",
        "external_dir": str(tmp_path / "external"),
        "raw_interactions_path": str(tmp_path / "raw" / "yelp_interactions.parquet"),
        "raw_items_path": str(tmp_path / "raw" / "yelp_items.parquet"),
        "download": {
            "mode": "manual",
            "manual_instructions": "Place the Yelp Open Dataset files in data/external/yelp/.",
        },
        "sources": {
            "reviews": "yelp_academic_dataset_review.json",
            "businesses": "yelp_academic_dataset_business.json",
        },
        "normalization": {
            "interactions": {
                "source": "reviews",
                "user_id": "user_id",
                "item_id": "business_id",
                "timestamp": "date",
            },
            "items": {
                "source": "businesses",
                "item_id": "business_id",
                "extra_columns": {"name": "name"},
            },
        },
    }

    with pytest.raises(FileNotFoundError, match="Place the Yelp Open Dataset files"):
        acquire_dataset(payload)


def _write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _write_gzip_text(path: Path, contents: str) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(contents)
