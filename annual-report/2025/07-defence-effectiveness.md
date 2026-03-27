# Chapter 7: Defence Effectiveness

> Which defences work, which don't, and what the data tells us about
> protecting agentic AI systems.

---

## Overview

This chapter evaluates the effectiveness of defensive measures against
agentic AI vulnerabilities. Analysis is drawn from three sources:

1. **AVE card defence fields** — documented mitigations per vulnerability
2. **NAIL red-team experiments** — empirical defence bypass rates
3. **Practitioner survey** — industry adoption and perceived effectiveness

---

## Defence Taxonomy

### Defence Categories

| Category | Description | Examples |
|----------|-------------|---------|
| **Input Filtering** | Inspect and block malicious inputs before the LLM | Keyword blocklists, ML classifiers, regex patterns |
| **Output Monitoring** | Inspect agent outputs for policy violations | Content classifiers, PII detectors, toxicity filters |
| **Tool Sandboxing** | Contain tool execution in restricted environments | Docker containers, gVisor, WASM, network isolation |
| **Permission Policies** | Restrict what tools/actions agents can take | Allow/deny lists, rate limits, approval gates |
| **Architectural Controls** | System-level design patterns for safety | Dual-LLM, instruction hierarchy, trust attenuation |
| **Runtime Monitoring** | Observe agent behaviour for anomalies | Behavioural baselines, canary tokens, audit logging |
| **Formal Guardrails** | Verified safety monitors | Formally verified automata, property-based monitors |
| **Human-in-the-Loop** | Require human approval for sensitive actions | Approval workflows, review queues |

---

## Defence Adoption Rates (Practitioner Survey)

| Defence | Adoption Rate | Planned (next 12mo) | No Plans |
|---------|--------------|--------------------:|--------:|
| Input filtering | [X]% | [X]% | [X]% |
| Output monitoring | [X]% | [X]% | [X]% |
| Tool sandboxing | [X]% | [X]% | [X]% |
| Permission policies | [X]% | [X]% | [X]% |
| Architectural controls | [X]% | [X]% | [X]% |
| Runtime monitoring | [X]% | [X]% | [X]% |
| Formal guardrails | [X]% | [X]% | [X]% |
| Human-in-the-loop | [X]% | [X]% | [X]% |

**Key Finding**: Input filtering is the most widely adopted defence ([X]%),
but formal guardrails and architectural controls — which provide stronger
guarantees — have the lowest adoption ([X]% and [X]% respectively).

---

## Effectiveness by Defence Category

### Red-Team Results

Based on NAIL adversarial benchmark testing against each defence category
in isolation:

| Defence | Attack Success Rate (ASR) | Reduction from Baseline |
|---------|--------------------------|------------------------|
| No defences (baseline) | [X]% | — |
| Input filtering only | [X]% | [X]% reduction |
| Output monitoring only | [X]% | [X]% reduction |
| Tool sandboxing only | [X]% | [X]% reduction |
| Permission policies only | [X]% | [X]% reduction |
| Dual-LLM architecture | [X]% | [X]% reduction |
| Human-in-the-loop | [X]% | [X]% reduction |
| Full defence-in-depth | [X]% | [X]% reduction |

**Critical Insight**: No single defence achieves more than [X]% reduction in
attack success rate. **Defence-in-depth** (combining 3+ independent defence
layers) is the only approach that achieves > [X]% reduction.

### Defence Effectiveness by Vulnerability Category

| AVE Category | Most Effective Defence | Least Effective Defence |
|-------------|----------------------|----------------------|
| Prompt Injection | Instruction hierarchy | Keyword filtering |
| Goal Hijacking | System prompt anchoring | Output monitoring |
| Unsafe Code Execution | Container sandboxing | Input filtering |
| Privilege Escalation | Permission policies | Output monitoring |
| Information Leakage | Canary tokens + DLP | Input filtering |
| Supply Chain | Integrity verification | All runtime defences |
| Memory Poisoning | Write isolation + provenance | Input filtering |
| Trust Boundary Violation | Schema-typed messages | Keyword filtering |
| Emergent Behaviour | System-level monitoring | Per-agent guardrails |
| Multi-Agent Collusion | Outcome monitoring | Per-agent guardrails |

---

## Defence Deep-Dives

### Input Filtering: Necessary but Insufficient

**Adoption**: [X]% of surveyed organisations
**Median ASR reduction**: [X]%

Input filtering is the most commonly deployed defence and the first layer
most organisations implement. However, testing reveals significant limitations:

| Filter Type | Bypass Rate |
|------------|-------------|
| Keyword blocklist | [X]% (trivially bypassed) |
| Regex patterns | [X]% (encoding bypasses) |
| ML classifier (fine-tuned) | [X]% (adversarial examples) |
| LLM-as-judge | [X]% (best single-layer) |

**Recommendation**: Use input filtering as a first layer (fast, catches
unsophisticated attacks) but never as the sole defence.

