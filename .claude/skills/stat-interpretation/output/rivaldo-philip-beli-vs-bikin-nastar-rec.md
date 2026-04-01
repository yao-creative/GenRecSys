# Beli vs Bikin Nastar — Content Recommendation for rivaldo.philip
**Date:** 2026-03-15 | **SDL Source:** 03-12-2026 (rivaldo-heroes, 997 posts) + 03-14-2026 (rivaldo-heroes-all, 1,165 posts) | **Target:** Views + Likes

---

## Creator Profile: rivaldo.philip "Beli vs Bikin" Track Record

rivaldo.philip has 6 confirmed Beli vs Bikin posts. Zero nastar/kue Lebaran content exists in the dataset. The format itself is proven. The question is: which execution of nastar lands in the right signal cluster?

| Caption | Views | Duration | Speech | TextOverlay |
|---------|-------|----------|--------|-------------|
| Mending beli atau bikin mie ayam jamur (Bakmi GM)? | **14,866** | 82s | 90% | 50% |
| Milk tea mending beli atau bikin? | 7,419 | 93s | 85% | 80% |
| Mending beli atau bikin pohon natal? | 6,444 | 57s | 90% | 70% |
| Beli vs bikin CoCo Ichibanya katsu + shabu curry | 4,440 | 79s | 70% | 40% |
| Beli vs Bikin Kimchi (Level 30 Samyang) | 2,990 | 87s | 70% | 30% |
| Mending beli atau bikin bouquet bunga Hari Ibu? | 2,411 | 56s | 70% | 40% |

**Pattern from rivaldo's own data:**
- Speech 85-90% → top 2 posts (7-15K views). Speech 70% → bottom 4 (2-5K).
- Duration 79-93s → all top performers. Under 60s → floor.
- Relatable everyday food (mie ayam, milk tea) > niche imports (CoCo Ichibanya, kimchi). Nastar is a Lebaran staple — same tier as mie ayam.

---

## SDL Signals Relevant to Nastar (03-12 Run, CAUSAL tier)

CI values not available in summary file — converted from point estimates only.

### Positive — What Nastar Should BE

| Feature | Metric | ATE | Converted Impact | Stability Flag |
|---------|--------|-----|-----------------|----------------|
| `dify_series_Dessert & Bakery Finds` | Views | +1.91 | **+575% views** | UNSTABLE (ATE>1.5, low prevalence 2.4%) — but replicated in 03-14 run |
| `dify_series_Dessert & Bakery Finds` | Likes | +2.05 | **+677% likes** | UNSTABLE — same caveat; treat as directional floor not point estimate |
| `65_scenario___` | Views | +1.36 | **+290% views** | Stable causal — scenario/comparison decision framing |
| `42_scientificsetting` | Views | +1.24 | **+246% views** | Stable causal — analytical/curiosity framing |
| `80_share` | Views | +1.19 | **+228% views** | Stable causal — shareable content format |

**Confirmed in 03-14 run (1,165 posts):**
- `190_food___` CAUSAL Likes +1.63 → +409% (direct replication of food signal)
- `33_instruction_clarity_clear_` CAUSAL Likes +1.34 → +280% (clear step-by-step narration)

### Negative — What Nastar Should NOT BE

| Feature | Metric | ATE | Converted Impact | Interpretation |
|---------|--------|-----|-----------------|----------------|
| `169_home_diy__` | Likes | -1.22 | **-70% likes** | Home craft DIY framing kills likes |
| `34_usefulness___` | Views | -1.49 | **-78% views** | Pure utility/tips format kills views |
| `34_usefulness___` | Likes | -1.23 | **-71% likes** | Pure utility/tips format kills likes |

**Confirmed stronger in 03-14 run:**
- `31_traditional_holiday_diy_arts` CAUSAL Likes -2.33 → **-90% likes** (stronger version of the same negative signal)
- `16_money_avoiding_frustration_saving` DIRECTIONAL Likes -0.92 → -60% (savings-led framing hurts)

---

## Cluster Content Verification (Section 2 Protocol)

### `dify_series_Dessert & Bakery Finds` — What's Actually Inside

The series label says "Dessert & Bakery Finds." Checked against actual posts (03-14-2026 data):

- onebitebigbite: "Mil Toast House beneran mau buka di Jakarta?" (bakery discovery, 187K views)
- onebitebigbite: "Spesialis coklat baru di Blok M!" (chocolate room discovery, 390K views)
- onebitebigbite: "ketika cheesecake dikawinin sama Japanese chiffon cake" (dessert reveal, 446K views)
- mgdalenaf: "Ga ikut2an tren roti viral tp justru itu yg bikin tempat ini beda! Roti di @javasari.id" (bakery feature, 53K views)

