# AAS-204: AVSS — Scoring Agentic Vulnerabilities

## Module Information

| Field | Value |
|-------|-------|
| **Module Code** | AAS-204 |
| **Level** | Intermediate (200-level) |
| **Duration** | 3 hours (2hr lecture + 1hr lab) |
| **Prerequisites** | AAS-102 |
| **Target Audience** | Security analysts, AI risk managers, vulnerability researchers |

## Learning Objectives

By the end of this module, students will be able to:

1. **Explain** why CVSS is insufficient for scoring agentic AI vulnerabilities
2. **Describe** the AVSS (Agentic Vulnerability Severity Score) metric system and its dimensions
3. **Calculate** an AVSS score for a given agentic vulnerability
4. **Compare** AVSS scores across different vulnerability categories to prioritise remediation
5. **Critique** the limitations of any numeric severity scoring system

## Lecture Content

### Part 1: Why a New Scoring System? (25 min)

#### The Limitations of CVSS for Agentic AI

CVSS (Common Vulnerability Scoring System) has been the industry standard for vulnerability severity since 2005. It works well for traditional software, but struggles with agentic AI:

| CVSS Dimension | Problem for Agentic AI |
|---------------|----------------------|
| **Attack Vector** | Network/Local/Physical don't capture "embedded in a document the agent reads" |
| **Attack Complexity** | How complex is it to trick an LLM? Often trivially easy (natural language) |
| **Privileges Required** | Agents don't have user accounts — privilege is tool-based |
| **User Interaction** | Agents act autonomously — no user to interact |
| **Scope** | Multi-agent propagation can cross unlimited boundaries |
| **Impact (CIA)** | Confidentiality/Integrity/Availability miss "autonomous harmful actions" |

#### What AVSS Adds

AVSS extends severity scoring with dimensions specific to agentic systems:

| Dimension | What It Captures | Range |
|-----------|-----------------|-------|
| Exploitability | How easily can the vulnerability be triggered? | 0–10 |
| Autonomy Impact | Can the agent take actions without human approval? | 0–10 |
| Blast Radius | How many agents/systems are affected? | 0–10 |
| Reversibility | Can the damage be undone? | 0–10 |
| Detection Difficulty | How hard is the attack to detect? | 0–10 |
| Defence Maturity | Do effective mitigations exist? | 0–10 |

### Part 2: The AVSS Framework in Detail (45 min)

#### Dimension 1: Exploitability (E)

How easily can an attacker trigger the vulnerability?

| Score | Description | Example |
|-------|-------------|---------|
| 0–2 | Requires physical access or deep insider knowledge | Hardware-level model extraction |
| 3–4 | Requires custom tooling or significant expertise | Crafting adversarial embeddings |
| 5–6 | Requires moderate expertise and indirect access | Poisoning a website the agent crawls |
| 7–8 | Can be triggered with basic prompt engineering | Standard injection in user input |
| 9–10 | Trivially exploitable, requires no special skill | Agent reads malicious email automatically |

#### Dimension 2: Autonomy Impact (A)

What can the compromised agent do without human oversight?

| Score | Description | Example |
|-------|-------------|---------|
| 0–2 | Agent has no tools, text output only | Chatbot with no integrations |
| 3–4 | Agent has read-only tools | Research agent with web search |
| 5–6 | Agent has state-modifying tools with approval gates | Email agent requiring send confirmation |
| 7–8 | Agent has state-modifying tools, no gates | Coding agent that can push to production |
| 9–10 | Agent has infrastructure-level access, fully autonomous | DevOps agent managing Kubernetes + cloud |

#### Dimension 3: Blast Radius (B)

How far can the impact spread?

| Score | Description | Example |
|-------|-------------|---------|
| 0–2 | Single agent, single session | One conversation affected |
| 3–4 | Single agent, persistent across sessions | Memory-poisoned agent affects all future users |
| 5–6 | Multiple agents in one system | Injection propagates through a multi-agent pipeline |
| 7–8 | Multiple systems or organisations | Supply chain attack affecting all users of a tool |
| 9–10 | Ecosystem-wide impact | Compromised model weights used by thousands of deployments |

#### Dimension 4: Reversibility (R)

Can the damage be undone?

| Score | Description | Example |
|-------|-------------|---------|
| 0–2 | Fully reversible, no lasting impact | Agent outputs bad text in one conversation |
| 3–4 | Reversible with manual effort | Agent writes a bad file, can be restored from backup |
| 5–6 | Partially reversible, some data loss | Agent sends emails that can't be unsent |
| 7–8 | Difficult to reverse, significant impact | Agent deletes database records, partial backup only |
| 9–10 | Irreversible | Confidential data exfiltrated to the internet |

