I'm focused mostly on the notebooks/llm_forensic_v4/ folder for mvp data analytics, my preferred data processing dataframe runs on polars however for profiling and analytics i use pandas often.

my pipeline entry points live in lema_ml/preprocess/pipelines.py (ETL) and lema_ml/pipelines/ (feature, model, recommendations, llm_recommendations, llm_eval stages). All related core logic is in lema_ml/.

The canonical schema for data analytic features from media insight content is defined structurally via lema_ml/features/v4_parsing.py (JSON flattening) and the feature column naming conventions in lema_ml/config.py.

- I'm in my mvp stage, I'm focused on clean + fast iteration. plus functionality you'll have to label my intent before answering always.

- always give me a short 2 line critique of the current code architecture and another 2 lines of next steps or progression for future architecture of my mvp.

- Boyscout rule to always leave the code slightly better than when you found it.

- code except for saving data should be as close or as tight to a pure function as possible.


pipeline related code are all prototyped in notebooks folder as a notebook and then refactored into lema_ml which is e2e single source of truth of pipeline functions assets and orchestration.


# Project Rules

## Documentation

- **Location:** All project documentation/ session summaries or change summaries must be saved in the `./docs` directory and `./docs/codex/summaries/` subdirectories respectively and properly organized in subfolders if needed. DO THIS ALWAYS when a problem seems to be end to end resolved. include the date in the filename. DATE-SESSION-NAME.md

- **Root Policy:** Do not create or move any `.md` files to the project root, except for `README.md`, `AGENTS.md`, and `CLAUDE.md`.

- **Naming:** Use kebab-case for filenames (e.g., `./docs/setup-guide.md`).

- Variable names for data types like dataframes or matrices should follow the format `<variable_name>_<variable_type>` to make their type clear.

- File names if they're in lema_ml/pipelines they should end in _pipelines.py

- Function names should be clean and consistent to what they do and the rest of the functions of similar level / functionality.



**Pipeline:** 

- pipeline related code are all prototyped in notebooks folder as a notebook and then refactored into lema_ml 

- the central source of production truth is orchestrated dvc.yaml which calls lema_ml/pipelines folder as single source of truth of pipeline functions assets and orchestration. modify or critique in accordance to this dvc orchestrated source of truth.

- pipelines should be flat and mainly readable as chain of functions. If it takes more than 5 seconds to figure out what the pipeline is doing by reading in linear order --> refactor it.

- flat if else statements

- lema_ml/pipelines/models/v4_model_pipelines.py::model_fit_pipeline is the golden example of a clean pipeline code style.

- dvc.yaml calls lema_ml/pipelines/<stage>/v<version>_<endpoint_name>_pipelines.py through their main function while

-  lema_ml/pipelines/<stage>/orchestration_pipelines.py acts as an adapter to lema_ml/<stage> containing high level pipeline orchestration logic of the specific pipeline stage.

- **Thin pipelines:** Pipeline files (`pipelines/<stage>/`) must be thin orchestration — only `main()`, CLI argparse, and a `run_*()` function that chains imports. Core domain logic (scoring, data loading, LLM execution, I/O) lives in `lema_ml/<domain>/` modules (e.g., `evaluation/`, `llm/`, `models/`). Target: ~60-150 lines per pipeline file.

- **1:1 DVC mapping:** Each `pipelines/<stage>/` folder maps to a DVC stage group. Folder name = DVC stage name. No catch-all folders.

- **No cross-pipeline imports:** If two pipeline stages share logic, extract it into a core `lema_ml/<domain>/` module. Never import from one pipeline into another.

- **DVC deps must list all imported core modules:** Every `lema_ml/<domain>/` module that a pipeline imports must appear in that stage's `deps:` in `dvc.yaml`. DVC only invalidates when deps change — unlisted imports silently skip reruns.

- **Core module layout:** Domain logic lives in `lema_ml/<domain>/` with consistent naming:
  - `*_loader.py` — data discovery and loading (e.g., `conclusions_loader.py`)
  - `*_scoring.py` — pure scoring/classification functions (e.g., `recommendation_scoring.py`)
  - `*_metrics.py` — metric computation (e.g., `llm_metrics.py`)
  - `*_io.py` — save/load I/O for artifacts (e.g., `llm_rec_io.py`, `recommendation_io.py`)
  - `*_prompts.py` — prompt builders (e.g., `llm_rec_prompts.py`, functions named `build_p<N>_*`)
  - Current domains: `evaluation/`, `llm/`, `models/`, `features/`, `tracking/`, `clients/`

- each function saving should happen the end and completely be just whatever was modified or created by the function. If there's modifys-save-modify-save then truncate logic into two functions

- A function should perform a single cohesive operation, as described by its name. It should be flat and use nesting only when necessary.

## Paths And Config

- Use `lema_ml.paths` as the single source of truth for all filesystem paths (`PROJ_ROOT`, `DATA_DIR`, `PROCESSED_DATA_DIR`, analytics/visualization helpers).
- Do not compute runtime roots with `Path(__file__).parents[...]` inside pipeline/evaluation modules.
- Use `lema_ml.config` for non-path runtime settings and constants; if path constants are needed from config, they must originate from/re-export `lema_ml.paths`.
- New path logic should be added to `lema_ml.paths` first, then consumed by other modules.

## DVC commands:

- Run through ```uv run dvc repro <stage-name>``` and etc modify for other dvc capabilities

## Validation for implementation session:

- After finishing a session, write me a development flow of me as the software/ architect/ ml engineer where do i start reading and current modeling evaluation entry point as engineer for my development flow, to understand the newly refactored code base and the outputs of the pipeline, quality of the models and even their eval/ (code ran results), if they're upgraded and reran and how to test it.