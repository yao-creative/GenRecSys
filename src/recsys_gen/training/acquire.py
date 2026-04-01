from __future__ import annotations

import typer

from recsys_gen.data.acquisition import acquire_dataset
from recsys_gen.utils.io import load_yaml

app = typer.Typer(add_completion=False)


@app.command()
def main(config: str = typer.Option(..., "--config")) -> None:
    payload = load_yaml(config)["dataset"]
    acquire_dataset(payload)


if __name__ == "__main__":
    app()
