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