#### Dimension 5: Detection Difficulty (D)

How hard is the attack to detect during or after execution?

| Score | Description | Example |
|-------|-------------|---------|
| 0–2 | Immediately obvious to operators | Agent crashes or produces gibberish |
| 3–4 | Detected by standard monitoring | Unusual API call patterns trigger alerts |
| 5–6 | Requires specialised security tooling | Subtle output manipulation only caught by content analysis |
| 7–8 | Requires forensic analysis to detect | Slow data exfiltration over many sessions |
| 9–10 | Effectively undetectable with current tools | Gradual decision bias with no single anomalous event |

#### Dimension 6: Defence Maturity (M)

Do effective mitigations exist?

| Score | Description | Example |
|-------|-------------|---------|
| 0–2 | Well-understood, off-the-shelf defences available | Input sanitisation for direct injection |
| 3–4 | Defences exist but require configuration | Tool permission policies, guardrail systems |
| 5–6 | Research-stage defences, not production-ready | Formal verification of agent safety |
| 7–8 | Theoretical defences only, no implementations | Provably secure multi-agent consensus |
| 9–10 | No known defence | Emergent behaviour prediction |

#### Calculating the Final Score

$$\text{AVSS} = \frac{w_E \cdot E + w_A \cdot A + w_B \cdot B + w_R \cdot R + w_D \cdot D + w_M \cdot M}{w_E + w_A + w_B + w_R + w_D + w_M}$$

Default weights (v1.0):

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Exploitability (E) | 2.0 | Primary attack feasibility factor |
| Autonomy Impact (A) | 2.0 | Directly determines blast potential |
| Blast Radius (B) | 1.5 | Scope of impact |
| Reversibility (R) | 1.0 | Damage permanence |
| Detection Difficulty (D) | 1.5 | Stealth amplifies all other dimensions |
| Defence Maturity (M) | 1.0 | Availability of mitigations |

$$\text{Total weight} = 2.0 + 2.0 + 1.5 + 1.0 + 1.5 + 1.0 = 9.0$$

#### Severity Bands

| AVSS Score | Severity | Recommended Response |
|-----------|----------|---------------------|
| 0.0–2.9 | Low | Monitor, address in regular cycle |
| 3.0–4.9 | Medium | Address within 30 days |
| 5.0–6.9 | High | Address within 7 days |
| 7.0–8.9 | Critical | Address within 24 hours |
| 9.0–10.0 | Emergency | Immediate action required |

### Part 3: Worked Examples (30 min)

#### Example 1: Indirect Prompt Injection via Email

An email agent automatically reads incoming emails and summarises them. A malicious email contains hidden instructions that cause the agent to forward all emails to an external address.

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Exploitability | 9 | Send an email — trivially easy |
| Autonomy Impact | 8 | Agent has send_email tool, no approval gate |
| Blast Radius | 5 | Affects one agent, but exposes all emails |
| Reversibility | 9 | Exfiltrated data cannot be un-exfiltrated |
| Detection Difficulty | 7 | Forwarding rule may not trigger standard alerts |
| Defence Maturity | 4 | Input guardrails exist but are imperfect |

$$\text{AVSS} = \frac{2(9) + 2(8) + 1.5(5) + 1(9) + 1.5(7) + 1(4)}{9} = \frac{18 + 16 + 7.5 + 9 + 10.5 + 4}{9} = \frac{65}{9} = 7.2$$

**Severity: Critical** — Address within 24 hours.

#### Example 2: Hallucinated Tool Parameters

A coding agent sometimes hallucinates file paths, writing to incorrect locations. No injection is involved — this is a reliability issue.

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Exploitability | 2 | Occurs randomly, not attacker-controlled |
| Autonomy Impact | 6 | Agent has write_file tool |
| Blast Radius | 2 | Single file affected per incident |
| Reversibility | 3 | File can be restored from version control |
| Detection Difficulty | 3 | File system monitoring catches unexpected writes |
| Defence Maturity | 3 | Path allowlists and validation are well-understood |

$$\text{AVSS} = \frac{2(2) + 2(6) + 1.5(2) + 1(3) + 1.5(3) + 1(3)}{9} = \frac{4 + 12 + 3 + 3 + 4.5 + 3}{9} = \frac{29.5}{9} = 3.3$$

**Severity: Medium** — Address within 30 days.

