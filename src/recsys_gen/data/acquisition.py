from __future__ import annotations

import gzip
import json
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlretrieve

import polars as pl

from recsys_gen.utils.io import ensure_dir


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    normalizer: str
    default_download_mode: str
    urls: tuple[str, ...] = ()
    manual_instructions: str | None = None


DATASET_SPECS: dict[str, DatasetSpec] = {
    "movielens25m": DatasetSpec(
        name="movielens25m",
        normalizer="movielens",
        default_download_mode="auto",
        urls=("https://files.grouplens.org/datasets/movielens/ml-25m.zip",),
    ),
    "amazon_electronics": DatasetSpec(
        name="amazon_electronics",
        normalizer="generic",
        default_download_mode="manual",
        manual_instructions=(
            "Download the Amazon Reviews 2023 Electronics review and metadata files "
            "from the official Amazon Reviews'23 release, place them under "
            "data/external/amazon_electronics/, then re-run acquisition."
        ),
    ),
    "amazon_beauty": DatasetSpec(
        name="amazon_beauty",
        normalizer="generic",
        default_download_mode="manual",
        manual_instructions=(
            "Download the Amazon Reviews 2023 Beauty review and metadata files "
            "from the official Amazon Reviews'23 release, place them under "
            "data/external/amazon_beauty/, then re-run acquisition."
        ),
    ),
    "amazon_sports": DatasetSpec(
        name="amazon_sports",
        normalizer="generic",
        default_download_mode="manual",
        manual_instructions=(
            "Download the Amazon Reviews 2023 Sports_and_Outdoors review and metadata files "
            "from the official Amazon Reviews'23 release, place them under "
            "data/external/amazon_sports/, then re-run acquisition."
        ),
    ),
    "yelp": DatasetSpec(
        name="yelp",
        normalizer="generic",
        default_download_mode="manual",
        manual_instructions=(
            "Download the Yelp Open Dataset archive and place the extracted review and "
            "business JSON files under data/external/yelp/, then re-run acquisition."
        ),
    ),
}


def get_dataset_spec(name: str) -> DatasetSpec:
    if name not in DATASET_SPECS:
        raise ValueError(f"Unsupported dataset: {name}")
    return DATASET_SPECS[name]


