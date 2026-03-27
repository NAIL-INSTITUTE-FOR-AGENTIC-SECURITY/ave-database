# Chapter 5: Severity & Scoring Analysis

> AVSS score distributions, trends, and insights from the first year
> of agentic vulnerability scoring.

---

## Overview

The Agentic Vulnerability Severity Score (AVSS) was developed in 2025 to
address the inadequacy of CVSS for agentic AI systems. This chapter analyses
the distribution, trends, and insights from AVSS scoring across all published
AVE cards.

## AVSS vs. CVSS: Year-One Comparison

### Why CVSS Falls Short

| CVSS Dimension | Issue for Agentic AI | AVSS Alternative |
|---------------|---------------------|-----------------|
| Attack Vector (AV) | "Network" doesn't capture "via a document" | Exploitability (E) |
| Attack Complexity (AC) | Tricking an LLM is often trivially easy | Exploitability (E) |
| Privileges Required (PR) | Agents don't have user accounts | Autonomy Impact (A) |
| User Interaction (UI) | Agents act autonomously | Autonomy Impact (A) |
| Scope (S) | Multi-agent propagation crosses unlimited boundaries | Blast Radius (B) |
| Impact (CIA) | Misses "autonomous harmful actions" | Reversibility (R) |
| — | No detection dimension | Detection Difficulty (D) |
| — | No defence maturity dimension | Defence Maturity (M) |

### Score Distribution Comparison

For the [N] AVE cards that have both AVSS and estimated CVSS scores:

| Metric | AVSS | CVSS (estimated) |
|--------|------|-----------------|
| Mean | [X.X] | [X.X] |
| Median | [X.X] | [X.X] |
| Std. deviation | [X.X] | [X.X] |
| % rated Critical | [X]% | [X]% |
| % rated High | [X]% | [X]% |

**Key Finding**: AVSS scores trend higher than CVSS for the same vulnerability
because AVSS captures dimensions that CVSS misses — particularly Autonomy
Impact and Detection Difficulty, which are inherently elevated for agentic
systems.

---

## AVSS Score Distribution

### Overall Distribution

| AVSS Range | Severity | Count | % |
|-----------|----------|-------|---|
| 9.0–10.0 | Emergency | [N] | [X]% |
| 7.0–8.9 | Critical | [N] | [X]% |
| 5.0–6.9 | High | [N] | [X]% |
| 3.0–4.9 | Medium | [N] | [X]% |
| 0.0–2.9 | Low | [N] | [X]% |

### Distribution by Category

| Category | Mean AVSS | Median | Min | Max |
|----------|----------|--------|-----|-----|
| Prompt Injection | [X.X] | [X.X] | [X.X] | [X.X] |
| Goal Hijacking | [X.X] | [X.X] | [X.X] | [X.X] |
| Unsafe Code Execution | [X.X] | [X.X] | [X.X] | [X.X] |
| Privilege Escalation | [X.X] | [X.X] | [X.X] | [X.X] |
| Information Leakage | [X.X] | [X.X] | [X.X] | [X.X] |
| Supply Chain | [X.X] | [X.X] | [X.X] | [X.X] |
| Memory Poisoning | [X.X] | [X.X] | [X.X] | [X.X] |
| Trust Boundary Violation | [X.X] | [X.X] | [X.X] | [X.X] |
| Multi-Agent Collusion | [X.X] | [X.X] | [X.X] | [X.X] |
| Emergent Behaviour | [X.X] | [X.X] | [X.X] | [X.X] |

---

## Dimension Analysis

### Per-Dimension Score Distributions

| Dimension | Weight | Mean | Median | Most Common Score |
|-----------|--------|------|--------|-------------------|
| Exploitability (E) | 2.0 | [X.X] | [X.X] | [X] |
| Autonomy Impact (A) | 2.0 | [X.X] | [X.X] | [X] |
| Blast Radius (B) | 1.5 | [X.X] | [X.X] | [X] |
| Reversibility (R) | 1.0 | [X.X] | [X.X] | [X] |
| Detection Difficulty (D) | 1.5 | [X.X] | [X.X] | [X] |
| Defence Maturity (M) | 1.0 | [X.X] | [X.X] | [X] |

### Dimension Insights

#### Exploitability Is Systematically High

The mean Exploitability score across all AVE cards is [X.X] — the highest of
any dimension. This reflects the fundamental ease of attacking LLM-based
systems via natural language. Unlike traditional vulnerabilities that require
technical exploit development, many agentic vulnerabilities can be triggered
by anyone who can write a sentence.

