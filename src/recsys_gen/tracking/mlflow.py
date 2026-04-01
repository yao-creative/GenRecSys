from __future__ import annotations

from pathlib import Path
from typing import Any

import mlflow

from recsys_gen.config import get_settings


def _normalize_metric_name(name: str) -> str:
    return name.replace("@", "_at_")


def log_run_summary(
    *,
    run_name: str,
    experiment_name: str,
    params: dict[str, Any],
    metrics: dict[str, float],
    artifact_dir: str | Path | None = None,
) -> str:
    settings = get_settings()
    if settings.mlflow_tracking_uri:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=run_name):
        mlflow.log_params(params)
        mlflow.log_metrics({_normalize_metric_name(key): value for key, value in metrics.items()})
        if artifact_dir is not None and Path(artifact_dir).exists():
            mlflow.log_artifacts(str(artifact_dir), artifact_path="artifacts")
        active_run = mlflow.active_run()
        assert active_run is not None
        return active_run.info.run_id
