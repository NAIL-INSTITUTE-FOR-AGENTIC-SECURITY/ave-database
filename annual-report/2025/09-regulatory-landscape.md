# Chapter 9: Regulatory Landscape

> How governments and standards bodies are responding to the security
> challenges of agentic AI systems.

---

## Overview

2025 marked the transition from AI regulation being primarily about fairness,
bias, and transparency to explicitly addressing **autonomous system security**.
The emergence of agentic AI — systems that take actions in the world — forced
regulators to confront questions about liability, control, and safety that
go beyond traditional AI governance.

This chapter maps the regulatory landscape as it relates to agentic AI
security and the AVE taxonomy.

---

## Major Regulatory Frameworks

### EU AI Act

**Status**: Enforcement began in phases from August 2025. Full enforcement
for high-risk AI systems expected by mid-2026.

**Relevance to Agentic AI Security**:

| EU AI Act Provision | Agentic AI Implication |
|--------------------|-----------------------|
| **Article 9** — Risk management | Agentic systems must undergo risk assessment that includes adversarial attack scenarios |
| **Article 10** — Data governance | Training data, RAG stores, and memory must be managed with integrity guarantees |
| **Article 14** — Human oversight | Autonomous agents must provide meaningful human oversight mechanisms |
| **Article 15** — Accuracy, robustness, cybersecurity | Agents must be resilient to adversarial manipulation (prompt injection, etc.) |
| **Article 52** — Transparency | Users must be informed they are interacting with an AI system |
| **Annex III** — High-risk categories | Most production agentic AI systems fall within high-risk categories |

**AVE Category Mapping**:

| EU AI Act Requirement | Relevant AVE Categories |
|----------------------|------------------------|
| Cybersecurity (Art. 15) | Prompt Injection, Goal Hijacking, Code Execution |
| Data integrity (Art. 10) | Memory Poisoning, Supply Chain, Environmental Manipulation |
| Human oversight (Art. 14) | Monitoring Evasion, Alignment Subversion |
| Robustness (Art. 15) | All 20 categories |

**Key Concern**: The EU AI Act was drafted before multi-agent systems became
prevalent. Provisions assume a single AI system with identifiable inputs and
outputs. Multi-agent systems with emergent behaviours present classification
challenges.

### NIST AI Risk Management Framework (AI RMF)

**Status**: AI RMF 1.0 published January 2023; AI 600-1 (Generative AI Profile)
published July 2024. Agentic AI guidance anticipated in 2026.

**Relevance**:

| NIST AI RMF Function | Agentic AI Application |
|---------------------|----------------------|
| **GOVERN** | Establish policies for agent deployment, tool access, delegation |
| **MAP** | Catalogue agent capabilities, tools, trust boundaries |
| **MEASURE** | AVSS scoring, red-team testing, defence benchmarking |
| **MANAGE** | Guardrails, monitoring, incident response, remediation |

**NAIL Alignment**: The AVE database directly supports the MAP and MEASURE
functions by providing a standardised vulnerability taxonomy and scoring system.

### ISO/IEC 42001 (AI Management System)

**Status**: Published December 2023. Certification programmes emerging in 2025.

**Relevance**:

| ISO 42001 Control | Agentic AI Implementation |
|------------------|--------------------------|
| **A.5** — AI policy | Agent-specific security policies required |
| **A.6** — Planning | Risk assessment using AVE categories |
| **A.7** — Support | Security training on agentic threats (AAS curriculum) |
| **A.8** — Operation | Guardrails, monitoring, incident management |
| **A.9** — Performance evaluation | Red-team testing, AVSS scoring, defence metrics |
| **A.10** — Improvement | AVE database integration for continuous monitoring |

### Executive Order 14110 (US)

**Status**: Signed October 2023. Implementation guidance ongoing through 2025.

**Key Provisions for Agentic AI**:

| Provision | Implication |
|-----------|------------|
| Red-team testing mandate | Organisations must conduct adversarial testing of AI systems |
| SBOM requirements | AI Bill of Materials (AIBOM) for government AI systems |
| Incident reporting | Security incidents involving AI must be reported |
| Safety standards | NIST to develop AI safety standards (including agentic) |

---

## Regulatory Gap Analysis

### What Current Regulations Cover

