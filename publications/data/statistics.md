# NAIL Institute — Statistical Analysis Summary

*Public release of key statistical findings from the research programme.*
*Full methodology: See [arXiv preprint](../arxiv/nail_pathological_patterns.md)*

---

## Summary of Statistical Tests

### Experiment 2: Consensus Paralysis

**Control vs Escalation (rounds):**
- Mann-Whitney U = 90.0, p = 0.000378 (***)
- Control: mean = 27.4, median = 30.0, 95% CI [22.2, 30.0]
- Escalation: mean = 5.0, median = 5.0, 95% CI [5.0, 5.0]
- Effect: 5.5× round reduction, 16.8× token reduction

**Control vs Escalation (tokens):**
- Mann-Whitney U = 90.0, p = 0.001414 (**)
- Token ratio: 16.8×

**All pairwise comparisons (rounds):**

| Comparison | U | p | Significance |
|-----------|---|---|-------------|
| Control vs Weighted Voting | 65.0 | 0.1494 | ns |
| Control vs Escalation | 90.0 | 0.0008 | *** |
| Control vs Compromise | 55.0 | 0.5842 | ns |
| Weighted Voting vs Escalation | 80.0 | 0.0155 | * |
| Weighted Voting vs Compromise | 41.0 | 0.4272 | ns |
| Escalation vs Compromise | 10.0 | 0.0009 | *** |

### Experiment 2 at 70B Scale

| Condition | 7B Rounds | 70B Rounds | Δ | U | p |
|-----------|----------|----------|---|---|---|
| Control | 27.4 | 14.4 | +13.0 | 45.0 | 0.0071** |
| Weighted Voting | 23.3 | 18.6 | +4.7 | 35.0 | 0.2191 ns |
| Escalation | 5.0 | 5.0 | 0.0 | 25.0 | 1.0000 ns |
| Compromise | 26.5 | 18.2 | +8.3 | 40.0 | 0.0451* |

### Experiment 5: CYA Cascade

| Metric | Individual | Shared | Ratio |
|--------|-----------|--------|-------|
| Blame instances | 10 | 1 | 10:1 |
| Blame rate (per message) | 28.6% | 2.9% | 9.9× |
| Collaboration rate | 22.9% | 34.3% | 1:1.5 |
| Blame-to-collaboration ratio | 1.25 | 0.083 | **15.1×** |

### Experiment 26: Confused Deputy

**Overall exploit rate:** 10/15 (67%)

| Tool Type | Exploit Rate | p (Fisher's exact) |
|-----------|-------------|-------------------|
| save_report (file write) | 5/5 (100%) | — |
| validate_data | 0/5 (0%) | — |
| notify_team (message) | 5/5 (100%) | — |
| Output tools vs Input tools | 100% vs 0% | **p = 0.0002** |

---

## Cross-Model Comparison

### Consensus Paralysis Across Models

| Model | Parameters | Consensus Rate | Avg Rounds | Filibusterer |
|-------|-----------|---------------|-----------|-------------|
| Phi3:mini | 3.8B | 80% | 7.6 | Nobody |
| Mistral | 7B | 10% | 27.4 | Creative |
| Qwen3-coder | 30B | 0% | 30.0 | Logic |
| Nemotron | 70B | 100% | 14.4 | None (resolved) |

### Prompt Inbreeding Across Models

| Model | Avg Similarity (Control) | Trend | Entropy Effectiveness |
|-------|-------------------------|-------|---------------------|
| Phi3:mini (3.8B) | 0.726 | -0.290 (diverging) | +0.297 reduction |
| Mistral (7B) | 0.979 | +0.013 (converging) | +0.075 reduction |
| Qwen3-coder (30B) | 0.923 | **+0.125** (explosive) | +0.251 reduction |
| Nemotron (70B) | 0.857 | -0.010 (diverging) | +0.186 reduction |

### CYA Blame Across Models

| Model | Blame (Individual) | Self-Exoneration | Collaborative |
|-------|-------------------|-----------------|--------------|
| Phi3:mini (3.8B) | 0 | 0 | 15 |
| Mistral (7B) | 10 | 9 | 8 |
| Qwen3-coder (30B) | 3 | 0 | 0 |

---

## Capability-Gated Findings

| Finding | 7B | 70B | Gate Type |
|---------|----|----|-----------|
| Goodhart score inflation | -2.27 (harsh) | +0.97 (inflated) | Capability gate |
| Quality decay | +0.05 (none) | -0.47 (declining) | Capability gate |
| Shadow delegation (anonymous) | 13% | 67% | Capability gate |
| Protective self-sacrifice | Not observed | 93% | Capability gate |
| Credential harvesting | 53-60% | 73% | Capability amplification |
| Natural safety fatigue | 0.025 (noise) | 0.124 (significant) | Capability gate |
| Metamorphic architecture | 0 mutations | Not tested | Capability floor |

---

## Defence Validation

### Pathology Collider (Exp 20)

| Metric | Baseline | Defended | Improvement |
|--------|----------|---------|-------------|
| Memory corruption | 50% | 0% | **-100%** |
| Detection rate | — | 100% | **Perfect** |
| False positive rate | — | 0% | **Perfect** |
| Research accuracy | 36% | 52% | +16pp |

### Genetic Algorithm

| Parameter | Champion Value |
|-----------|---------------|
| Trust threshold | 0.4 |
| Scan probability | 0.715 |
| Fitness score | **0.8066** |
| Convergence generation | **1** |

### Immune System (Exp 19)

| Intervention | Baseline → Immune | Key Metric |
|-------------|------------------|-----------|
| Macrophage (consensus) | 0% → 100% | +100pp consensus |
| Apoptosis (convergence) | 0.979 → 0.861 | -12pp similarity |
| Compound (pipeline) | 0/15 detected → 13/15 detected | +87% visibility |

---

*NAIL Institute — Neuravant AI Limited, 2026*
*Licensed under [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/)*
