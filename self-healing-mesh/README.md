# Self-Healing Service Mesh

**Phase 23 — Service 1 of 5 · Port `9700`**

Autonomous service recovery with failure prediction, automatic restarts,
traffic rerouting, cascading failure prevention, and real-time health
topology awareness.

---

## Core Concepts

### Mesh Nodes
Each service in the mesh is a **node** with:
- **node_id** / **service_name** / **endpoint** / **region**
- **health_state**: `healthy` → `warning` → `degraded` → `failing` → `dead` → `recovering`
- **health_score** (0–100): composite metric from heartbeat, latency, error rate
- **restart_count** / **last_restart_at**

### Traffic Routes
Routes define how traffic flows between nodes:
- **source_node** → **target_node**, **weight** (0–1), **active** flag
- When a target degrades, weight auto-reduces; when dead, route deactivates

### Failure Prediction
Predictive health analysis using rolling windows:
- **heartbeat_miss_rate** — missed heartbeats over last N intervals
- **latency_trend** — slope of recent latency measurements (rising = warning)
- **error_rate_trend** — slope of error rates
- Prediction produces a **risk_score** (0–1) and recommended action

### Self-Healing Actions
| Action | Trigger | Description |
|--------|---------|-------------|
| `restart` | health_score < 30 | Automatic service restart |
| `reroute` | node degraded | Shift traffic to healthy peers |
| `isolate` | cascading risk | Remove node from mesh temporarily |
| `scale_up` | capacity pressure | Request additional instances |
| `restore` | node recovered | Reinstate node in mesh |

### Cascading Failure Prevention
When multiple nodes degrade simultaneously, the mesh:
1. Identifies the blast radius (connected nodes)
2. Applies circuit-breaking to affected routes
3. Triggers isolation of failing nodes
4. Gradually restores as nodes recover

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + mesh overview |
| `POST` | `/v1/nodes` | Register mesh node |
| `GET` | `/v1/nodes` | List nodes with filters |
| `GET` | `/v1/nodes/{id}` | Node detail |
| `POST` | `/v1/nodes/{id}/heartbeat` | Heartbeat with metrics |
| `POST` | `/v1/routes` | Create traffic route |
| `GET` | `/v1/routes` | List routes |
| `GET` | `/v1/nodes/{id}/predict` | Failure prediction |
| `POST` | `/v1/nodes/{id}/heal` | Trigger self-healing action |
| `GET` | `/v1/topology` | Full mesh topology |
| `GET` | `/v1/analytics` | Mesh analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9700
```

---

*Part of the NAIL Institute AVE Database — Phase 23: Autonomous Resilience & Self-Healing Infrastructure*
