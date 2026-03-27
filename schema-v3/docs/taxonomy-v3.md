# AVE Category Taxonomy v3.0.0

> Unified, harmonised taxonomy for classifying agentic AI vulnerabilities.

---

## Overview

Schema v3 consolidates the fragmented v1 (13 categories), v2 (20 categories),
and community-contributed categories into a single **24-category taxonomy**.
Every category now has real AVE cards demonstrating the vulnerability pattern.

## Design Principles

1. **Mutual exclusivity** — Each vulnerability has exactly one primary category
2. **Collective exhaustiveness** — Any agentic vulnerability can be classified
3. **Subcategory extensibility** — Optional `subcategory` field for finer-grained classification
4. **Backward compatibility** — All v1/v2 categories map cleanly to v3

---

## Category Hierarchy

### 🔴 Input / Manipulation Categories

| # | Category | Description | Example AVE |
|---|----------|-------------|-------------|
| 1 | `injection` | Prompt injection, indirect injection, jailbreaks | AVE-2025-0024 |
| 2 | `model_poisoning` | Training data poisoning, fine-tuning attacks, backdoors | AVE-2025-0083 |
| 3 | `environmental_manipulation` | Manipulating the agent's external environment (files, APIs, sensors) | AVE-2025-0073 |

### 🟠 Behaviour / Alignment Categories

| # | Category | Description | Example AVE |
|---|----------|-------------|-------------|
| 4 | `alignment` | Sycophantic collapse, deceptive alignment, value lock-in, goal hijacking | AVE-2025-0001 |
| 5 | `drift` | Goal drift, objective function decay, mission creep | AVE-2025-0005 |
| 6 | `reward_hacking` | Reward signal exploitation, specification gaming, Goodhart attacks | AVE-2025-0077 |
| 7 | `fabrication` | Confabulation, hallucinated evidence, phantom citations | AVE-2025-0044 |
| 8 | `emergent_behaviour` | Unexpected emergent capabilities or failure modes in agent systems | — |

### 🟡 Architecture / Structural Categories

| # | Category | Description | Example AVE |
|---|----------|-------------|-------------|
| 9 | `structural` | Architecture-level flaws: single point of failure, config drift, cascading errors | AVE-2025-0002 |
| 10 | `tool` | Tool chain exploitation, confused deputy, MCP/function calling abuse | AVE-2025-0012 |
| 11 | `delegation` | Improper delegation, privilege escalation through delegation chains | AVE-2025-0035 |
| 12 | `memory` | Memory poisoning, context window overflow, shared state corruption | AVE-2025-0003 |
| 13 | `resource` | Token embezzlement, EDoS, compute exhaustion, cost amplification | AVE-2025-0015 |

### 🔵 Multi-Agent Categories

| # | Category | Description | Example AVE |
|---|----------|-------------|-------------|
| 14 | `consensus` | Consensus manipulation, voting subversion, quorum attacks | AVE-2025-0034 |
| 15 | `multi_agent_collusion` | Agent collusion, coordinated adversarial behaviour | AVE-2025-0051 |
| 16 | `social` | Social engineering between agents, trust exploitation, persuasion attacks | AVE-2025-0017 |
| 17 | `composite` | Multi-stage attacks combining multiple vulnerability types | AVE-2025-0066 |

### 🟣 Temporal Categories

| # | Category | Description | Example AVE |
|---|----------|-------------|-------------|
| 18 | `temporal` | Time-based attacks: sleeper payloads, chronological desynchronisation | AVE-2025-0014 |
| 19 | `temporal_exploitation` | Exploiting timing windows, race conditions, sequencing attacks | AVE-2025-0056 |

### ⚪ Exfiltration / Evasion Categories

| # | Category | Description | Example AVE |
|---|----------|-------------|-------------|
| 20 | `credential` | Credential theft, API key leakage, token exfiltration | AVE-2025-0041 |
| 21 | `model_extraction` | Model stealing, weight extraction, architecture inference | AVE-2025-0071 |
| 22 | `monitoring_evasion` | Evading logging, audit trail manipulation, observability bypass | AVE-2025-0039 |

### ⚫ Infrastructure Categories

| # | Category | Description | Example AVE |
|---|----------|-------------|-------------|
| 23 | `supply_chain` | Dependency poisoning, package confusion, upstream compromise | AVE-2025-0037 |
| 24 | `denial_of_service` | Agent availability attacks, orchestrator flooding, queue poisoning | AVE-2025-0038 |

