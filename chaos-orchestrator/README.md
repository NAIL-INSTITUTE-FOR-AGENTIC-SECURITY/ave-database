# Chaos Engineering Orchestrator

**Phase 23 — Service 2 of 5 · Port `9701`**

Automated fault injection framework with blast radius control, steady-state
validation, experiment scheduling, and automated rollback on safety
violations.

---

## Core Concepts

### Experiments
A **chaos experiment** defines:
- **hypothesis** — expected system behaviour under fault
- **fault_type** — the kind of failure injected
- **target_services** — which services are affected
- **blast_radius** — maximum allowed impact scope
- **steady_state** — metrics that must remain within bounds
- **duration_seconds** — how long the fault is active
- **rollback_on_violation** — automatic abort if steady-state breached

### Fault Types
| Fault | Description |
|-------|-------------|
| `latency_injection` | Add artificial delay to target |
| `error_injection` | Force HTTP 500 responses |
| `cpu_stress` | Simulate CPU saturation |
| `memory_pressure` | Simulate memory exhaustion |
| `network_partition` | Simulate network split |
| `dependency_failure` | Kill upstream dependency |
| `clock_skew` | Simulate time drift |
| `disk_pressure` | Simulate disk I/O bottleneck |

### Experiment States
`draft` → `scheduled` → `running` → `validating` → `completed` | `aborted` | `rolled_back`

### Steady-State Validation
Before, during, and after fault injection, the orchestrator checks:
- **metric_name** (e.g., error_rate, p99_latency, availability)
- **operator** (lt, gt, eq, lte, gte)
- **threshold** value
- If any check fails during experiment → automatic rollback

### Blast Radius Control
- **max_affected_services** — cap on services impacted
- **max_error_rate** — abort if error rate exceeds this
- **geographic_scope** — limit to specific regions

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/experiments` | Create experiment |
| `GET` | `/v1/experiments` | List experiments |
| `GET` | `/v1/experiments/{id}` | Experiment detail |
| `POST` | `/v1/experiments/{id}/run` | Execute experiment |
| `POST` | `/v1/experiments/{id}/abort` | Abort running experiment |
| `GET` | `/v1/experiments/{id}/results` | Experiment results |
| `POST` | `/v1/schedules` | Schedule recurring experiment |
| `GET` | `/v1/schedules` | List schedules |
| `GET` | `/v1/analytics` | Chaos analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9701
```

---

*Part of the NAIL Institute AVE Database — Phase 23: Autonomous Resilience & Self-Healing Infrastructure*
