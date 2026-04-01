# Code Review Rubric (MVP)

Use this rubric for every review. Keep findings concrete, with file/line references and impact.

## 1. Correctness

### Core checks
- Does the change solve the stated problem end-to-end?
- Does behavior match the canonical data/pipeline flow used by this repo?
- Are schema assumptions explicit and validated where needed?

### Edge-case checks
- Null/empty/missing input behavior is defined.
- Type/shape changes are handled (especially dataframe column drift).
- Save boundaries are correct: no hidden partial writes or modify-save-modify-save chains.

### Review output
- List functional regressions first (highest severity first).
- Call out any unhandled edge cases with exact failure mode.

## 2. Architecture

### Alignment checks
- Change aligns with DVC-orchestrated source of truth (`dvc.yaml` -> `lema_ml/pipelines/...`).
- Pipeline remains flat and readable as a linear chain of functions.
- Stage orchestration stays in pipeline orchestration/adapter layers, not spread across utilities.

### Coupling checks
- Functions stay close to pure except explicit save operations.
- Each function has one cohesive responsibility.
- Path logic uses `lema_ml.paths`; config logic uses `lema_ml.config`.
- Avoid new implicit coupling between notebooks/prototypes and production pipeline code.

### Review output
- Flag architectural drift and explain boundary violations.
- Note coupling introduced and minimal refactor to remove it.

## 3. Maintainability

### Readability checks
- Naming is clear and consistent with nearby functions/modules.
- Control flow is flat (`if/else` structure remains easy to scan).
- Pipeline intent is understandable quickly in linear order.

### Abstraction boundary checks
- Orchestration vs transformation vs persistence responsibilities are cleanly separated.
- No hidden root/path computation in pipeline/evaluation modules.
- New logic is added to the correct layer instead of convenience placement.

### Review output
- Flag readability debt that slows iteration.
- Suggest smallest clean-up following boyscout rule.

## 4. Tests

### Verifiability checks
- Behavior changes are covered by tests or deterministic checks.
- Tests verify externally observable behavior, not only implementation details.
- Assertions cover both success path and failure/guardrail path.

### Edge-case test checks
- Include at least one edge-case test for new logic.
- Include schema/column/empty-input tests where applicable.
- Validate persistence side effects for save operations.

### Review output
- State missing tests explicitly and what risk each gap creates.
- Mark whether current evidence is sufficient to ship.
