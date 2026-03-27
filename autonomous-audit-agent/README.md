# Autonomous Audit Agent

**Phase 26 — Service 2 of 5 · Port `9906`**

Self-directed AI auditor that continuously monitors system behaviour,
generates audit reports, flags anomalies, and triggers remediation workflows
without human initiation.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Audit Target Registry** | Register systems to audit with target_type (api_service/database/ai_model/pipeline/infrastructure), audit_domains (security/compliance/performance/data_quality/access), monitoring_interval_minutes |
| **Audit Campaigns** | Auto-generated or manual audit campaigns with 6 campaign types (scheduled/continuous/triggered/spot_check/deep_dive/post_incident), 5-state lifecycle (planned→running→analysing→reporting→closed) |
| **Probe System** | Configurable probes per target: probe_type (health_check/log_analysis/config_drift/permission_scan/data_flow_trace/model_drift/latency_profile), expected_result, threshold, auto_schedule |
| **Anomaly Detection** | Simulated statistical anomaly detection: z-score against rolling baseline, configurable sensitivity (low/medium/high/critical), anomaly categories (spike/drift/pattern_break/missing_data/threshold_breach) |
| **Finding Management** | Auto-generated findings from probe results: finding_type (violation/anomaly/warning/observation/recommendation), severity (critical/high/medium/low/info), evidence_refs, affected_components |
| **Auto-Remediation** | Trigger remediation for known finding patterns: remediation_type (auto_fix/escalate/quarantine/notify/log_only), approval_required flag for high-severity, execution tracking |
| **Report Generation** | Auto-generated audit reports: executive_summary + detailed_findings + risk_score (0-100) + recommendations + compliance_mapping; 3 formats (summary/detailed/regulatory) |
| **Continuous Monitoring** | Background monitoring with configurable intervals; alert on threshold breach; escalation on repeated violations |
| **Analytics** | Campaigns by state/type, findings by severity/type, anomaly trends, remediation success rates, risk score distribution |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/targets` | Register audit target |
| `GET` | `/v1/targets` | List targets |
| `POST` | `/v1/campaigns` | Create audit campaign |
| `GET` | `/v1/campaigns` | List campaigns |
| `GET` | `/v1/campaigns/{id}` | Get campaign detail |
| `PATCH` | `/v1/campaigns/{id}/advance` | Advance campaign state |
| `POST` | `/v1/campaigns/{id}/probe` | Run probe against target |
| `GET` | `/v1/findings` | List findings (filter by severity/type/target) |
| `POST` | `/v1/findings/{id}/remediate` | Trigger remediation |
| `POST` | `/v1/campaigns/{id}/report` | Generate audit report |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9906 --reload
```

> **Production note:** Replace simulated probes with real infrastructure integrations (Prometheus/Grafana/CloudWatch); add webhook-based alert delivery.