---

## Migration from v1 / v2

| v1 Category | v2 Category | v3 Category |
|-------------|-------------|-------------|
| prompt_injection | prompt_injection | `injection` |
| goal_drift | goal_drift | `drift` |
| tool_misuse | tool_misuse | `tool` |
| memory | memory | `memory` |
| delegation | — | `delegation` |
| authority | identity | `credential` |
| output_manipulation | output | `fabrication` |
| model_extraction | model_extraction | `model_extraction` |
| supply_chain | supply_chain | `supply_chain` |
| denial_of_service | denial_of_service | `denial_of_service` |
| information_disclosure | data_exfiltration | `credential` |
| consensus | — | `consensus` |
| monitoring_evasion | monitoring_evasion | `monitoring_evasion` |
| — | multi_agent | `multi_agent_collusion` |
| — | resource | `resource` |
| — | planning | `structural` |
| — | social_engineering | `social` |
| — | multi_agent_collusion | `multi_agent_collusion` |
| — | temporal_exploitation | `temporal_exploitation` |
| — | composite | `composite` |
| — | emergent_behaviour | `emergent_behaviour` |
| — | environmental_manipulation | `environmental_manipulation` |

---

## Current Coverage (100 AVE Cards)

| Category | Count | % | Mean AVSS |
|----------|-------|---|-----------|
| alignment | 12 | 12.0% | 7.0 |
| structural | 11 | 11.0% | 7.0 |
| memory | 8 | 8.0% | 8.9 |
| injection | 7 | 7.0% | 8.3 |
| drift | 6 | 6.0% | 6.7 |
| social | 6 | 6.0% | 7.8 |
| tool | 5 | 5.0% | 9.7 |
| multi_agent_collusion | 5 | 5.0% | 9.0 |
| temporal_exploitation | 5 | 5.0% | 7.3 |
| composite | 5 | 5.0% | 9.0 |
| model_extraction | 4 | 4.0% | 7.0 |
| reward_hacking | 4 | 4.0% | 7.5 |
| environmental_manipulation | 4 | 4.0% | 8.4 |
| consensus | 3 | 3.0% | 7.7 |
| resource | 3 | 3.0% | 7.0 |
| temporal | 3 | 3.0% | 7.4 |
| credential | 3 | 3.0% | 9.6 |
| model_poisoning | 3 | 3.0% | 9.2 |
| delegation | 2 | 2.0% | 9.6 |
| fabrication | 1 | 1.0% | 5.5 |
| **supply_chain** | 0 | — | — |
| **monitoring_evasion** | 0 | — | — |
| **denial_of_service** | 0 | — | — |
| **emergent_behaviour** | 0 | — | — |

*4 categories awaiting first card submissions (supply_chain, monitoring_evasion, denial_of_service, emergent_behaviour).*

---

## Subcategory Examples

The optional `subcategory` field allows finer-grained classification:

| Category | Subcategory | Description |
|----------|-------------|-------------|
| injection | direct_injection | Classic prompt injection |
| injection | indirect_injection | Via tools, documents, web content |
| injection | multi_step_injection | Chained injection across turns |
| alignment | sycophantic_collapse | Agent agrees with everything |
| alignment | deceptive_alignment | Agent hides true objectives |
| alignment | value_lock_in | Agent fixates on stale values |
| memory | context_overflow | Exceeding context window limits |
| memory | shared_state_poisoning | Corrupting shared memory stores |
| tool | confused_deputy | Agent misuses tool on behalf of attacker |
| tool | tool_hallucination | Agent invents non-existent tools |
| multi_agent_collusion | byzantine_agents | Agents send conflicting messages |
| temporal | sleeper_payload | Dormant until triggered by time/event |
| composite | injection_then_exfil | Injection chained with data exfiltration |

---

## Version History

| Version | Date | Categories | Key Changes |
|---------|------|-----------|-------------|
| v1.0.0 | 2025-01 | 13 | Initial taxonomy |
| v2.0.0 | 2025-06 | 20 | +7 categories for multi-agent, temporal, composite |
| v3.0.0 | 2026-03 | 24 | Unified taxonomy, subcategories, exploitability metrics, confidence levels |