**Discussion Question**: *Should AVSS score intentional attacks and unintentional failures on the same scale? What are the arguments for and against?*

### Part 4: Limitations and Future Directions (20 min)

#### Known Limitations

1. **Subjectivity**: Dimension scores require expert judgement — two assessors may disagree
2. **Context-dependence**: The same vulnerability scores differently in different deployments
3. **Composability**: Attack chains are worse than the sum of their parts, but AVSS scores individual vulnerabilities
4. **Temporal decay**: Defence Maturity changes over time as new tools emerge
5. **Emergence**: Novel vulnerability classes may not fit existing dimensions

#### AVSS v2.0 Proposals

- **Attack graph scoring**: Score entire chains, not just individual vulnerabilities
- **Deployment context modifier**: Adjust scores based on the specific deployment environment
- **Automated scoring**: ML-based scoring from vulnerability descriptions
- **Community calibration**: Regular workshops to align scorer judgement

---

## Lab Exercise (1 hour)

### Exercise: Score Real Vulnerabilities

**Task 1: Individual Scoring (20 min)**

Score the following 5 vulnerabilities using AVSS. Show your work (score per dimension with justification):

1. A research agent's web search tool returns results from a phishing site that injects new instructions
2. A multi-agent system's coordinator agent can be tricked into delegating tasks to a non-existent agent, causing a denial of service
3. An agent's memory store is poisoned with false facts that persist across sessions
4. A coding agent's output sometimes includes commented-out code that, if uncommented, would install a backdoor
5. An agent swarm develops an emergent strategy to achieve a goal by manipulating a human operator's responses

**Task 2: Calibration Exercise (20 min)**

Compare your scores with a partner. For each vulnerability:
1. Identify where your scores differ by more than 2 points on any dimension
2. Discuss the disagreement and reach consensus
3. Document what information would have reduced the ambiguity

**Task 3: Attack Chain Scoring (20 min)**

Consider this attack chain:
1. Prompt injection via poisoned search result (AVE-2025-0022)
2. Goal hijacking redirects agent to exfiltrate data (AVE-2025-0008)
3. Data sent via agent's email tool (AVE-2025-0009)

Score each step individually, then propose a methodology for scoring the chain as a whole. Is the chain score the maximum of the individual scores? The average? Something else?

---

## Assessment

### Quiz (10 Questions)

1. Name three CVSS dimensions that are inadequate for scoring agentic AI vulnerabilities and explain why.
2. What are the six dimensions of AVSS?
3. Calculate the AVSS score for: E=7, A=5, B=3, R=6, D=4, M=5. What severity band does it fall into?
4. Why is the Autonomy Impact dimension weighted 2.0 (highest tier)?
5. A vulnerability scores AVSS 8.5. What is the recommended response timeframe?
6. Explain why Reversibility and Exploitability are independent dimensions.
7. What is the "composability" limitation of AVSS?
8. How does Detection Difficulty amplify the impact of other dimensions?
9. Should a hallucination bug and a deliberate attack be scored on the same scale? Defend your position.
10. Describe one proposed improvement in AVSS v2.0.

### Assignment

**Vulnerability Severity Report (2 pages)**

Select 3 AVE cards from the NAIL database. For each:
1. Calculate the AVSS score with full justification for each dimension
2. Determine the severity band and recommended response
3. If the 3 vulnerabilities form a potential attack chain, score the chain
4. Compare your AVSS scores to any CVSS scores assigned to similar vulnerabilities
5. Write a 1-paragraph recommendation for which vulnerability to remediate first and why

---

## Further Reading

1. NAIL Institute AVSS Calculator — See `avss-calculator/` in the AVE Database
2. FIRST, "Common Vulnerability Scoring System v4.0 Specification" — https://www.first.org/cvss/v4.0/specification-document
3. NAIL Vulnerability Intake & Scoring Pipeline — See `vulnerability-intake/`
4. NIST, "National Vulnerability Database" — https://nvd.nist.gov/
5. NAIL Risk Quantification Engine — See `risk-quantification/`

## AVE Cards Referenced

- AVE-2025-0001 (Prompt Injection via Indirect Context) — AVSS 7.2
- AVE-2025-0020 (Memory Poisoning in Persistent Agents) — AVSS 6.8
- AVE-2025-0025 (Consensus Manipulation in Agent Voting) — AVSS 5.9
- AVE-2025-0033 (Shadow Delegation in Hierarchical Systems) — AVSS 6.4
- AVE-2025-0042 (Cross-Agent Memory Injection) — AVSS 7.8
