from pathlib import Path

import yaml


def test_dvc_stages_exist() -> None:
    config = yaml.safe_load(Path("dvc.yaml").read_text(encoding="utf-8"))
    stages = config["stages"]
    assert "acquire_movielens25m" in stages
    assert "acquire_amazon_electronics" in stages
    assert "acquire_amazon_beauty" in stages
    assert "acquire_amazon_sports" in stages
    assert "acquire_yelp" in stages
    assert "prepare_yambda" in stages
    assert "prepare_movielens25m" in stages
    assert "prepare_amazon_electronics" in stages
    assert "prepare_amazon_beauty" in stages
    assert "prepare_amazon_sports" in stages
    assert "prepare_yelp" in stages
    assert "train_torchrec_yambda" in stages
    assert "eval_torchrec_yambda" in stages


def test_configs_target_new_package() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "recsys-gen" in readme
    assert "lema_ml" not in readme


def test_dataset_configs_include_item_sidecar_paths() -> None:
    for path in Path("configs").glob("dataset_*.yaml"):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        dataset_config = config["dataset"]
        assert "item_metadata_path" in dataset_config or "item_embeddings_path" in dataset_config
