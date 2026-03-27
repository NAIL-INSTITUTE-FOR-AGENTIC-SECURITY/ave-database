# Regulation Simulator

**Phase 26 — Service 4 of 5 · Port `9908`**

Sandbox environment for testing regulatory changes against production-like
workloads before enforcement, with impact prediction, system compatibility
checks, and safe rollback.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Regulation Registry** | Register regulations with jurisdiction, domain (ai_governance/data_privacy/security/financial/healthcare/environmental), effective_date, requirements as structured rules, current_status (proposed/adopted/enforced/repealed) |
| **Sandbox Environments** | Create isolated sandboxes with sandbox_type (full_clone/lightweight/config_only), 5-state lifecycle (provisioning→ready→running→analysing→terminated), configurable TTL, resource limits |
| **Workload Simulation** | Define production-like workloads: workload_type (api_traffic/data_processing/model_inference/batch_job/user_interaction), volume (requests/sec), duration_minutes, data_profile (synthetic/anonymised/sample) |
| **Impact Prediction** | Pre-enforcement impact analysis per regulation: affected_systems count, compliance_gaps identified, estimated_remediation_hours, risk_level (critical/high/medium/low/none), cost_impact_estimate |
| **Compatibility Check** | Test regulation against current system config: check_type (technical_feasibility/policy_conflict/resource_requirement/timeline_feasibility), pass/fail per check with detail |
| **Simulation Execution** | Run workload against sandbox with regulation applied: capture metrics (latency_p50/p95/p99, error_rate, throughput, compliance_violations), compare against baseline (no regulation) |
| **A/B Comparison** | Side-by-side comparison of regulation variants: metric deltas, violation diffs, performance impact, recommendation (adopt/modify/reject) |
| **Rollback** | Revert sandbox to pre-regulation state; capture rollback reason and metrics at rollback point |
| **Report Generation** | Simulation report with executive_summary + metric_comparison + compliance_assessment + recommendation + risk_analysis |
| **Analytics** | Simulations by jurisdiction/domain, impact distribution, compatibility pass rates, avg simulation duration |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/regulations` | Register regulation |
| `GET` | `/v1/regulations` | List regulations |
| `POST` | `/v1/sandboxes` | Create sandbox |
| `GET` | `/v1/sandboxes` | List sandboxes |
| `GET` | `/v1/sandboxes/{id}` | Get sandbox detail |
| `PATCH` | `/v1/sandboxes/{id}/advance` | Advance sandbox state |
| `POST` | `/v1/sandboxes/{id}/simulate` | Run simulation |
| `POST` | `/v1/sandboxes/{id}/impact` | Predict regulation impact |
| `POST` | `/v1/sandboxes/{id}/compatibility` | Run compatibility checks |
| `POST` | `/v1/sandboxes/{id}/compare` | A/B comparison |
| `POST` | `/v1/sandboxes/{id}/rollback` | Rollback sandbox |
| `POST` | `/v1/sandboxes/{id}/report` | Generate report |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9908 --reload
```

> **Production note:** Replace simulated metrics with real sandbox infrastructure (Docker/K8s-based isolation); add integration with CI/CD pipelines for automated pre-deployment regulation testing.
