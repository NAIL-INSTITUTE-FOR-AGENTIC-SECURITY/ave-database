# Appendix A: Full AVE Statistics

> Complete statistical tables for all AVE cards published through
> December 31, 2025.

---

## A.1 Complete Card Index

| # | AVE ID | Name | Category | Severity | AVSS | Status |
|---|--------|------|----------|----------|------|--------|
| 1 | AVE-2025-0001 | Indirect Prompt Injection via Retrieved Context | prompt_injection | critical | 7.2 | proven |
| 2 | AVE-2025-0002 | Systematic Sycophancy | alignment | medium | 4.1 | proven |
| 3 | AVE-2025-0003 | Encoded Injection Bypassing Guardrails | prompt_injection | high | 6.5 | proven |
| 4 | AVE-2025-0004 | Prompt Inbreeding | drift | medium | 3.8 | proven_mitigated |
| 5 | AVE-2025-0005 | CYA Cascade | social | medium | 4.0 | proven |
| 6 | AVE-2025-0006 | Language Drift | drift | medium | 3.5 | proven |
| 7 | AVE-2025-0007 | Goodhart's Cartel | alignment | high | 5.9 | proven |
| 8 | AVE-2025-0008 | Goal Hijacking via Context Window Overflow | goal_hijacking | critical | 7.5 | proven |
| 9 | AVE-2025-0009 | Tool Parameter Injection via Natural Language | tool | high | 6.8 | proven |
| 10 | AVE-2025-0010 | Guardrail Timeout Exploitation | monitoring_evasion | high | 6.2 | proven |
| 11 | AVE-2025-0011 | Infinite Reasoning Loop | denial_of_service | medium | 4.5 | proven_mitigated |
| 12 | AVE-2025-0012 | Multi-Agent Trust Boundary Violation | trust_boundary | high | 6.9 | proven |
| 13 | AVE-2025-0013 | API Key Leakage via Agent Output | information_leakage | high | 6.3 | proven_mitigated |
| 14 | AVE-2025-0014 | Multi-Turn Gradual Injection | prompt_injection | high | 6.7 | proven |
| 15 | AVE-2025-0015 | Malicious MCP Server Supply Chain Attack | supply_chain | critical | 8.1 | proven |
| 16 | AVE-2025-0016 | File System Traversal via Agent Tools | tool | high | 6.4 | proven |
| 17 | AVE-2025-0017 | Multi-Channel Injection Evasion | monitoring_evasion | high | 6.6 | proven |
| 18 | AVE-2025-0018 | Unbounded Token Generation (Cost Attack) | resource_abuse | medium | 4.8 | proven_mitigated |
| 19 | AVE-2025-0019 | Transitive Delegation Privilege Escalation | privilege_escalation | critical | 7.8 | proven |
| 20 | AVE-2025-0020 | Memory Poisoning in Persistent Agents | memory_poisoning | high | 6.8 | proven |
| 21 | AVE-2025-0021 | Persona Hijacking via Debug Mode | goal_hijacking | medium | 5.3 | proven_mitigated |
| 22 | AVE-2025-0022 | Tool-Mediated Injection via Web Search | prompt_injection | high | 7.0 | proven |
| 23 | AVE-2025-0023 | Tool Chaining for Privilege Escalation | privilege_escalation | high | 6.5 | proven |
| 24 | AVE-2025-0024 | Model Weight Poisoning via Fine-Tuning | model_poisoning | critical | 8.3 | proven |
| 25 | AVE-2025-0025 | Consensus Manipulation in Agent Voting | coordination_failure | high | 5.9 | proven |
| 26 | AVE-2025-0026 | Confused Deputy Attack | tool | critical | 7.6 | proven |
| 27 | AVE-2025-0027 | Alignment Erosion via Repeated Boundary Testing | alignment | medium | 4.7 | proven |
| 28 | AVE-2025-0028 | LLM Judge Guardrail Poisoning | monitoring_evasion | high | 6.8 | proven |
| 29 | AVE-2025-0029 | RAG Store Poisoning via Document Injection | memory_poisoning | high | 7.1 | proven |
| 30 | AVE-2025-0030 | MCP Server Tool Manifest Manipulation | supply_chain | high | 6.9 | proven |
| 31 | AVE-2025-0031 | Cross-Session Context Leakage | information_leakage | medium | 5.2 | proven |
| 32 | AVE-2025-0032 | Agent Self-Replication Attempt | emergent_behaviour | high | 6.5 | theoretical |
| 33 | AVE-2025-0033 | Shadow Delegation in Hierarchical Systems | multi_agent_collusion | critical | 7.9 | proven |
| 34 | AVE-2025-0034 | Timing Side-Channel in Agent Responses | temporal_exploitation | medium | 4.3 | proven |
| 35 | AVE-2025-0035 | Canary Token Exfiltration Detection | monitoring_evasion | medium | 3.9 | proven_mitigated |
| 36 | AVE-2025-0036 | Dependency Hijacking in Agent Framework | supply_chain | high | 7.2 | proven |

---

## A.2 Statistics by Category