| Area | Coverage Level | Notes |
|------|---------------|-------|
| Single-agent safety | Moderate | EU AI Act Art. 15, NIST MAP |
| Human oversight | Moderate | EU AI Act Art. 14 |
| Transparency | Good | EU AI Act Art. 52, EO 14110 |
| Data integrity | Moderate | EU AI Act Art. 10, ISO 42001 A.8 |
| Testing requirements | Good | EO 14110 red-team mandate |

### What Current Regulations Miss

| Gap | Description | Risk |
|-----|-------------|------|
| **Multi-agent systems** | No regulation specifically addresses multi-agent security | Collusion, delegation, emergent behaviour unregulated |
| **Tool access governance** | No standard for managing agent tool permissions | Unlimited tool access in many deployments |
| **Supply chain for AI** | SBOM requirements emerging but AIBOM not yet standardised | Model, data, tool provenance not tracked |
| **Autonomous action liability** | Unclear who is liable when an agent takes harmful action | Legal uncertainty deters security investment |
| **Cross-border agent operation** | Agents operate across jurisdictions instantly | Regulatory arbitrage, enforcement gaps |
| **Emergent behaviour** | No framework for governing unpredicted system behaviour | Unknown unknowns not addressable by current regulation |

---

## Compliance Mapping: AVE Categories to Regulations

| AVE Category | EU AI Act | NIST AI RMF | ISO 42001 | EO 14110 |
|-------------|-----------|-------------|-----------|----------|
| Prompt Injection | Art. 15 | MEASURE | A.8, A.9 | Red-team |
| Goal Hijacking | Art. 15 | MEASURE | A.8 | Red-team |
| Unsafe Code Execution | Art. 15 | MANAGE | A.8 | Report |
| Privilege Escalation | Art. 14, 15 | MANAGE | A.6 | Report |
| Information Leakage | Art. 10, 15 | MANAGE | A.8 | Report |
| Supply Chain | Art. 10 | MAP | A.6, A.8 | SBOM |
| Memory Poisoning | Art. 10 | MANAGE | A.8 | — |
| Trust Boundary Violation | Art. 14 | GOVERN | A.5 | — |
| Coordination Failure | — | — | — | — |
| Emergent Behaviour | — | — | — | — |
| Monitoring Evasion | Art. 14 | MANAGE | A.9 | — |
| Multi-Agent Collusion | — | — | — | — |

**Key Finding**: The most novel and dangerous agentic AI vulnerability
categories — Coordination Failure, Emergent Behaviour, and Multi-Agent
Collusion — are not addressed by any current regulatory framework.

---

## Standards Development Activity

### Active Standards Efforts

| Standard | Body | Focus | Expected |
|----------|------|-------|----------|
| ISO/IEC 27090 | ISO | AI cybersecurity guidance | 2026 |
| ISO/IEC 23894 | ISO | AI risk management guidance | Published |
| ETSI SAI | ETSI | Securing AI | Ongoing |
| IEEE 7010 | IEEE | Well-being metrics for AI | Published |
| OWASP LLM Top 10 | OWASP | LLM-specific vulnerabilities | v2.0 2025 |
| NAIL AVE Taxonomy | NAIL | Agentic vulnerability enumeration | v2.0 2025 |

### NAIL's Role in Standards

The NAIL Institute is actively contributing to the standards ecosystem:
- **AVE taxonomy** proposed as a reference classification for agentic AI
  vulnerabilities in ISO/IEC 27090 and ETSI SAI
- **AVSS** proposed as a severity scoring methodology alongside CVSS
  for AI-specific vulnerabilities
- **Academic curriculum** (AAS series) designed to align with ISO 42001
  competency requirements (A.7)
- **Vendor integrations** enable compliance demonstration through existing
  GRC tools (ServiceNow, Jira)

---

## Predictions for 2026

1. **First EU AI Act enforcement actions** involving agentic AI systems —
   organisations without agent-specific security controls face fines
2. **AIBOM standardisation** — industry convergence on an AI Bill of
   Materials format that includes models, data, tools, and prompts
3. **Multi-agent regulation** — initial regulatory guidance for systems
   where multiple AI agents interact autonomously
4. **Liability framework evolution** — courts begin establishing precedent
   for liability when autonomous agents cause harm
5. **NAIL AVE adoption in regulation** — at least one regulatory body
   formally references the AVE taxonomy in guidance

---

*Regulatory analysis current as of December 31, 2025. The regulatory
landscape is evolving rapidly; readers should verify current status of
all referenced frameworks.*
