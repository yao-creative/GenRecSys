PROJECT_NAME = recsys-gen
UV = uv
PYTHON = $(UV) run python
PYTEST = $(UV) run pytest

.PHONY: requirements
requirements:
	$(UV) sync

.PHONY: lint
lint:
	$(UV) run ruff check

.PHONY: format
format:
	$(UV) run ruff check --fix
	$(UV) run ruff format

.PHONY: test
test:
	$(PYTEST)

.PHONY: train-baseline
train-baseline:
	$(PYTHON) -m recsys_gen.training.train --config configs/itemknn_yambda.yaml

.PHONY: acquire-movielens25m
acquire-movielens25m:
	$(PYTHON) -m recsys_gen.training.acquire --config configs/acquire_movielens25m.yaml

.PHONY: acquire-amazon-electronics
acquire-amazon-electronics:
	$(PYTHON) -m recsys_gen.training.acquire --config configs/acquire_amazon_electronics.yaml

.PHONY: acquire-amazon-beauty
acquire-amazon-beauty:
	$(PYTHON) -m recsys_gen.training.acquire --config configs/acquire_amazon_beauty.yaml

.PHONY: acquire-amazon-sports
acquire-amazon-sports:
	$(PYTHON) -m recsys_gen.training.acquire --config configs/acquire_amazon_sports.yaml

.PHONY: acquire-yelp
acquire-yelp:
	$(PYTHON) -m recsys_gen.training.acquire --config configs/acquire_yelp.yaml

.PHONY: prepare-movielens25m
prepare-movielens25m:
	$(PYTHON) -m recsys_gen.training.prepare --config configs/dataset_movielens25m.yaml

.PHONY: prepare-amazon-electronics
prepare-amazon-electronics:
	$(PYTHON) -m recsys_gen.training.prepare --config configs/dataset_amazon_electronics.yaml

.PHONY: prepare-amazon-beauty
prepare-amazon-beauty:
	$(PYTHON) -m recsys_gen.training.prepare --config configs/dataset_amazon_beauty.yaml

.PHONY: prepare-amazon-sports
prepare-amazon-sports:
	$(PYTHON) -m recsys_gen.training.prepare --config configs/dataset_amazon_sports.yaml

.PHONY: prepare-yelp
prepare-yelp:
	$(PYTHON) -m recsys_gen.training.prepare --config configs/dataset_yelp.yaml

.PHONY: train-sasrec
train-sasrec:
	$(PYTHON) -m recsys_gen.training.train --config configs/sasrec_yambda.yaml

.PHONY: dvc-repro
dvc-repro:
	$(UV) run dvc repro

.PHONY: docs
docs:
	$(UV) run mkdocs serve -f docs/mkdocs.yml

.PHONY: docs-build
docs-build:
	$(UV) run mkdocs build -f docs/mkdocs.yml
