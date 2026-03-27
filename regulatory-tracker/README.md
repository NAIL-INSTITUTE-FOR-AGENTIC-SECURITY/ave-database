# Regulatory Change Tracker

**Phase 23 — Service 5 of 5 · Port `9704`**

Automated monitoring of AI regulatory changes across jurisdictions with
impact assessment, compliance gap detection, and action-item generation.

---

## Core Concepts

### Jurisdictions
Pre-seeded regulatory jurisdictions:
| Code | Name | Key Legislation |
|------|------|-----------------|
| `EU` | European Union | EU AI Act 2024/1689 |
| `US` | United States | Executive Order 14110, NIST AI RMF |
| `UK` | United Kingdom | AI Regulation White Paper |
| `CN` | China | Interim Measures for GenAI |
| `JP` | Japan | AI Strategy 2022 |
| `AU` | Australia | AI Ethics Framework |
| `BR` | Brazil | AI Bill PL 2338/2023 |
| `IN` | India | DPDP Act 2023 |
| `CA` | Canada | AIDA (C-27) |
| `SG` | Singapore | Model AI Governance Framework |

### Regulatory Changes
A **change** represents a new or amended regulation:
- **change_id** / **jurisdiction** / **title** / **description**
- **change_type**: `new_legislation` | `amendment` | `guidance` | `enforcement_action` | `court_ruling`
- **severity**: `critical` | `high` | `medium` | `low`
- **effective_date** / **published_date**
- **affected_domains**: list of AI domains impacted

### Impact Assessments
Each change is assessed for organisational impact:
- **compliance_gap** — what is not currently compliant
- **required_actions** — steps to achieve compliance
- **effort_estimate_hours** — implementation effort
- **deadline** — when compliance is required
- **risk_if_non_compliant** — fine ranges, operational restrictions

### Action Items
Generated from impact assessments:
- **action_id** / **title** / **owner** / **priority** / **status**
- Status: `open` → `in_progress` → `completed` → `verified`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `GET` | `/v1/jurisdictions` | List monitored jurisdictions |
| `POST` | `/v1/changes` | Register regulatory change |
| `GET` | `/v1/changes` | List changes with filters |
| `GET` | `/v1/changes/{id}` | Change detail |
| `POST` | `/v1/changes/{id}/assess` | Create impact assessment |
| `GET` | `/v1/changes/{id}/assessment` | Get assessment |
| `POST` | `/v1/action-items` | Create action item |
| `GET` | `/v1/action-items` | List action items |
| `PATCH` | `/v1/action-items/{id}/advance` | Advance status |
| `GET` | `/v1/analytics` | Regulatory analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9704
```

---

*Part of the NAIL Institute AVE Database — Phase 23: Autonomous Resilience & Self-Healing Infrastructure*
