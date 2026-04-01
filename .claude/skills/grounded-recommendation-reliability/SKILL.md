# Grounded Recommendation Reliability

You are a reliability engineer for LLM recommendation outputs. Your task is to prevent hallucinated citations, unsupported claims, and numeric drift in creator recommendations.

---

## Short Goal

Make every recommendation traceable to source evidence, numerically consistent with model outputs, and safe to ship behind production quality gates.

---

## Implementation Status

| Item | Status | Location |
|---|---|---|
| Citation integrity — cited permalinks exist in source | Done | `lema_ml/llm_eval/metrics.py` — `_normalize_url` + strict IG pattern |
| No placeholder/fabricated links | Done | `lema_ml/llm_recommendations/validate_links.py` |
| Grounding rules in P1/P2/P3 prompt contracts | Done | `prompts/p1_feature_explainer.py`, `p2_beli_vs_bikin.py`, `p3_series_content.py` |
| DML summary surfaces example_permalinks | Done | `lema_ml/llm/prompts/formatters/conclusion_summaries.py` |
| Numeric integrity (exp(ate)-1 drift check) | Not started | Needs `numeric_consistency_score` in `metrics.py` |
| Eval gate — hard fail when citation accuracy < threshold | Not started | Needs gate logic in `v4_llm_eval_pipelines.py` |
| Structured JSON output schema + strict parser | Not started | P1-P6 currently emit freeform markdown |
| Per-prompt validator JSON report artifact | Partial | `validate_links.py` covers format; no per-prompt JSON saved to artifacts |
| P4/P5/P6 grounding rules | Not started | Only P1/P2/P3 have Grounding Rules |
| Two-pass generation (draft + verifier) | Not started | |
| Regression eval suite in CI | Not started | |
| Confidence tagging per claim (causal/directional/insufficient) | Not started | |

---

## Loop To Resolve

Run this loop until all P0 checks pass and quality gates are green:

1. **Read latest artifacts**
   - Load recommendation outputs (`p1/p2/p3`) and source conclusion CSVs.
   - Build an evidence map: feature -> allowed permalinks, allowed metrics, allowed numeric ranges.

2. **Find failure modes**
   - Run `python -m lema_ml.llm_recommendations.validate_links --recs-dir <path>` to detect non-canonical and placeholder citations.
   - Check `citation_accuracy` in eval results (target >= 0.9).
   - Flag unsupported narrative claims (details not present in prompt context).
   - Flag numeric drift (`reported_pct` vs `exp(ate)-1`).

3. **Patch the pipeline**
   - Tighten prompt contracts (add `## Grounding Rules` to any prompt missing them — P4/P5/P6 still need this).
   - Add deterministic validators (link whitelist, placeholder check, numeric consistency check).
   - Consider schema-constrained output (JSON first, markdown render second).

4. **Re-run and verify**
   - Reproduce affected DVC stages: `uv run dvc repro -f llm_recommendation_eval_semantic_sparse_double_lasso@<creator>`
   - Recompute eval metrics and failure counts.
   - Confirm no regressions in output completeness.

5. **Evaluate the Run**
   - Read output files and validate against eval metrics.
   - Check for hallucination, statistical inaccuracies, or model interpretation issues.
   - Compare `citation_accuracy`, `specificity`, and judge pass rates vs baseline.

6. **Gate and report**
   - If any P0 issue remains: `BLOCKED`.
   - If P0 resolved but P1 remains: `DIRECTIONAL-ONLY`.
   - If P0+P1 resolved with stable metrics: `CLAIM-READY`.
   - Save report to `docs/codex/summaries/{DATE}-grounded-reliability-audit.md`.

---

## Priorities

### P0 (Must Fix)
- **Citation integrity** (done): every cited permalink must exist in source evidence. Implemented in `citation_accuracy_score` with `_normalize_url` and strict IG permalink pattern.
- **No placeholder/fabricated links** (done): `validate_links.py` detects non-canonical slugs and placeholder IDs (`permalink1`, `abc123`, etc.).
- **Numeric integrity** (not started): all percentage claims must deterministically match source ATE/CI transforms (`(exp(ate) - 1) * 100`). Needs `numeric_consistency_score` in `lema_ml/llm_eval/metrics.py`.
- **Eval gate** (not started): pipeline must fail when `citation_accuracy < 0.9` or `placeholder_links > 0`. Needs gate logic added to `v4_llm_eval_pipelines.py`.

### P1 (High Impact)
- **Prompt/data contract cleanup** (partial): Grounding Rules added to P1/P2/P3. P4 (topic deep-dive), P5 (contradiction), P6 (repost) still need them.
- **Structured output schema + strict parser** (not started): JSON-first output with markdown render second.
- **Per-prompt validator reports** (partial): `validate_links.py` covers link format; add per-prompt JSON artifacts saved alongside `llm_eval/` outputs.

### P2 (Scale / Hardening)
- **Two-pass generation** (not started): draft pass then verifier pass before saving.
- **Regression eval suite in CI** (not started): curated known-failure examples with expected citation accuracy bounds.
- **Confidence tagging** (not started): tag each claim as `causal`, `directional`, or `INSUFFICIENT_EVIDENCE`.

---

## Key Files To Check

- `lema_ml/llm_recommendations/prompts/` — P1-P6 prompt builders (check for Grounding Rules section)
- `lema_ml/llm_recommendations/validate_links.py` — format-only citation validator (done)
- `lema_ml/llm_recommendations/runner.py`
- `lema_ml/llm_recommendations/io.py`
- `lema_ml/llm_eval/metrics.py` — `citation_accuracy_score`, `specificity_score` (done)
- `lema_ml/llm_eval/evaluation.py`
- `lema_ml/llm/prompts/formatters/conclusion_summaries.py` — DML summary with example_permalinks (done)
- `lema_ml/pipelines/llm_recommendations/v4_llm_recommendations_pipelines.py`
- `lema_ml/pipelines/llm_eval/v4_llm_eval_pipelines.py` — needs eval gate (not started)
- `dvc.yaml`

---

## Done Criteria

- Zero fabricated/placeholder citations (`validate_links.py` reports `ok: true`).
- Zero numeric drift violations above tolerance.
- All recommendation claims have evidence references or `INSUFFICIENT_EVIDENCE`.
- `citation_accuracy` >= 0.9 on latest target creator run.
- Eval gate enforced: pipeline fails when thresholds not met.
- Grounding Rules present in all 6 prompt builders (P1-P6).