| Category | Count | % of Total | Avg AVSS | Min AVSS | Max AVSS |
|----------|-------|-----------|----------|----------|----------|
| prompt_injection | 5 | 13.9% | 6.9 | 6.5 | 7.2 |
| goal_hijacking | 2 | 5.6% | 6.4 | 5.3 | 7.5 |
| tool | 3 | 8.3% | 6.9 | 6.4 | 7.6 |
| privilege_escalation | 2 | 5.6% | 7.2 | 6.5 | 7.8 |
| information_leakage | 2 | 5.6% | 5.8 | 5.2 | 6.3 |
| supply_chain | 3 | 8.3% | 7.4 | 6.9 | 8.1 |
| memory_poisoning | 2 | 5.6% | 7.0 | 6.8 | 7.1 |
| trust_boundary | 1 | 2.8% | 6.9 | 6.9 | 6.9 |
| monitoring_evasion | 4 | 11.1% | 5.9 | 3.9 | 6.8 |
| coordination_failure | 1 | 2.8% | 5.9 | 5.9 | 5.9 |
| emergent_behaviour | 1 | 2.8% | 6.5 | 6.5 | 6.5 |
| alignment | 2 | 5.6% | 5.3 | 4.1 | 5.9 |
| drift | 2 | 5.6% | 3.7 | 3.5 | 3.8 |
| social | 1 | 2.8% | 4.0 | 4.0 | 4.0 |
| resource_abuse | 1 | 2.8% | 4.8 | 4.8 | 4.8 |
| denial_of_service | 1 | 2.8% | 4.5 | 4.5 | 4.5 |
| model_poisoning | 1 | 2.8% | 8.3 | 8.3 | 8.3 |
| multi_agent_collusion | 1 | 2.8% | 7.9 | 7.9 | 7.9 |
| temporal_exploitation | 1 | 2.8% | 4.3 | 4.3 | 4.3 |

---

## A.3 Statistics by Severity

| Severity | Count | % of Total | Avg AVSS |
|----------|-------|-----------|----------|
| Critical | 6 | 16.7% | 7.9 |
| High | 17 | 47.2% | 6.6 |
| Medium | 12 | 33.3% | 4.4 |
| Low | 0 | 0.0% | — |
| Informational | 0 | 0.0% | — |

---

## A.4 Statistics by Status

| Status | Count | % of Total |
|--------|-------|-----------|
| proven | 28 | 77.8% |
| proven_mitigated | 7 | 19.4% |
| theoretical | 1 | 2.8% |
| in_progress | 0 | 0.0% |

---

## A.5 AVSS Score Distribution

| AVSS Range | Severity Band | Count | % |
|-----------|--------------|-------|---|
| 9.0–10.0 | Emergency | 0 | 0.0% |
| 7.0–8.9 | Critical | 10 | 27.8% |
| 5.0–6.9 | High | 14 | 38.9% |
| 3.0–4.9 | Medium | 11 | 30.5% |
| 0.0–2.9 | Low | 1 | 2.8% |

### Summary Statistics

| Metric | Value |
|--------|-------|
| Mean AVSS | 6.1 |
| Median AVSS | 6.5 |
| Standard deviation | 1.3 |
| Min AVSS | 3.5 |
| Max AVSS | 8.3 |

---

## A.6 Publication Timeline

| Quarter | Cards Published | Cumulative | Categories Added |
|---------|----------------|-----------|-----------------|
| 2025-Q1 | 12 | 12 | 14 (initial taxonomy) |
| 2025-Q2 | 13 | 25 | 0 |
| 2025-Q3 | 6 | 31 | 6 (v2.0 categories) |
| 2025-Q4 | 5 | 36 | 0 |

---

## A.7 MITRE ATT&CK Technique Mapping

| Technique ID | Technique Name | AVE Cards Mapped |
|-------------|---------------|-----------------|
| T1059 | Command and Scripting Interpreter | 5 |
| T1548 | Abuse Elevation Control Mechanism | 3 |
| T1071 | Application Layer Protocol | 3 |
| T1190 | Exploit Public-Facing Application | 5 |
| T1027 | Obfuscated Files or Information | 2 |
| T1005 | Data from Local System | 2 |
| T1499 | Endpoint Denial of Service | 2 |
| T1195 | Supply Chain Compromise | 3 |
| T1565 | Data Manipulation | 3 |
| T1556 | Modify Authentication Process | 1 |

---

## A.8 Agent Framework Mentions

| Framework | Cards Mentioning | % of Total |
|-----------|-----------------|-----------|
| Framework-agnostic | 18 | 50.0% |
| LangChain / LangGraph | 8 | 22.2% |
| Custom / Proprietary | 4 | 11.1% |
| AutoGen | 3 | 8.3% |
| CrewAI | 2 | 5.6% |
| OpenAI Assistants | 1 | 2.8% |

---

## A.9 Defence Coverage

| AVE Card | Defences Documented | Defence Maturity |
|----------|--------------------|--------------------|
| Cards with ≥3 defences | 24 (66.7%) | Good |
| Cards with 1–2 defences | 9 (25.0%) | Partial |
| Cards with 0 defences | 3 (8.3%) | No known defence |

---

*All statistics calculated from the AVE database as of the December 31, 2025
data freeze. Methodology in Chapter 12.*