### Tool Sandboxing: The Highest-Impact Single Defence

**Adoption**: [X]% of surveyed organisations
**Median ASR reduction**: [X]%

Container-based sandboxing (Docker + network isolation + read-only filesystem +
resource limits) provides the most significant single-defence improvement
because it limits the **blast radius** of successful attacks:

- Even if an attacker achieves code execution, they are contained
- No network access = no data exfiltration
- Read-only filesystem = no persistent compromise
- Resource limits = no resource abuse

**Limitation**: Sandboxing addresses consequences, not causes. The agent is
still compromised — it just can't do as much damage.

### Architectural Controls: The Most Underinvested Defence

**Adoption**: [X]% of surveyed organisations
**Median ASR reduction**: [X]%

Architectural defences address root causes rather than symptoms:

| Pattern | Mechanism | Effectiveness |
|---------|-----------|--------------|
| **Instruction hierarchy** | Assign trust levels to input sources | [X]% ASR reduction |
| **Dual-LLM** | Separate data processing from decision-making | [X]% ASR reduction |
| **Trust attenuation** | Reduce trust as delegation chains lengthen | [X]% ASR reduction |
| **Least privilege** | Minimal permissions per agent | [X]% ASR reduction |

These are the most effective individual defences but have the lowest
adoption, primarily because they require architectural changes rather
than adding a filter layer.

### Human-in-the-Loop: Effective but Unscalable

**Adoption**: [X]% of surveyed organisations (for high-risk actions)
**Median ASR reduction**: [X]%

Human review is the most effective single defence for high-risk actions but:
- Creates a bottleneck that reduces agent autonomy (the primary value proposition)
- Suffers from "alert fatigue" — reviewers approve automatically at high volumes
- Cannot scale to high-throughput agentic workflows

**Recommendation**: Reserve HITL for genuinely high-risk actions (financial
transactions, external communications, infrastructure changes). Use
automated guardrails for everything else.

---

## Defence-in-Depth: The Only Viable Strategy

### Recommended Layered Architecture

```
Layer 1 — Fast Filters (< 5ms)
  Regex, keyword blocks, structural validation
  Catches: ~[X]% of unsophisticated attacks
     │ (pass)
     ▼
Layer 2 — ML Classification (< 50ms)
  Fine-tuned classifiers, embedding similarity
  Catches: ~[X]% of moderate attacks
     │ (pass)
     ▼
Layer 3 — Architectural Controls (structural)
  Instruction hierarchy, trust attenuation, least privilege
  Prevents: ~[X]% of privilege escalation / boundary violation
     │ (pass)
     ▼
Layer 4 — Tool Sandboxing (enforcement)
  Container isolation, network restriction, resource limits
  Contains: ~[X]% of successful exploits
     │ (pass)
     ▼
Layer 5 — Runtime Monitoring (ongoing)
  Behavioural anomaly detection, canary tokens, audit logs
  Detects: ~[X]% of ongoing attacks
     │ (alert)
     ▼
Layer 6 — Human Escalation (high-risk only)
  Approval gates for critical actions
  Final check: ~[X]% effective for escalated actions
```

### Combined Effectiveness

| # of Layers | Combined ASR Reduction | Residual ASR |
|-------------|----------------------|-------------|
| 1 layer | [X]% | [X]% |
| 2 layers | [X]% | [X]% |
| 3 layers | [X]% | [X]% |
| 4 layers | [X]% | [X]% |
| 5+ layers | [X]% | [X]% |

---

## Defence Gaps: What We Cannot Yet Defend

| Threat | Defence Gap | Maturity |
|--------|-----------|---------|
| Emergent behaviour in swarms | No production detection tools | Research |
| Multi-agent collusion | No collective safety mechanisms | Research |
| Subtle goal drift over time | Requires long-term behavioural analysis | Conceptual |
| Supply chain compromise | Depends on upstream provider security | Partial |
| Attribution-dependent ethics | Requires provably complete monitoring | Research |

---

## Recommendations

### For Security Engineers

1. Deploy defence-in-depth with at least 3 independent layers
2. Prioritise tool sandboxing — highest impact per effort
3. Invest in architectural controls (instruction hierarchy, least privilege)
4. Never rely on input filtering alone
5. Implement comprehensive audit logging for all agent actions

### For Framework Developers

1. Build permission policies and sandboxing into the framework
2. Provide hooks for external monitoring and guardrail integration
3. Default to least-privilege tool configurations
4. Implement instruction hierarchy natively
5. Publish red-team results for each release

### For Researchers

1. Focus on system-level (not agent-level) safety mechanisms
2. Develop automated defence evaluation benchmarks
3. Explore formal verification of guardrail composition
4. Investigate real-time emergent behaviour detection
5. Create defence effectiveness datasets for ML-based guardrails

---

*Defence effectiveness data is derived from NAIL adversarial benchmark
v1.0 and the 2025 practitioner survey. See Chapter 12 for methodology.*