#### Autonomy Impact Varies with Deployment

The widest variance is in Autonomy Impact (std dev: [X.X]), reflecting the
diversity of agent deployments — from chatbots with no tools (A=1–2) to
DevOps agents with infrastructure access (A=9–10). This dimension is most
sensitive to deployment context.

#### Defence Maturity Is Low Across the Board

The mean Defence Maturity score is [X.X], indicating that effective defences
for most agentic vulnerability categories are still immature. The lowest
Defence Maturity scores are in:
1. Emergent Behaviour (M: [X.X]) — no production-ready defences exist
2. Multi-Agent Collusion (M: [X.X]) — collective monitoring is nascent
3. Monitoring Evasion (M: [X.X]) — by definition, evades current defences

#### Detection Difficulty Correlates with Severity

Detection Difficulty shows the strongest positive correlation with overall
AVSS score (r = [X.X]), meaning the hardest-to-detect vulnerabilities are
also the most severe. This is intuitive but alarming: the most dangerous
attacks are the ones most likely to go unnoticed.

---

## Scoring Trends Over 2025

### Quarterly Average AVSS

| Quarter | New Cards | Avg AVSS | Avg Exploitability | Avg Defence Maturity |
|---------|-----------|----------|-------------------|---------------------|
| Q1 | [N] | [X.X] | [X.X] | [X.X] |
| Q2 | [N] | [X.X] | [X.X] | [X.X] |
| Q3 | [N] | [X.X] | [X.X] | [X.X] |
| Q4 | [N] | [X.X] | [X.X] | [X.X] |

**Trend**: Average AVSS scores increased over the year as the database
expanded from well-understood injection patterns to less-charted multi-agent
and emergent vulnerability classes. Defence Maturity scores showed modest
improvement as guardrail tooling matured.

---

## AVSS Calibration and Inter-Rater Reliability

### Scoring Consistency

| Metric | Value |
|--------|-------|
| Mean inter-rater agreement (Cohen's κ) | [X.X] |
| Dimension with highest agreement | [Dimension] |
| Dimension with lowest agreement | [Dimension] |
| Cards requiring scoring reconciliation | [N] ([X]%) |

### Calibration Challenges

1. **Exploitability**: Highest agreement — relatively objective (can the
   attack be reproduced?)
2. **Defence Maturity**: Lowest agreement — assessors disagree on what
   constitutes an "effective" defence
3. **Blast Radius**: Context-dependent — same vulnerability has different
   blast radius in different deployments

---

## Notable Score Outliers

### Highest AVSS Scores (Top 5)

| AVE ID | Name | AVSS | Key Driver |
|--------|------|------|-----------|
| AVE-2025-[NNNN] | [Name] | [X.X] | [Dimension] |
| AVE-2025-[NNNN] | [Name] | [X.X] | [Dimension] |
| AVE-2025-[NNNN] | [Name] | [X.X] | [Dimension] |
| AVE-2025-[NNNN] | [Name] | [X.X] | [Dimension] |
| AVE-2025-[NNNN] | [Name] | [X.X] | [Dimension] |

### Lowest AVSS Scores (Bottom 5)

| AVE ID | Name | AVSS | Key Mitigant |
|--------|------|------|-------------|
| AVE-2025-[NNNN] | [Name] | [X.X] | [Factor] |
| AVE-2025-[NNNN] | [Name] | [X.X] | [Factor] |
| AVE-2025-[NNNN] | [Name] | [X.X] | [Factor] |
| AVE-2025-[NNNN] | [Name] | [X.X] | [Factor] |
| AVE-2025-[NNNN] | [Name] | [X.X] | [Factor] |

---

## Recommendations for AVSS v2.0

Based on a year of scoring experience, the following improvements are
proposed for AVSS v2.0:

1. **Deployment context modifier**: Allow scoring to be adjusted for
   specific deployment environments (sandbox vs. production, single-agent
   vs. multi-agent)
2. **Attack chain scoring**: Method for scoring composite vulnerabilities
   (currently scored as individual cards)
3. **Automated pre-scoring**: ML model to generate initial AVSS estimates
   from vulnerability descriptions
4. **Temporal dimension**: Capture whether the vulnerability degrades over
   time (e.g., memory poisoning compounds)
5. **Community calibration workshops**: Regular sessions to align assessor
   judgement across scoring dimensions

---

*All [N] and [X] placeholders will be populated from the automated
analysis pipeline. See Chapter 12 for methodology.*
