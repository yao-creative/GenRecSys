from __future__ import annotations

from pathlib import Path

import polars as pl
import typer

from recsys_gen.data.dataset import filter_interactions, load_dataset, normalize_interactions, train_test_split_temporal
from recsys_gen.data.retrieval import (
    build_retrieval_examples,
    build_seen_items,
    build_vocab,
    build_index_lookup,
    encode_split,
    write_parquet,
)
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
    train.write_parquet(Path(output_dir) / "train.parquet")
    validation.write_parquet(Path(output_dir) / "validation.parquet")
    test.write_parquet(Path(output_dir) / "test.parquet")

    user_vocab = build_vocab(filtered, "user_id")
    item_vocab = build_vocab(filtered, "item_id", start_index=1)
    user_lookup = build_index_lookup(user_vocab)
    item_lookup = build_index_lookup(item_vocab)
    train_encoded = encode_split(train, user_lookup=user_lookup, item_lookup=item_lookup)
    validation_encoded = encode_split(validation, user_lookup=user_lookup, item_lookup=item_lookup)
    test_encoded = encode_split(test, user_lookup=user_lookup, item_lookup=item_lookup)

    write_parquet(user_vocab, Path(output_dir) / "user_vocab.parquet")
    write_parquet(item_vocab, Path(output_dir) / "item_vocab.parquet")
    write_parquet(train_encoded, Path(output_dir) / "train_encoded.parquet")
    write_parquet(validation_encoded, Path(output_dir) / "validation_encoded.parquet")
    write_parquet(test_encoded, Path(output_dir) / "test_encoded.parquet")
    write_parquet(
        build_retrieval_examples(
            train_encoded,
            train_encoded,
            max_history_length=payload["sequence"]["max_length"],
        ),
        Path(output_dir) / "retrieval_train.parquet",
    )
    write_parquet(
        build_retrieval_examples(
            train_encoded,
            validation_encoded,
            max_history_length=payload["sequence"]["max_length"],
        ),
        Path(output_dir) / "retrieval_validation.parquet",
    )
    write_parquet(
        build_retrieval_examples(
            pl.concat([train_encoded, validation_encoded], rechunk=False),
            test_encoded,
            max_history_length=payload["sequence"]["max_length"],
        ),
        Path(output_dir) / "retrieval_test.parquet",
    )
    write_parquet(build_seen_items(train_encoded), Path(output_dir) / "seen_train.parquet")


if __name__ == "__main__":
    app()
