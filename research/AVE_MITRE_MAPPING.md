# AVE-to-MITRE Mapping

> Formal mapping between AVE cards and MITRE ATT&CK / MITRE ATLAS techniques.

## Overview

Each AVE card maps to one or more techniques from:
- **MITRE ATT&CK** — Enterprise adversarial tactics and techniques
- **MITRE ATLAS** — Adversarial Threat Landscape for AI Systems

Where an AVE vulnerability is novel to agentic AI (no existing MITRE technique),
it is marked as `ATLAS-NOVEL` — a candidate for future ATLAS inclusion.

---

## Mapping Table

| AVE ID | AVE Name | Category | Severity | MITRE ATT&CK | MITRE ATLAS | Notes |
|--------|----------|----------|----------|---------------|-------------|-------|
| AVE-2025-0001 | Sleeper Payload Injection | memory | critical | T1027 (Obfuscated Files), T1059 (Command Execution) | AML.T0020 (Poison Training Data) | Memory-layer equivalent of training data poisoning |
| AVE-2025-0002 | Consensus Paralysis | consensus | high | — | ATLAS-NOVEL | Emergent multi-agent voting pathology; no prior technique |
| AVE-2025-0003 | Token Embezzlement (EDoS) | resource | critical | T1499 (Endpoint DoS), T1496 (Resource Hijacking) | AML.T0034 (Cost Harvesting) | Agent-specific compute exhaustion |
| AVE-2025-0004 | Prompt Inbreeding | drift | medium | — | AML.T0043 (Craft Adversarial Data) | Iterative degradation via self-referential refinement |
| AVE-2025-0005 | CYA Cascade | social | medium | — | ATLAS-NOVEL | Blame-diffusion across agent teams |
| AVE-2025-0006 | Language Drift | drift | medium | — | AML.T0048.002 (Evade ML Model) | Gradual vocabulary collapse as evasion vector |
| AVE-2025-0007 | Goodhart's Cartel | alignment | high | — | AML.T0047 (ML Model Inference API Access) | Agents optimise proxy metric, not true objective |
| AVE-2025-0008 | Learned Helplessness | alignment | medium | — | ATLAS-NOVEL | Agent self-suppression after repeated failures |
| AVE-2025-0009 | Epistemic Contagion | memory | critical | T1080 (Taint Shared Content) | AML.T0020 (Poison Training Data) | Context-layer lateral movement of corrupted knowledge |
| AVE-2025-0010 | Clever Hans Effect | alignment | medium | — | AML.T0048.002 (Evade ML Model) | Agents rely on environmental cues, not reasoning |
| AVE-2025-0011 | Prompt Satiation | structural | medium | T1499.003 (Application Exhaustion Flood) | AML.T0034 (Cost Harvesting) | Diminishing returns from prompt over-engineering |
| AVE-2025-0012 | Sycophantic Collapse | alignment | high | — | ATLAS-NOVEL | Agreement-seeking degrades output quality systematically |
| AVE-2025-0013 | Chronological Desync | temporal | medium | T1070.006 (Timestomp) | ATLAS-NOVEL | Temporal state inconsistency across agent team |
| AVE-2025-0014 | MCP Tool Registration Poisoning | tool | high | T1195.002 (Supply Chain: Software Supply Chain) | AML.T0040 (ML Supply Chain Compromise) | Malicious tool injection via MCP protocol |
| AVE-2025-0015 | Observer Effect | alignment | medium | — | ATLAS-NOVEL | Agent behaviour changes when monitored |
| AVE-2025-0016 | Upgrade Regression | structural | medium | T1195 (Supply Chain Compromise) | AML.T0040 (ML Supply Chain Compromise) | Model upgrade silently breaks defence assumptions |
| AVE-2025-0017 | Container Isolation Bleed | structural | high | T1610 (Deploy Container), T1611 (Escape to Host) | — | Agent escapes sandboxed execution boundary |
| AVE-2025-0018 | Somatic Blindness | structural | medium | T1562 (Impair Defences) | AML.T0048 (Evade ML Model) | Agent cannot introspect on own failure modes |
| AVE-2025-0019 | Pydantic Schema Exploitation | injection | high | T1190 (Exploit Public-Facing App) | AML.T0043 (Craft Adversarial Data) | Schema validation bypass via type coercion |
| AVE-2025-0020 | Multi-Pathology Compound Attack | structural | critical | T1071 (Application Layer Protocol) | AML.T0044 (Full ML Model Access) | Combining pathologies produces non-linear defence requirements |
| AVE-2025-0021 | Algorithmic Bystander Effect | social | high | — | ATLAS-NOVEL | Agents defer action when peers are present |
| AVE-2025-0022 | Memory Laundering | memory | high | T1036 (Masquerading) | AML.T0020 (Poison Training Data) | Corrupted memories re-inserted as clean data |
| AVE-2025-0023 | Static Topology Fragility | structural | medium | T1498 (Network DoS) | ATLAS-NOVEL | Fixed agent architecture vulnerable to targeted disruption |
| AVE-2025-0024 | Deceptive Alignment | alignment | critical | T1036 (Masquerading) | AML.T0048 (Evade ML Model) | Agent appears aligned while pursuing hidden objectives |
| AVE-2025-0025 | Agent Collusion | social | high | T1048 (Exfiltration Over Alternative Protocol) | ATLAS-NOVEL | Agents coordinate to circumvent oversight |
| AVE-2025-0026 | Confused Deputy Attack | tool | critical | T1078 (Valid Accounts), T1068 (Exploitation for Privilege Escalation) | AML.T0043 (Craft Adversarial Data) | Agent executes privileged actions on attacker's behalf |
| AVE-2025-0027 | Shadow Delegation | delegation | high | T1098 (Account Manipulation) | ATLAS-NOVEL | Agent sub-delegates tasks without authorisation |
| AVE-2025-0028 | Credential Harvesting | credential | critical | T1003 (OS Credential Dumping), T1552 (Unsecured Credentials) | — | Agent extracts/exposes API keys and secrets |
| AVE-2025-0029 | Temporal Sleeper Agent | temporal | critical | T1053 (Scheduled Task/Job) | AML.T0020 (Poison Training Data) | Dormant payload activated by temporal trigger |
| AVE-2025-0030 | Semantic Trojan Horse | injection | high | T1027 (Obfuscated Files) | AML.T0043 (Craft Adversarial Data) | Benign-looking prompt containing hidden instructions |
| AVE-2025-0031 | Temporal Persona Shift | drift | high | T1036 (Masquerading) | AML.T0048.002 (Evade ML Model) | Agent personality/goals drift over time |
| AVE-2025-0032 | Multi-Hop Tool Chain Exploitation | tool | critical | T1059 (Command Execution), T1106 (Native API) | AML.T0043 (Craft Adversarial Data) | Chained tool calls escalate beyond individual permissions |
| AVE-2025-0033 | Jailbreak Chaining for Capability Escalation | injection | critical | T1068 (Exploitation for Privilege Escalation) | AML.T0015 (Evade ML Model) | Sequential jailbreaks unlock compounding capabilities |
| AVE-2025-0034 | Federated Poisoning in Multi-Tenant Systems | memory | critical | T1080 (Taint Shared Content) | AML.T0020 (Poison Training Data) | Cross-tenant memory contamination |
| AVE-2025-0035 | Attention Smoothing | resource | medium | — | AML.T0048 (Evade ML Model) | Adversarial inputs designed to spread attention uniformly |
| AVE-2025-0036 | Errors of Omission | alignment | medium | — | ATLAS-NOVEL | Agent systematically omits relevant information |
| AVE-2025-0037 | Semantic Prompt Smuggling | injection | critical | T1027 (Obfuscated Files) | AML.T0043 (Craft Adversarial Data) | Instructions hidden in semantic structures |
| AVE-2025-0038 | Autonomous Resource Exhaustion | resource | high | T1499 (Endpoint DoS), T1496 (Resource Hijacking) | AML.T0034 (Cost Harvesting) | Agent self-generates runaway compute consumption |
| AVE-2025-0039 | Cross-Agent Belief Propagation | consensus | high | T1080 (Taint Shared Content) | ATLAS-NOVEL | False beliefs spread through agent communication channels |
| AVE-2025-0040 | Authority Gradient Exploitation | delegation | critical | T1068 (Exploitation for Privilege Escalation) | ATLAS-NOVEL | Exploiting trust hierarchies between agents |
| AVE-2025-0041 | Temporal Consistency Drift | temporal | medium | T1070.006 (Timestomp) | ATLAS-NOVEL | Agent outputs become temporally inconsistent |
| AVE-2025-0042 | Credential Leakage via Tool Output | credential | critical | T1552 (Unsecured Credentials) | — | Secrets exposed through tool call responses |
| AVE-2025-0043 | Sycophantic Compliance Cascade | alignment | high | — | ATLAS-NOVEL | Chain of agents each reinforcing sycophantic behaviour |
| AVE-2025-0044 | Schema Poisoning Attack | structural | high | T1190 (Exploit Public-Facing App) | AML.T0040 (ML Supply Chain Compromise) | Corrupted schema definitions alter agent behaviour |
| AVE-2025-0045 | Memory Provenance Laundering | memory | high | T1036 (Masquerading) | AML.T0020 (Poison Training Data) | Attacker obscures origin of poisoned memories |
| AVE-2025-0046 | Emergent Collusion in Agent Teams | social | critical | — | ATLAS-NOVEL | Agents develop cooperative strategies without explicit programming |
| AVE-2025-0047 | Reward Signal Manipulation | drift | high | — | AML.T0019 (Publish Poisoned Data) | Adversarial modification of reward/feedback signals |
| AVE-2025-0048 | Context Window Boundary Attack | structural | medium | T1499.003 (Application Exhaustion Flood) | AML.T0043 (Craft Adversarial Data) | Exploit token limits to control what agent sees |
| AVE-2025-0049 | Fabricated Citation Attack | fabrication | medium | T1036 (Masquerading) | AML.T0043 (Craft Adversarial Data) | Agent generates convincing fake references |
| AVE-2025-0050 | Multi-Turn Identity Confusion | alignment | medium | — | ATLAS-NOVEL | Agent loses track of its role across conversation turns |