**Label says:** Dessert & Bakery content
**Content is actually:** DISCOVERY/REVIEW format — cafe reveals, bakery finds, taste test reveals. NOT home baking tutorials.

**For nastar specifically:** The signal attaches to the REVIEW/DISCOVERY framing. Showing up at a famous nastar bakery, doing a taste test, revealing price-per-cookie — this is the cluster. Not: sitting in your kitchen making dough step by step.

### `31_traditional_holiday_diy_arts` — What's Actually Inside (the trap)

Posts that fall here:
- tiranissya: DIY bantal biskuit, DIY cermin ala Pinterest, DIY bag charm, DIY fireplace rack — all home craft projects
- widi.nurrohman: DIY sayap Garuda (craft project)
- rivaldo.philip's own post here: "I made my own Rinjani summit: Part 2" (628 views)

**Label says:** Traditional holiday DIY / arts and crafts
**Content is actually:** Home craft tutorials with a seasonal/cultural framing
**The danger for nastar:** "Bikin nastar sendiri untuk Lebaran" is almost verbatim this cluster. This framing → -90% likes.

---

## Recommendation

### Make this video

> **"Gue cobain bikin nastar vs beli dari [famous brand] — mana lebih worth buat Lebaran?"**

**Format brief — based on mie ayam template (best BvB post):**

| Parameter | Target | Why |
|-----------|--------|-----|
| Duration | 79-85s | mie ayam at 82s is the top; milk tea at 93s is acceptable ceiling |
| Speech | 88-90% | Direct predictor of BvB performance in rivaldo's own data |
| TextOverlay | ~50% | mie ayam at 50% outperformed milk tea at 80% |
| Hook | Comparison question | "Nastar [Brand X] 80rb/toples — worth it ga?" |

**Structure (82s target):**
- **0-5s:** Hook — show a premium nastar toples with price visible. One line: "Ini [X] ribu setoples."
- **5-25s:** BELI segment — taste test from 1-2 famous brands. Quick verdict on flavor/texture/cost-per-cookie.
- **25-65s:** BIKIN segment — show the key moments of making with narration. Cost tracking visible. NOT step-by-step tutorial — treat it like a cost breakdown with process highlights.
- **65-82s:** Verdict — side by side, personal call, end with comparison question to audience.

**Framing to use:**
- "Gue tes dua opsi buat Lebaran" (scenario/test framing → `65_scenario`)
- "Ini hasilnya" / "mana yang lebih worth?" (discovery framing → `dify_series_Dessert & Bakery Finds`)
- Show the ingredient quality difference (analytical framing → `42_scientificsetting` / curiosity)

### What to AVOID

1. **"Tutorial bikin nastar Lebaran step-by-step"** → falls into `31_traditional_holiday_diy_arts` (-90% likes). The bikin side should be shown as evidence in a comparison, not as a how-to guide.
2. **"Lebih hemat X% bikin sendiri"** as the hook → `16_money_avoiding_frustration_saving` (-60% likes directional). Cost comparison is fine as supporting data — it should not be the hero claim.
3. **"Tips bikin nastar yang sempurna"** → `34_usefulness___` (-78% views, -71% likes). Pure utility framing is the second strongest negative signal in the dataset.
4. **Under 60s** — rivaldo's floor for food BvB content.
5. **Speech below 80%** — every sub-80% BvB post lands under 3K views.

### Timing

Lebaran 2026 is ~March 30-31. This post should go out **now (March 15-22)** to catch the pre-Lebaran discovery window. Nastar content is bought/made in the 2 weeks before Lebaran, not after.

---

## Expected Performance

Based on rivaldo.philip's existing BvB food range and SDL signal alignment:

| Scenario | Views |
|----------|-------|
| Baseline (matches mie ayam format, food topic) | 7,000–15,000 |
| With Lebaran timing lift | 15,000–30,000 |
| If captures `dify_series_Dessert & Bakery Finds` signal | Ceiling unquantified (flag: ATE unstable, very low prevalence cluster) |

The Lebaran timing variable is the largest wildcard. rivaldo.philip already demonstrated Lebaran resonance (18.3M views on a Lebaran air-pollution post), though that post was a short-form viral format (8s, 0% speech) — a different mechanism entirely.

---

## Data Sources

- **SDL reference:** `docs/codex/summaries/2026-03-12-rivaldo-heroes-sparse-double-lasso.md`
- **Supporting SDL run:** `data/analytics/ig-media/03-14-2026/rivaldo-heroes-all/conclusions/semantic_sparse_double_lasso/`
- **Creator posts:** `data/processed/03-14-2026/rivaldo-heroes-all_v4_*_id.parquet`
- **Cluster content verification:** permalinks from conclusions CSV joined to categorical features parquet
