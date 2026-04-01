from __future__ import annotations

from pathlib import Path

import polars as pl


def main() -> None:
    output = Path("data/raw/yambda_interactions.parquet")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pl.DataFrame(
        {
            "user_id": [1, 1, 1, 2, 2, 2, 3, 3, 3],
            "item_id": [10, 11, 12, 10, 13, 14, 11, 13, 15],
            "timestamp": [1, 2, 3, 1, 2, 3, 1, 2, 3],
            "target": [1] * 9,
            "event_type": ["listen"] * 9,
        }
    )
    frame.write_parquet(output)


if __name__ == "__main__":
    main()