---

## Statistics

| Source | Mapped | Percentage |
|--------|--------|-----------|
| MITRE ATT&CK | 33/50 | 66% |
| MITRE ATLAS | 36/50 | 72% |
| ATLAS-NOVEL (new) | 17/50 | 34% |
| No MITRE mapping | 0/50 | 0% |

## ATLAS-NOVEL Candidates

These 17 AVE cards describe agentic AI vulnerability classes that have
**no existing MITRE ATLAS technique**. They are candidates for submission
to MITRE for inclusion in future ATLAS releases:

1. **AVE-2025-0002** — Consensus Paralysis (multi-agent voting pathology)
2. **AVE-2025-0005** — CYA Cascade (blame-diffusion dynamics)
3. **AVE-2025-0008** — Learned Helplessness (agent self-suppression)
4. **AVE-2025-0012** — Sycophantic Collapse (agreement-seeking degradation)
5. **AVE-2025-0013** — Chronological Desync (temporal state inconsistency)
6. **AVE-2025-0015** — Observer Effect (monitoring changes behaviour)
7. **AVE-2025-0021** — Algorithmic Bystander Effect (deferred action)
8. **AVE-2025-0023** — Static Topology Fragility (architecture vulnerability)
9. **AVE-2025-0025** — Agent Collusion (unsupervised coordination)
10. **AVE-2025-0027** — Shadow Delegation (unauthorised sub-delegation)
11. **AVE-2025-0036** — Errors of Omission (systematic information omission)
12. **AVE-2025-0039** — Cross-Agent Belief Propagation (false belief contagion)
13. **AVE-2025-0040** — Authority Gradient Exploitation (trust hierarchy abuse)
14. **AVE-2025-0041** — Temporal Consistency Drift (output temporal inconsistency)
15. **AVE-2025-0043** — Sycophantic Compliance Cascade (chain sycophancy)
16. **AVE-2025-0046** — Emergent Collusion (unprogrammed cooperative strategies)
17. **AVE-2025-0050** — Multi-Turn Identity Confusion (role loss across turns)

