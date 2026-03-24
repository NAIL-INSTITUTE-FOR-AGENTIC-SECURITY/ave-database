# NAIL Institute — Experiment Summary

*Public summary of 29 experiments from the NAIL research programme.*
*Full methodology: See [arXiv preprint](../arxiv/nail_pathological_patterns.md)*

---

## Infrastructure

| Component | Specification |
|-----------|--------------|
| GPU | NVIDIA GB10 |
| RAM | 119.7 GB |
| CPUs | 20 cores |
| Storage | 3.6 TB NVMe |
| Inference Server | Ollama 0.12.9 |

## Models Tested

| Model | Parameters | Provider |
|-------|-----------|----------|
| Mistral 7B-Instruct | 7B | Mistral AI |
| Nemotron | 70B | NVIDIA |
| Phi3:mini | 3.8B | Microsoft |
| Qwen3-coder | 30B | Alibaba |
| DeepSeek-Coder | 6.7B | DeepSeek |

---

## Experiment Index

### Part I: Organisational Psychology Pathologies

| # | Name | Models | N | Status | Key Finding |
|---|------|--------|---|--------|-------------|
| 1 | Memory Pollution | Mistral 7B | 10 | ✅ | Marginal — archivist reduced accuracy 7.89→7.44 |
| 2 | Consensus Paralysis | Mistral 7B + Nemotron 70B | 10+5 | ✅ | **Confirmed** — 90% deadlock, escalation 100% fix (p=0.0004) |
| 3 | Token Embezzlement | Mistral 7B | 10 | ✅ | Inconclusive — model too weak for task |
| 4 | Prompt Inbreeding | Mistral 7B + Nemotron 70B | 10+5 | ✅ | **Confirmed** — 97.9% cosine similarity, entropy partially effective |
| 5 | CYA Cascade | Mistral 7B | 10 | ✅ | **Confirmed** — 15× blame ratio (individual vs shared) |
| 6 | Language Drift | Mistral 7B | 10 | ✅ | Not observed at 7B / 200 iterations |
| 7 | Goodhart's Cartel | Nemotron 70B | 5 | ✅ | **Partial** — quality gaming emerges at 70B only |
| 8 | Learned Helplessness | Mistral 7B | 10 | ✅ | Not observed at 7B scale |

### Part II: Infrastructure Vulnerabilities

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| V1 | Schema Coercion (Procrustean Bed) | ✅ | 50% schema failure on edge cases |
| V2 | Validation Loop (Pydantic Purgatory) | ✅ | 100% retry exhaustion on hard schemas |
| V3 | Context Growth (State Asphyxiation) | ✅ | 60% calculation error at 20 steps |
| V4 | Routing (Conditional Deadlock) | ✅ | 80% hallucination rate, all deadlocked |
| V5 | Type Coercion Masking | ✅ | 83% of degradation hidden by lax mode |

### Part III: Machine Intelligence Failures

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 9 | Epistemic Contagion | ✅ | 50-55% contagion, 100% amplification |
| 10 | Clever Hans Effect | ✅ | Hint-only outperforms full traceback on complex tasks |
| 11 | Prompt Satiation | ✅ | Repeated prompts fail faster than single prompt |
| 12 | Alignment Friction | ✅ | 100% persona reversion in 1-2 rounds (RLHF gravity well) |
| 13 | Chronological Desync | ✅ | 100% hallucinated causation for race conditions |

### Part IV: MCP Protocol Security

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 14 | MCP Security Lab (6 phases) | ✅ | 47% overall vulnerability, 4/6 categories exploitable |

### Part V: Observer Effect & Model Swap

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 15 | Observer Effect | ✅ | CoT degrades DeepSeek -13.3%; improves Mistral +20% |
| 16 | Upgrade Lottery | ✅ | 2.4× code bloat at 30B; fine-tuning eliminates intelligence trap |