def acquire_dataset(payload: dict[str, Any]) -> dict[str, Any]:
    spec = get_dataset_spec(payload["name"])
    external_dir = ensure_dir(payload["external_dir"])
    download_cfg = _merge_download_config(spec, payload.get("download", {}))
    archives = _ensure_external_assets(download_cfg, external_dir)
    sources = _resolve_sources(payload["sources"], external_dir)
    _validate_sources(sources, download_cfg)

    normalizer = payload.get("normalizer", spec.normalizer)
    if normalizer == "movielens":
        interactions, items = _normalize_movielens(sources)
    elif normalizer == "generic":
        normalization_cfg = payload["normalization"]
        interactions, items = _normalize_generic(sources, normalization_cfg)
    else:
        raise ValueError(f"Unsupported normalizer: {normalizer}")

    interactions_path = Path(payload["raw_interactions_path"])
    items_path = Path(payload["raw_items_path"])
    ensure_dir(interactions_path.parent)
    ensure_dir(items_path.parent)
    interactions.write_parquet(interactions_path)
    items.write_parquet(items_path)

    manifest_path = external_dir / "acquisition_manifest.json"
    manifest = {
        "dataset": payload["name"],
        "download_mode": download_cfg["mode"],
        "archives": [str(path) for path in archives],
        "sources": {key: str(path) for key, path in sources.items()},
        "raw_outputs": {
            "interactions_path": str(interactions_path),
            "items_path": str(items_path),
        },
        "row_counts": {
            "interactions": interactions.height,
            "items": items.height,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _merge_download_config(spec: DatasetSpec, override: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": override.get("mode", spec.default_download_mode),
        "urls": list(override.get("urls", list(spec.urls))),
        "expected_archives": list(override.get("expected_archives", [])),
        "manual_instructions": override.get("manual_instructions", spec.manual_instructions),
    }


def _ensure_external_assets(download_cfg: dict[str, Any], external_dir: Path) -> list[Path]:
    mode = download_cfg["mode"]
    urls = [url for url in download_cfg.get("urls", []) if url]
    archives: list[Path] = []

    if mode == "auto":
        for url in urls:
            parsed = urlparse(url)
            filename = Path(parsed.path).name
            if not filename:
                raise ValueError(f"Cannot infer filename from URL: {url}")
            destination = external_dir / filename
            if not destination.exists():
                urlretrieve(url, destination)
            _extract_archive(destination, external_dir)
            archives.append(destination)
    elif mode == "manual":
        expected_archives = [external_dir / name for name in download_cfg.get("expected_archives", [])]
        missing_archives = [path for path in expected_archives if not path.exists()]
        if missing_archives:
            instructions = download_cfg.get("manual_instructions") or "Provide the required source files manually."
            missing_text = ", ".join(str(path.name) for path in missing_archives)
            raise FileNotFoundError(f"Missing manual dataset archives: {missing_text}. {instructions}")
        for archive in expected_archives:
            _extract_archive(archive, external_dir)
            archives.append(archive)
    elif mode == "skip":
        pass
    else:
        raise ValueError(f"Unsupported download mode: {mode}")

    return archives


def _extract_archive(archive_path: Path, external_dir: Path) -> None:
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as handle:
            handle.extractall(external_dir)
        return
    if archive_path.suffixes[-2:] == [".tar", ".gz"] or archive_path.suffix == ".tar":
        with tarfile.open(archive_path) as handle:
            handle.extractall(external_dir)
        return


def _resolve_sources(source_cfg: dict[str, str], external_dir: Path) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for key, raw_path in source_cfg.items():
        path = Path(raw_path)
        resolved[key] = path if path.is_absolute() else external_dir / raw_path
    return resolved


def _validate_sources(sources: dict[str, Path], download_cfg: dict[str, Any]) -> None:
    missing = [key for key, path in sources.items() if not path.exists()]
    if missing:
        instructions = download_cfg.get("manual_instructions")
        suffix = f" {instructions}" if instructions else ""
        raise FileNotFoundError(f"Missing dataset source files: {missing}.{suffix}")


def _normalize_movielens(sources: dict[str, Path]) -> tuple[pl.DataFrame, pl.DataFrame]:
    ratings = pl.read_csv(sources["ratings"])
    movies = pl.read_csv(sources["movies"])
    tags = pl.read_csv(sources["tags"]) if "tags" in sources and sources["tags"].exists() else None

    interactions = ratings.select(
        pl.col("userId").cast(pl.Int64).alias("user_id"),
        pl.col("movieId").cast(pl.Int64).alias("item_id"),
        pl.col("timestamp").cast(pl.Int64).alias("timestamp"),
        pl.lit(1).cast(pl.Int8).alias("target"),
        pl.lit("rating").alias("event_type"),
        pl.col("rating").alias("rating"),
    ).sort(["user_id", "timestamp", "item_id"])

    item_frame = movies.select(
        pl.col("movieId").cast(pl.Int64).alias("item_id"),
        pl.col("movieId").cast(pl.Utf8).alias("source_item_id"),
        pl.col("title").alias("title"),
        pl.col("genres").alias("genres"),
    )
    if tags is not None:
        tag_features = (
            tags.group_by("movieId")
            .agg(pl.col("tag").drop_nulls().unique().sort().alias("tag_list"))
            .with_columns(pl.col("tag_list").list.join(" | ").alias("tag_text"))
            .select(pl.col("movieId").alias("item_id"), pl.col("tag_text"))
            .with_columns(pl.col("item_id").cast(pl.Int64))
        )
        item_frame = item_frame.join(tag_features, on="item_id", how="left")

    return interactions, item_frame.sort("item_id")


def _normalize_generic(
    sources: dict[str, Path],
    normalization_cfg: dict[str, Any],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    interaction_cfg = normalization_cfg["interactions"]
    item_cfg = normalization_cfg["items"]

    interaction_source = _read_table(sources[interaction_cfg["source"]])
    item_source = _read_table(sources[item_cfg["source"]])

    interaction_user_col = interaction_cfg["user_id"]
    interaction_item_col = interaction_cfg["item_id"]
    item_item_col = item_cfg["item_id"]

    encoded_interactions, encoded_items = _encode_source_ids(
        interaction_source=interaction_source,
        item_source=item_source,
        interaction_user_col=interaction_user_col,
        interaction_item_col=interaction_item_col,
        item_item_col=item_item_col,
    )

    interactions = _build_canonical_interactions(encoded_interactions, interaction_cfg)
    items = _build_item_metadata(encoded_items, item_cfg)
    return interactions, items


def _read_table(path: Path) -> pl.DataFrame:
    suffixes = path.suffixes
    if suffixes[-1:] == [".parquet"]:
        return pl.read_parquet(path)
    if suffixes[-1:] == [".csv"] or suffixes[-2:] == [".csv", ".gz"]:
        return pl.read_csv(path)
    if suffixes[-1:] == [".tsv"] or suffixes[-2:] == [".tsv", ".gz"]:
        return pl.read_csv(path, separator="\t")
    if suffixes[-1:] == [".jsonl"] or suffixes[-2:] == [".jsonl", ".gz"]:
        return _read_ndjson(path)
    if suffixes[-1:] == [".json"] or suffixes[-2:] == [".json", ".gz"]:
        return _read_ndjson(path)
    raise ValueError(f"Unsupported source format: {path}")


def _read_ndjson(path: Path) -> pl.DataFrame:
    if path.suffix == ".gz":
        extracted = path.with_suffix("")
        with gzip.open(path, "rb") as source, extracted.open("wb") as target:
            shutil.copyfileobj(source, target)
        try:
            return pl.read_ndjson(extracted)
        finally:
            extracted.unlink(missing_ok=True)
    return pl.read_ndjson(path)


def _encode_source_ids(
    *,
    interaction_source: pl.DataFrame,
    item_source: pl.DataFrame,
    interaction_user_col: str,
    interaction_item_col: str,
    item_item_col: str,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    interactions = interaction_source.with_columns(
        pl.col(interaction_user_col).cast(pl.Utf8).alias("source_user_id"),
        pl.col(interaction_item_col).cast(pl.Utf8).alias("source_item_id"),
    )
    items = item_source.with_columns(pl.col(item_item_col).cast(pl.Utf8).alias("source_item_id"))

    user_map = (
        interactions.select("source_user_id")
        .unique()
        .sort("source_user_id")
        .with_row_index("encoded_user_id", offset=1)
        .with_columns(pl.col("encoded_user_id").cast(pl.Int64))
    )
    item_map = (
        pl.concat([interactions.select("source_item_id"), items.select("source_item_id")])
        .unique()
        .sort("source_item_id")
        .with_row_index("encoded_item_id", offset=1)
        .with_columns(pl.col("encoded_item_id").cast(pl.Int64))
    )

    encoded_interactions = interactions.join(user_map, on="source_user_id", how="left").join(
        item_map, on="source_item_id", how="left"
    )
    encoded_items = items.join(item_map, on="source_item_id", how="left")
    return encoded_interactions, encoded_items


def _build_canonical_interactions(frame: pl.DataFrame, cfg: dict[str, Any]) -> pl.DataFrame:
    event_type = cfg.get("event_type", "interaction")
    timestamp_expr = _timestamp_expr(frame, cfg["timestamp"]).alias("timestamp")
    columns = [
        pl.col("encoded_user_id").cast(pl.Int64).alias("user_id"),
        pl.col("encoded_item_id").cast(pl.Int64).alias("item_id"),
        timestamp_expr,
        pl.lit(1).cast(pl.Int8).alias("target"),
        pl.lit(event_type).cast(pl.Utf8).alias("event_type"),
        pl.col("source_user_id"),
        pl.col("source_item_id"),
    ]

    for source_col in cfg.get("extra_columns", []):
        columns.append(pl.col(source_col).alias(source_col))

    return frame.select(columns).sort(["user_id", "timestamp", "item_id"])


def _build_item_metadata(frame: pl.DataFrame, cfg: dict[str, Any]) -> pl.DataFrame:
    columns = [
        pl.col("encoded_item_id").cast(pl.Int64).alias("item_id"),
        pl.col("source_item_id"),
    ]
    extra_columns = cfg.get("extra_columns", {})
    for output_col, source_col in extra_columns.items():
        columns.append(pl.col(source_col).alias(output_col))
    return frame.select(columns).unique(subset=["item_id"]).sort("item_id")


def _timestamp_expr(frame: pl.DataFrame, source_col: str) -> pl.Expr:
    dtype = frame.schema[source_col]
    if dtype.is_integer() or dtype.is_float():
        return pl.col(source_col).cast(pl.Int64)
    return pl.coalesce(
        pl.col(source_col).cast(pl.Utf8).str.strptime(pl.Datetime, strict=False).dt.epoch(time_unit="s"),
        pl.col(source_col).cast(pl.Utf8).str.strptime(pl.Date, strict=False).cast(pl.Datetime).dt.epoch(time_unit="s"),
    ).cast(pl.Int64)