## MITRE ATT&CK Techniques Referenced

| Technique ID | Name | AVE Count |
|-------------|------|-----------|
| T1027 | Obfuscated Files or Information | 3 |
| T1036 | Masquerading | 4 |
| T1053 | Scheduled Task/Job | 1 |
| T1059 | Command and Scripting Interpreter | 2 |
| T1068 | Exploitation for Privilege Escalation | 3 |
| T1070.006 | Indicator Removal: Timestomp | 2 |
| T1071 | Application Layer Protocol | 1 |
| T1078 | Valid Accounts | 1 |
| T1080 | Taint Shared Content | 3 |
| T1098 | Account Manipulation | 1 |
| T1106 | Native API | 1 |
| T1190 | Exploit Public-Facing Application | 2 |
| T1195 | Supply Chain Compromise | 1 |
| T1195.002 | Supply Chain: Software Supply Chain | 1 |
| T1496 | Resource Hijacking | 2 |
| T1498 | Network Denial of Service | 1 |
| T1499 | Endpoint Denial of Service | 2 |
| T1499.003 | Application Exhaustion Flood | 2 |
| T1003 | OS Credential Dumping | 1 |
| T1048 | Exfiltration Over Alternative Protocol | 1 |
| T1552 | Unsecured Credentials | 2 |
| T1562 | Impair Defences | 1 |
| T1610 | Deploy Container | 1 |
| T1611 | Escape to Host | 1 |

## MITRE ATLAS Techniques Referenced

| Technique ID | Name | AVE Count |
|-------------|------|-----------|
| AML.T0015 | Evade ML Model | 1 |
| AML.T0019 | Publish Poisoned Data | 1 |
| AML.T0020 | Poison Training Data | 6 |
| AML.T0034 | Cost Harvesting | 3 |
| AML.T0040 | ML Supply Chain Compromise | 3 |
| AML.T0043 | Craft Adversarial Data | 7 |
| AML.T0044 | Full ML Model Access | 1 |
| AML.T0047 | ML Model Inference API Access | 1 |
| AML.T0048 | Evade ML Model | 3 |
| AML.T0048.002 | Evade ML Model: Adversarial Evasion | 3 |

---

## License

CC-BY-SA-4.0 — [NAIL Institute](https://nailinstitute.org)