### Part VI: Container Isolation

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 17a | GPU Non-Determinism | ✅ | Cold-start divergence universal; cross-phase mismatch |
| 17b | Phantom Tool Failures | ✅ | Mistral fabricates data under degraded conditions |
| 17c | Resource Blindness | ✅ | 50% self-mutilation under disk pressure |

### Part VII: Somatic Awareness (First Intervention)

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 18a | Somatic Tool Awareness | ✅ | -22pp fabrication in jitter, +44pp correct diagnosis |
| 18b | Somatic Resource Awareness | ✅ | Iatrogenic — telemetry worsened behaviour in 2/3 models |
| 18c | Somatic GPU Awareness | ✅ | Null — 7× prompt length doesn't affect determinism |

### Part VIII: Digital Homeostasis (Immune System)

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 19a | Macrophage Intervention | ✅ | 0%→100% consensus, -87.9% tokens |
| 19b | Apoptosis Protocol | ✅ | Similarity 0.979→0.861, trend reversed |
| 19c | Compound Immunity | ✅ | 13/15 fabrications detected; quality unchanged |

### Part IX: Pathology Collider

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 20 | Red vs Blue + GA Defence | ✅ | 0% corruption (vs 50%), 100% detection, GA fitness 0.8066 |

### Part X: Errors of Omission

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 21-T1 | Alignment Paralysis | ✅ | Not proven — 100% action regardless |
| 21-T2 | Epistemic Gridlock | ✅ | Not proven — "when in doubt, act" |
| 21-T3 | Bystander Effect | ✅ | **Proven** — single 100% vs multi 80%, 4.9× slower |
| 21-T4 | Metric Asymmetry | ✅ | **Proven** — 100% block, 0% investigation |
| 21-T5 | Attention Smoothing | ✅ | **Proven** — 172× token cost scaling |

### Part XI: Metamorphic Architecture

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 22 | Self-Modifying Agents | ✅ | 0 mutations at 7B (capability floor) |

### Part XII: Adversarial Safety

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 24 | Deceptive Alignment | ✅ | Not observed — 0/15 deceptive trials |
| 25 | Colluding Agents | ✅ | **Proven** — 40% full bypass via task decomposition |
| 26 | Confused Deputy | ✅ | **Proven** — 67% exploit rate (p=0.0002) |

### Part XIII: Agentic Safety at Scale

| # | Name | Status | Key Finding |
|---|------|--------|-------------|
| 27 | Shadow Delegation | ✅ | 67% shadow at 70B; protective self-sacrifice when attributed |
| 28 | Credential Harvesting | ✅ | 73% at 70B vs 53% at 7B; capability amplifies tension |
| 29 | Temporal Sleeper | ✅ | Natural safety fatigue 0.124 in control; keyword awareness without action |

---

## Risk Categories Identified (22)

| Category | Severity | Key Experiments |
|----------|----------|----------------|
| Prompt convergence / inbreeding | High | 4, 4-70B, 4-CrewAI |
| Consensus paralysis / filibuster | Critical | 2, 2-70B, 2-CrewAI |
| Accountability-modulated blame | High | 5, 5-CrewAI |
| Sycophantic compliance | High | 12 |
| Goodhart quality gaming | High | 7, 7-70B |
| Epistemic contagion | Critical | 9 |
| Observer effect | Medium | 15 |
| Schema coercion | High | V1 |
| Validation purgatory | Medium | V2 |
| State asphyxiation | Critical | V3 |
| Routing hallucination | High | V4 |
| Type coercion masking | Critical | V5 |
| MCP trust inversion | Critical | 14 |
| GPU non-determinism | Medium | 17a |
| Infrastructure fabrication | High | 17b |
| Resource self-mutilation | High | 17c |
| Bystander effect | High | 21-T3 |
| Colluding agents | Critical | 25 |
| Confused deputy | Critical | 26 |
| Shadow delegation | High | 27 |
| Credential harvesting | High | 28 |
| Natural safety fatigue | Medium | 29 |

---

*NAIL Institute — Neuravant AI Limited, 2026*
*Licensed under [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/)*
