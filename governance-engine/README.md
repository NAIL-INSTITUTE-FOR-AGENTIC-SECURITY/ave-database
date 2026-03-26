# 🏛️ Autonomous Governance Engine

> AI-assisted policy engine that dynamically adjusts organisational AI governance
> based on threat landscape, compliance requirements, and risk tolerance.

**Phase 13 · Item 5 · Port 8704**

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                      AUTONOMOUS GOVERNANCE ENGINE                         │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ Policy   │ Risk     │ Compli-  │ Threat   │ Decision │ Audit              │
│ Engine   │ Assessor │ ance     │ Integr-  │ Engine   │ Logger             │
│          │          │ Monitor  │ ator     │          │                    │
├──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────────┤
│                      GOVERNANCE KNOWLEDGE BASE                            │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ Policy   │ Regul-   │ Risk     │ Org      │ Incident │ Change             │
│ Library  │ atory    │ Appetite │ Context  │ History  │ Log                │
│          │ Matrix   │ Model    │          │          │                    │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────────┘
```

## Concepts

| Concept | Description |
|---------|-------------|
| **Policy** | A governance rule with conditions, actions, and enforcement level |
| **Risk Appetite** | Organisation-configurable tolerance thresholds per domain |
| **Compliance Posture** | Current state of compliance across regulatory frameworks |
| **Threat Context** | Live threat landscape data influencing policy adjustments |
| **Policy Adjustment** | Automated policy modification in response to changed conditions |
| **Governance Decision** | Auditable record of every automated policy change |

## Key Features

1. **Dynamic Policy Adjustment** — Policies auto-tune based on threat landscape, compliance gaps, and risk posture
2. **Risk-Appetite Modelling** — Configurable per-domain risk tolerance with floor/ceiling thresholds
3. **Multi-Framework Compliance** — Maps policies to NIST AI RMF, EU AI Act, ISO 42001, OWASP LLM Top 10
4. **Threat-Driven Governance** — Ingests threat intelligence to proactively tighten or relax policies
5. **Governance Decisions Audit** — Every policy change is logged with justification, trigger, and rollback path
6. **Policy Simulation** — "What-if" analysis of proposed policy changes before deployment
7. **Organisational Context** — Adapts recommendations to industry, size, and regulatory jurisdiction
8. **Automated Escalation** — Policies exceeding risk appetite trigger human review workflows

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health |
| `POST` | `/v1/policies` | Create a governance policy |
| `GET` | `/v1/policies` | List policies |
| `GET` | `/v1/policies/{id}` | Policy details |
| `PATCH` | `/v1/policies/{id}` | Update policy |
| `DELETE` | `/v1/policies/{id}` | Archive policy |
| `POST` | `/v1/risk-appetite` | Set risk appetite profile |
| `GET` | `/v1/risk-appetite` | Current risk appetite |
| `POST` | `/v1/evaluate` | Evaluate governance posture & generate adjustments |
| `POST` | `/v1/simulate` | Simulate policy change impact |
| `POST` | `/v1/threats/ingest` | Ingest threat signal for governance context |
| `GET` | `/v1/decisions` | Governance decision audit log |
| `GET` | `/v1/decisions/{id}` | Decision details |
| `POST` | `/v1/decisions/{id}/rollback` | Rollback a governance decision |
| `GET` | `/v1/compliance-map` | Policy → regulatory requirement mapping |
| `GET` | `/v1/analytics` | Governance analytics |

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 8704 --reload
```

Docs at http://localhost:8704/docs
