# Why Some "Beli vs Bikin" Content Fails — Contradiction Analysis
**Date:** 2026-03-15 | **Focus:** rivaldo.philip format patterns | **Comparison:** High performers vs low performers across dataset

---

## Quick Answer

"Beli vs bikin" posts underperform when:
1. **Duration too short** — low performers average 34s vs 73s for high performers
2. **Speech/narration too low** — low performers average 45% speech vs 75% for high performers
3. **Topic has no instructional value** — comparison works best when there's a genuine skill or process to demonstrate
4. **Wrong semantic framing** — holiday/arts-crafts framing hurts likes (causal signal -2.33); cost-savings-first hooks hurt likes (directional -0.92)

This is NOT a failure of the "beli vs bikin" format itself. rivaldo.philip has proven the format works. The pattern is execution-dependent.

---

## Evidence: High vs Low Performers Across Dataset

### The Hard Numbers (beli/bikin posts in dataset, n=275 with views data)

| Group | n | Avg Views | Avg Duration | Avg Speech |
|-------|---|-----------|--------------|------------|
| High performers (>10K views) | 181 | 397,936 | 73s | 75% |
| Low performers (<2K views) | 57 | 467 | 34s | 45% |

**Key insight:** Duration and narration are the clearest separators. Topic fit is secondary.

---

## rivaldo.philip's Own Beli-Bikin Performance Spread

| Post | Views | Duration | Speech | Outcome |
|------|-------|----------|--------|---------|
| Mending beli atau bikin mie ayam jamur (Bakmi GM)? | 14,865 | 82s | 90% | Best food beli-bikin post |
| Milk tea mending beli atau bikin? (Boba, soy bean...) | 7,418 | 93s | 85% | 2nd best |
| Mending beli atau bikin pohon natal? | 6,443 | 58s | 90% | Mid |
| Beli vs bikin CoCo Ichibanya katsu + shabu curry | 4,439 | 79s | 70% | Mid |
| Beli vs Bikin Kimchi (Level 30 Samyang) | 2,989 | 86s | 70% | Below mid |
| Mending beli atau bikin bouquet bunga Hari Ibu? | 2,410 | 56s | 70% | Low |

**Pattern:** The two best posts (mie ayam, milk tea) share 82-93s duration and 85-90% speech. The two weakest food posts are shorter or have lower speech.

Niche/imported items (CoCo Ichibanya, Kimchi) also underperform relative to locally relatable everyday foods (mie ayam, milk tea).

---

## Detailed Failure Analysis

### What Makes a "Beli vs Bikin" Post Fail

**Short duration + low narration:**

A 30-40s post with 45% speech leaves no room to:
- Build curiosity about the outcome
- Explain why the DIY version is worth attempting
- Show enough of the process to create learning value
- Create emotional investment in the result

The comparison hook alone ("beli vs bikin X") does not hold attention. The process content does.

**Commodity foods with no instructional gap:**

For foods where the comparison is obvious or the DIY version offers nothing new — no skill transfer, no cost surprise, no "I didn't know you could do this" moment — the format underdelivers. The audience's implicit question is "why am I watching this?"

The format works best when there is a genuine answer to that question: a technique to learn, a price gap that surprises, or a process that most people haven't seen.

---

## High Performer Examples From Dataset

### machelwie — Kaldu Ayam Kampung (Cluster 134)
- **Creator:** machelwie
- **Caption:** "❗️SAVE DULU❗️ Karena ini cara tergampang untuk bikin kaldu ayam kampung yang nutrisinya daebakk!!✨"
- **Performance:** 445,264 views | 12,985 likes
- **Format:** 58s | 90% speech
- **Why it worked:**
  - Kaldu ayam kampung has a genuine skill component — most people buy pre-made stock
  - Health angle ("nutrisi daebakk") gives a reason to DIY beyond cost
  - 90% narration explains each step with credibility
  - "SAVE DULU" hook signals high-utility content

### nadya.mci8 — "Ga sempet beli, bikin aja" (Rice Noodles)
- **Creator:** nadya.mci8
- **Caption:** "Ga sempet beli, bikin aja 🤭 Rice Noodle: 1 cup rice flour..."
- **Performance:** 631,511 views | 14,952 likes
- **Format:** 34s | 10% speech (mostly recipe text on screen)
- **Why it worked despite low speech:**
  - Surprise factor — most people don't know rice noodles can be made at home in minutes
  - The "bikin aja" hook positions it as a practical shortcut, not a tutorial
  - Low speech works here because the concept is simple enough for text-only delivery
  - Exception case: the surprise outweighs the format deficit

