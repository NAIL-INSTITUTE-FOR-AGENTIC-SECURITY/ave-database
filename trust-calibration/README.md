# Trust Calibration Engine

**Phase 25 — Service 4 of 5 · Port `9903`**

Dynamic trust scoring between human operators and AI agents with calibration
exercises, accuracy tracking, trust boundary enforcement, and bi-directional
trust modelling.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Entity Registry** | Register human operators and AI agents with role, department, capabilities; track trust relationships as directed pairs (trustor → trustee) |
| **Trust Scores** | Bi-directional trust: human→AI and AI→human; composite score 0-100 from 5 dimensions: competence (30%) + reliability (25%) + transparency (20%) + predictability (15%) + benevolence (10%) |
| **Calibration Exercises** | Structured exercises: present scenario → collect predicted outcome from both parties → reveal actual outcome → update trust based on accuracy; 5 exercise types (prediction/classification/risk_assessment/anomaly_detection/decision_making) |
| **Accuracy Tracking** | Per-entity rolling accuracy: predictions vs actuals; over-confidence detection (high confidence + wrong = trust penalty); under-confidence detection (low confidence + right = trust boost) |
| **Trust Boundaries** | Configurable boundaries: min_trust_for_autonomy, trust_decay_rate (unused relationships decay), trust_recovery_rate, max_trust_change_per_event; boundary violations trigger alerts |
| **Trust Events** | Log trust-affecting events: successful_collaboration / failed_task / accurate_prediction / inaccurate_prediction / override_accepted / override_rejected / calibration_completed |
| **Decay & Recovery** | Time-based trust decay for inactive relationships (configurable half-life); recovery through successful interactions; floor/ceiling enforcement |
| **Trust Network** | Visualise trust relationships as directed graph; identify trust bottlenecks; compute network-wide trust metrics (avg, min, clustering) |
| **Analytics** | Trust distribution, calibration performance, accuracy trends, trust event frequency, boundary violations |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/entities` | Register entity (human/AI) |
| `GET` | `/v1/entities` | List entities |
| `POST` | `/v1/trust-pairs` | Create trust relationship |
| `GET` | `/v1/trust-pairs` | List trust pairs |
| `GET` | `/v1/trust-pairs/{id}` | Get trust pair detail |
| `POST` | `/v1/trust-pairs/{id}/event` | Log trust event |
| `POST` | `/v1/calibrations` | Start calibration exercise |
| `POST` | `/v1/calibrations/{id}/respond` | Submit prediction |
| `POST` | `/v1/calibrations/{id}/resolve` | Reveal actual + update trust |
| `GET` | `/v1/trust-network` | Trust network overview |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9903 --reload
```

> **Production note:** Replace in-memory stores with graph database (Neo4j) for trust network analysis; add real ML model integration for accuracy tracking.
