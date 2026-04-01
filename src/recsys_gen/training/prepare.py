from __future__ import annotations

from pathlib import Path

import polars as pl
import typer

from recsys_gen.data.dataset import filter_interactions, load_dataset, normalize_interactions, train_test_split_temporal
from recsys_gen.data.sequences import build_user_sequences
from recsys_gen.utils.io import ensure_dir, load_yaml

app = typer.Typer(add_completion=False)


@app.command()
def main(config: str = typer.Option(..., "--config")) -> None:
    payload = load_yaml(config)["dataset"]
    output_dir = ensure_dir(payload["output_dir"])
    frame = load_dataset(payload["interactions_path"])
    normalized = normalize_interactions(frame, payload["column_map"])
    filtered = filter_interactions(
        normalized,
        min_user_interactions=payload["filters"]["min_user_interactions"],
        min_item_interactions=payload["filters"]["min_item_interactions"],
    )
    train, validation, test = train_test_split_temporal(
        filtered,
        train_ratio=payload["split"]["train_ratio"],
        validation_ratio=payload["split"]["validation_ratio"],
        test_ratio=payload["split"]["test_ratio"],
    )
    sequences = build_user_sequences(
        filtered,
        max_length=payload["sequence"]["max_length"],
        min_length=payload["sequence"]["min_length"],
    )
    train.write_parquet(Path(output_dir) / "train.parquet")
    validation.write_parquet(Path(output_dir) / "validation.parquet")
    test.write_parquet(Path(output_dir) / "test.parquet")
    sequences.write_parquet(Path(output_dir) / "sequences.parquet")


if __name__ == "__main__":
    app()