**Note:** This is an exception to the duration/speech pattern. The surprise-DIY format can succeed with short/text-heavy content, but only when the content itself delivers a genuine "I didn't know that was possible" moment.

### onebitebigbite — "Dari gagal jualan bakso..."
- **Creator:** onebitebigbite
- **Caption:** "Dari gagal jualan bakso, sekarang sukses bikin Thai food seenak ini"
- **Performance:** 94,234 views | 26,066 likes
- **Why it worked:**
  - The angle is personal redemption (failure → success), not a beli-vs-bikin comparison
  - "Bakso" is mentioned in the context of past failure, not as the comparison subject
  - The actual topic is Thai food discovery + entrepreneur story — different category

---

## SDL Signals That Explain the Pattern

### Causal Signals for Likes (strongest evidence)

| Feature | ATE | What It Means |
|---------|-----|---------------|
| `31_traditional_holiday_diy_arts` | -2.33 | Holiday tradition / arts-crafts framing HURTS likes |
| `190_food___` | +1.63 | Food content HELPS likes |
| `23_decor_decoration_diy_wall` | -1.58 | Decoration/home-crafts framing HURTS likes |
| `33_instruction_clarity_clear_` | +1.34 | Instructional clarity HELPS likes |

### Directional Signals for Views

| Feature | ATE | What It Means |
|---------|-----|---------------|
| `190_food___` | +0.73 | Food content directionally helps views |
| `81_instruct_make__` | +0.66 | "How to make" framing helps views |
| `33_tutorial_implied__` | +0.61 | Even an implied tutorial format helps views |

**Practical implication:** Nastar framed as "step-by-step bikin nastar sendiri" (instructional clarity + food label) aligns with positive signals. Nastar framed as "kue lebaran tradisional bikin vs beli" (holiday tradition + arts/crafts adjacent) hits two negative causal signals simultaneously.

---

## Food Topic Taxonomy: What Works With "Beli vs Bikin"

### Works Well

**Skill-based foods** — require technique the audience doesn't already know:
- Kaldu ayam kampung (stock-making is a learnable skill)
- Rice noodles (surprising that it's DIY-possible)
- Specialty drinks (milk tea formulation, recipe-specific)

**Foods with a process-reveal** — the "how it's made" is the content:
- Foods with multiple steps that justify 70-90s duration
- Recipes where the DIY version has a meaningful difference from bought (taste, health, cost)

### Does Not Work Well

**Commodity street foods** where the comparison offers nothing:
- Items where bought and homemade versions are functionally equivalent
- Items requiring specialist equipment that defeats the "bikin sendiri" premise
- Foods where the "bikin" version is not clearly superior in any dimension

**Holiday/seasonal-framed DIY** — the SDL causal signal (-2.33 for `31_traditional_holiday_diy_arts`) is the strongest negative finding in the dataset for likes. Even if nastar is Lebaran-associated, framing the content as "bikin kue lebaran" may trigger this penalty. Frame it as a food skill post instead.

---

## Nastar Specifically: The Risk and the Path Around It

Nastar occupies a difficult position: it is strongly associated with Lebaran (activates the holiday/tradition signal), but it is also a genuinely skill-based food (dough texture and filling ratio matter, not everyone can execute it well).

**The risk:** Framing as "bikin kue lebaran tradisional" → likely triggers the -2.33 causal penalty for likes.

**The path around it:** Frame as a food skill post, not a cultural tradition post:
- "Nastar yang ga pecah dan tidak lengket — bikin sendiri vs beli jadi" (skill-focused hook)
- Not "Kue lebaran kesukaan keluarga, bikin sendiri yuk!" (tradition hook)

The former positions nastar as a technique challenge. The latter positions it as a seasonal cultural activity, which the model consistently penalizes.

---

## Appendix: Data Sources

- **Dataset:** rivaldo-heroes-all (n=1,165 posts with views data), 03-14-2026
- **Model:** Sparse Double Lasso (DML), v4 semantic features
- **SDL output:** `data/analytics/ig-media/03-14-2026/rivaldo-heroes-all/conclusions/semantic_sparse_double_lasso/`
- **High/low performer groupings:** beli/bikin caption keyword match (n=275 total), views thresholds >10K and <2K
