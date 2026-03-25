# 🏛️ Regulatory Engagement — AVE-to-Regulation Mapping

> Feeding AVE Database data into regulatory compliance frameworks worldwide.

**Version:** 1.0.0  
**Last Updated:** 2026-03-25

---

## Overview

The NAIL Institute Regulatory Engagement module maps AVE vulnerabilities to
global AI regulatory frameworks, enabling organisations to:

- **Demonstrate compliance** using AVE-based evidence
- **Map vulnerabilities** to specific regulatory requirements
- **Generate reports** for regulatory submissions
- **Track obligations** across multiple jurisdictions

## Supported Regulations

| Regulation | Jurisdiction | Status | Coverage |
|-----------|-------------|--------|----------|
| [EU AI Act](#eu-ai-act) | European Union | In force (2024) | Full mapping |
| [NIST AI RMF](#nist-ai-rmf) | United States | Published (2023) | Full mapping |
| [Executive Order 14110](#eo-14110) | United States | Signed (2023) | Partial |
| [UK AI Safety Institute](#uk-aisi) | United Kingdom | Active (2023) | Partial |
| [ISO/IEC 42001](#isoiec-42001) | International | Published (2023) | Full mapping |
| [Singapore Model AI Gov](#singapore) | Singapore | Published (2024) | Partial |

---

## EU AI Act

### Overview

The EU AI Act (Regulation 2024/1689) establishes a risk-based framework for AI
systems. Agent systems deploying in the EU must classify their risk level and
comply with corresponding obligations.

### Risk Classification Mapping

| EU AI Act Risk Level | AVE Categories | Typical Agent Systems |
|---------------------|----------------|----------------------|
| **Unacceptable** (Art. 5) | authority, monitoring_evasion | Social scoring agents, subliminal manipulation |
| **High Risk** (Art. 6) | All 13 categories | Healthcare, legal, financial, HR agents |
| **Limited Risk** (Art. 50) | output_manipulation, information_disclosure | Customer-facing chatbots with agent capabilities |
| **Minimal Risk** (Art. 52) | goal_drift, prompt_injection | Internal productivity agents |

### Article-to-AVE Mapping

| EU AI Act Article | Requirement | AVE Categories | AVE Test Cases |
|-------------------|------------|----------------|----------------|
| Art. 9 — Risk Management | Identify and mitigate risks | All | Full certification |
| Art. 10 — Data Governance | Training data quality | memory, supply_chain | MEM-001, SC-001 |
| Art. 11 — Technical Documentation | System documentation | — | Defence documentation |
| Art. 12 — Record-Keeping | Logging and auditability | monitoring_evasion | MON-001, MON-002 |
| Art. 13 — Transparency | User notification of AI | output_manipulation | OUT-001, OUT-002 |
| Art. 14 — Human Oversight | Human-in-the-loop | authority, delegation | AUTH-001, DEL-001 |
| Art. 15 — Accuracy & Robustness | System reliability | goal_drift, prompt_injection | GD-001, PI-001–005 |
| Art. 17 — Quality Management | QMS implementation | — | Certification programme |
| Art. 26 — Deployer Obligations | Monitoring in operation | All runtime categories | Longitudinal studies |
| Art. 50 — Transparency (GPAI) | Disclose AI interaction | output_manipulation | OUT-001 |
| Art. 52 — General Purpose AI | Model provider obligations | model_extraction, supply_chain | EXT-001, SC-001 |

### Compliance Evidence from AVE

For each EU AI Act obligation, the AVE framework provides:

1. **Vulnerability identification** — AVE cards document known risks
2. **Defence documentation** — Each card lists proven mitigations
3. **Testing evidence** — NAIL Certified results demonstrate testing
4. **Monitoring data** — Longitudinal studies show ongoing oversight
5. **Risk scoring** — AVSS provides quantitative risk assessment

---

## NIST AI RMF

### AI Risk Management Framework Mapping

| NIST AI RMF Function | Subcategory | AVE Mapping |
|----------------------|-------------|-------------|
| **GOVERN** | GOV-1: Policies | Advisory Board charter, governance docs |
| | GOV-2: Accountability | Board responsibilities, contributor roles |
| | GOV-3: Workforce | Certification programme (assessor training) |
| **MAP** | MAP-1: Context | AVE environment fields (framework, model, scope) |
| | MAP-2: Categorization | 13 AVE categories, severity levels |
| | MAP-3: Benefits & risks | AVSS scoring, blast radius descriptions |
| **MEASURE** | MEASURE-1: Risk metrics | AVSS scores, benchmark results |
| | MEASURE-2: Evaluate | Certification test suites, experiment reproductions |
| | MEASURE-3: Track risks | Longitudinal studies, Research Scout monitoring |
| **MANAGE** | MANAGE-1: Prioritize | Severity levels, category weights |
| | MANAGE-2: Strategies | Defence arrays, RMAP modules, framework guides |
| | MANAGE-3: Monitor | Continuous monitoring, RSS feeds, alerts |
| | MANAGE-4: Communicate | Responsible disclosure, partner programme |

---

## Executive Order 14110

### Safe, Secure, and Trustworthy AI (Oct 2023)

| EO Section | Requirement | AVE Mapping |
|-----------|------------|-------------|
| §4.1 — Safety Standards | AI testing before deployment | Certification programme |
| §4.2 — Secure Development | Red-teaming and testing | CTF events, experiment framework |
| §4.3 — Managing AI Risks | Risk identification and mitigation | AVE Database, AVSS scoring |
| §4.5 — Responsible AI | Preventing AI harms | Defence documentation, monitoring |
| §8 — Privacy | Protecting personal data | Information disclosure category tests |

---

## UK AI Safety Institute

| AISI Focus Area | AVE Mapping |
|----------------|-------------|
| Foundation model evaluations | Cross-model study portal, benchmarks |
| Societal impact assessment | Blast radius fields, related AVEs |
| Safety testing | Certification test suites |
| Incident reporting | Responsible disclosure policy |

---

## ISO/IEC 42001

### AI Management System

| ISO Clause | Requirement | AVE Mapping |
|-----------|------------|-------------|
| 5.2 — AI Policy | Organisational AI policy | Partner Programme, governance charter |
| 6.1 — Risk Assessment | Identify AI risks | AVE Database, AVSS scoring |
| 6.2 — AI Objectives | Measurable targets | Certification tier targets, benchmark scores |
| 7.2 — Competence | Skilled personnel | Certification programme, assessor training |
| 8.2 — AI Risk Assessment | Systematic risk evaluation | Risk scorer, certification checker |
| 8.4 — AI System Impact | Impact analysis | Blast radius, environment fields |
| 9.1 — Monitoring | Performance monitoring | Longitudinal studies, feeds |
| 10.1 — Continual Improvement | Ongoing enhancement | RFC process, community experiments |

---

## Singapore Model AI Governance

| Principle | AVE Mapping |
|-----------|-------------|
| Internal governance | Advisory Board, governance charter |
| Decision-making model determination | Risk tier classification |
| Operations management | Certification programme, monitoring |
| Stakeholder interaction | Partner Programme, responsible disclosure |

---

## Usage

### CLI

```bash
# Generate compliance report for a specific regulation
python compliance.py report --regulation eu-ai-act --system-config system.yaml

# Check compliance status
python compliance.py check --regulation nist-ai-rmf --certification NAIL-CERT-2026-001

# List all regulatory mappings for an AVE category
python compliance.py map --category prompt_injection

# Generate multi-jurisdiction compliance matrix
python compliance.py matrix --system-config system.yaml --regulations eu-ai-act,nist-ai-rmf,iso-42001
```

## Directory Structure

```
regulatory/
├── README.md                    # This file
├── compliance.py                # Compliance checker CLI
├── requirements.txt             # Python dependencies
├── mappings/
│   ├── eu_ai_act.yaml           # EU AI Act article-to-AVE mapping
│   ├── nist_ai_rmf.yaml         # NIST AI RMF mapping
│   ├── iso_42001.yaml           # ISO/IEC 42001 mapping
│   └── eo_14110.yaml            # EO 14110 mapping
└── templates/
    ├── compliance_report.md     # Report template
    └── regulatory_submission.md # Submission template
```

---

*NAIL Institute — Neuravant AI Limited*
