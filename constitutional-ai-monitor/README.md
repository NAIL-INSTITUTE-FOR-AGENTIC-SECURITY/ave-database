# Constitutional AI Monitor

**Phase 26 — Service 5 of 5 · Port `9909`**

Monitors AI systems for adherence to defined constitutional principles with
violation detection, severity scoring, remediation recommendations, and
continuous constitutional compliance tracking.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Constitution Registry** | Define constitutions with ordered principles: principle_text, category (fairness/safety/transparency/privacy/accountability/beneficence/non_maleficence/autonomy), weight (1-10), enforcement_level (hard_constraint/soft_constraint/aspiration) |
| **AI System Registry** | Register AI systems with system_type (classifier/generator/recommender/agent/pipeline), bound_constitution_id, deployment_env, risk_tier (critical/high/medium/low) |
| **Behavioural Observations** | Log AI system actions as observations: action_type (decision/output/recommendation/denial/escalation), input_summary, output_summary, affected_parties, context metadata |
| **Violation Detection** | Analyse observations against bound constitution: per-principle compliance check, violation_type (direct_violation/borderline/spirit_violation/pattern_violation), confidence 0-1, evidence chain |
| **Severity Scoring** | Multi-factor severity: principle_weight × enforcement_level × affected_scope × recurrence_multiplier; 5 severity tiers: critical (≥90) / high (70-89) / medium (50-69) / low (30-49) / info (<30) |
| **Remediation Recommendations** | Auto-generated remediation per violation: action_type (retrain/constrain/audit/rollback/decommission/human_review), estimated_effort, priority, deadline_suggestion |
| **Compliance Score** | Per-system rolling compliance score 0-100: weighted average of principle adherence; trend tracking (improving/stable/declining); threshold alerts |
| **Constitutional Amendments** | Propose amendments to principles: amendment_type (add/modify/remove/reorder), requires approval (linked to governance), version tracking with rationale |
| **Reporting** | Constitutional compliance reports: per-system + per-principle breakdown, violation trends, remediation progress, risk heat map |
| **Analytics** | Violations by category/severity/system, compliance score distribution, remediation completion rates, amendment history |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/constitutions` | Create constitution |
| `GET` | `/v1/constitutions` | List constitutions |
| `GET` | `/v1/constitutions/{id}` | Get constitution detail |
| `POST` | `/v1/constitutions/{id}/amend` | Propose amendment |
| `POST` | `/v1/systems` | Register AI system |
| `GET` | `/v1/systems` | List systems |
| `POST` | `/v1/systems/{id}/bind` | Bind system to constitution |
| `POST` | `/v1/observations` | Log behavioural observation |
| `POST` | `/v1/observations/{id}/evaluate` | Evaluate against constitution |
| `GET` | `/v1/violations` | List violations (filter by severity/system/principle) |
| `POST` | `/v1/violations/{id}/remediate` | Apply remediation |
| `GET` | `/v1/systems/{id}/compliance` | System compliance score + trend |
| `POST` | `/v1/reports/generate` | Generate compliance report |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9909 --reload
```

> **Production note:** Replace rule-based violation detection with ML-powered semantic analysis; integrate with model registries for automated binding; add real-time streaming evaluation via Kafka.
