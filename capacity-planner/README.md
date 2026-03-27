# Predictive Capacity Planner

**Phase 23 — Service 4 of 5 · Port `9703`**

ML-driven resource forecasting with auto-scaling recommendations, cost
optimisation, capacity reservation, and trend analysis across all
infrastructure tiers.

---

## Core Concepts

### Resources
A **resource** represents a scalable infrastructure component:
- **resource_id** / **name** / **resource_type** / **region**
- **current_capacity** / **min_capacity** / **max_capacity**
- **unit_cost_per_hour** / **currency**

### Resource Types
`compute` | `memory` | `storage` | `network` | `gpu` | `api_quota`

### Metric Ingestion
Time-series metrics are ingested per resource:
- **metric_name** (e.g., cpu_utilisation, memory_used, request_count)
- **value** / **timestamp**
- Rolling window retained for forecasting

### Forecasting
The planner uses exponential smoothing + trend decomposition:
1. Compute rolling average + trend slope
2. Project forward N hours
3. Identify when projected usage exceeds capacity threshold
4. Generate scaling recommendation

### Scaling Recommendations
| Action | Trigger |
|--------|---------|
| `scale_up` | Forecasted usage > 80% capacity |
| `scale_down` | Forecasted usage < 30% capacity for sustained period |
| `reserve` | Predictable periodic peak detected |
| `no_action` | Usage within comfortable bounds |

### Cost Optimisation
Each recommendation includes:
- **current_cost** / **projected_cost** / **savings_potential**
- **confidence** (0–1) based on forecast accuracy

### Capacity Reservations
Pre-book capacity for anticipated demand spikes:
- **start_at** / **end_at** / **reserved_capacity** / **status**

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/resources` | Register resource |
| `GET` | `/v1/resources` | List resources |
| `POST` | `/v1/resources/{id}/metrics` | Ingest metric |
| `GET` | `/v1/resources/{id}/forecast` | Get forecast |
| `GET` | `/v1/resources/{id}/recommendation` | Scaling recommendation |
| `POST` | `/v1/reservations` | Create capacity reservation |
| `GET` | `/v1/reservations` | List reservations |
| `GET` | `/v1/cost-report` | Cost optimisation report |
| `GET` | `/v1/analytics` | Capacity analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9703
```

---

*Part of the NAIL Institute AVE Database — Phase 23: Autonomous Resilience & Self-Healing Infrastructure*
