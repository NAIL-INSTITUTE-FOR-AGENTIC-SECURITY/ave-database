# 🤖 Regulatory Compliance Autopilot

> Fully autonomous compliance engine that continuously monitors
> regulatory changes across jurisdictions, maps new requirements
> to AVE controls, and auto-adjusts governance policies.

## Overview

The Regulatory Compliance Autopilot eliminates manual compliance
tracking by ingesting regulatory updates from global jurisdictions,
parsing them for AI-relevant requirements, mapping those requirements
to existing AVE controls, identifying gaps, generating remediation
actions, and auto-adjusting governance policies — all with human
oversight gates for high-impact changes.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                Regulatory Compliance Autopilot                 │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ Reg      │  │ Parser & │  │ Control  │  │ Policy       │ │
│  │ Monitor  │  │ Classifier│  │ Mapper   │  │ Auto-Adjuster│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │
│       │              │              │               │         │
│  ┌────▼──────────────▼──────────────▼───────────────▼───────┐ │
│  │              Compliance Intelligence Engine               │ │
│  │  Gap Analysis │ Impact Scoring │ Remediation Planning    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Jurisdic-│  │ Human        │  │ Compliance│  │ Audit    │ │
│  │ tion     │  │ Oversight    │  │ Posture   │  │ Trail    │ │
│  │ Registry │  │ Gate         │  │ Dashboard │  │          │ │
│  └──────────┘  └──────────────┘  └──────────┘  └──────────┘ │
└───────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Regulatory Monitor** | Tracks updates from 8+ jurisdictions (US, EU, UK, AU, CA, SG, JP, BR) |
| **AI Requirement Parser** | Extracts AI-specific obligations from regulatory text |
| **Framework Mapping** | Maps requirements to NIST AI RMF, EU AI Act, ISO 42001, OWASP LLM Top 10 |
| **AVE Control Mapper** | Links regulatory requirements to specific AVE defence categories |
| **Gap Analysis** | Identifies missing controls against new requirements |
| **Impact Scoring** | Quantifies business impact of non-compliance |
| **Policy Auto-Adjuster** | Generates governance policy updates with approval workflows |
| **Human Oversight Gate** | High-impact changes require manual approval |
| **Compliance Posture** | Real-time compliance score across all jurisdictions |
| **Remediation Planner** | Prioritised action items with effort/impact estimates |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health and jurisdiction count |
| `POST` | `/v1/regulations` | Ingest a regulatory update |
| `GET` | `/v1/regulations` | List tracked regulations |
| `GET` | `/v1/regulations/{reg_id}` | Get regulation details with mappings |
| `GET` | `/v1/jurisdictions` | List monitored jurisdictions |
| `POST` | `/v1/analyse` | Run compliance gap analysis |
| `GET` | `/v1/gaps` | List identified compliance gaps |
| `POST` | `/v1/adjustments` | Generate policy adjustment recommendations |
| `GET` | `/v1/adjustments` | List pending/applied adjustments |
| `POST` | `/v1/adjustments/{adj_id}/approve` | Approve a policy adjustment |
| `GET` | `/v1/posture` | Current compliance posture across jurisdictions |
| `GET` | `/v1/audit` | Compliance autopilot audit trail |
| `GET` | `/v1/analytics` | Regulatory analytics and trends |

## Running

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 8903
```

## Port

| Service | Port |
|---------|------|
| Regulatory Compliance Autopilot | **8903** |

## Production Notes

- Replace in-memory stores with **PostgreSQL** + **Elasticsearch**
- Integrate **real regulatory feeds** (Thomson Reuters, LexisNexis)
- Add **NLP pipeline** for requirement extraction from legal text
- Enable **webhook notifications** for compliance posture changes
