from pathlib import Path

import yaml


def test_dvc_stages_exist() -> None:
    config = yaml.safe_load(Path("dvc.yaml").read_text(encoding="utf-8"))
    stages = config["stages"]
    assert "prepare_yambda" in stages
    assert "train_itemknn" in stages
    assert "train_sasrec" in stages


def test_configs_target_new_package() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "recsys-gen" in readme
    assert "lema_ml" not in readme
