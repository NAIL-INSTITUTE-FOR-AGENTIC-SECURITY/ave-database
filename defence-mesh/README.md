# 🕸️ Self-Healing Defence Mesh

> Distributed defence network that autonomously detects, isolates, and recovers
> from compromised nodes without human intervention.

**Phase 13 · Item 1 · Port 8700**

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        SELF-HEALING DEFENCE MESH                        │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Topology │ Heart-   │ Quorum   │ Isolation│ Recovery │ Rebalance       │
│ Manager  │ beat     │ Consensus│ Engine   │ Engine   │ Orchestrator    │
│          │ Monitor  │          │          │          │                 │
├──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                         MESH FABRIC (gossip)                           │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Node A   │ Node B   │ Node C   │ Node D   │ …        │ Node N          │
│ (guard)  │ (monitor)│ (guard)  │ (router) │          │ (sentinel)      │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────┘
```

## Concepts

| Concept | Description |
|---------|-------------|
| **Mesh Node** | An individual defence component (guardrail, monitor, router, sentinel) |
| **Heartbeat** | Periodic liveness probe every node must answer within deadline |
| **Quorum** | Minimum healthy-node ratio before mesh declares degraded state |
| **Isolation** | Suspected-compromised node is fenced from mesh traffic |
| **Self-Heal** | Automatic node restart, replacement, or config rollback |
| **Rebalance** | Traffic and responsibility re-distribution after topology change |

## Key Features

1. **Autonomous Failure Detection** — Heartbeat + anomaly scoring identifies unhealthy nodes within seconds
2. **Byzantine-Tolerant Consensus** — Quorum-based voting prevents single-node false alarms
3. **Automatic Isolation** — Compromised or failing nodes are fenced before damage spreads
4. **Zero-Downtime Recovery** — Standby replicas promote automatically; config rollback on persistent failure
5. **Dynamic Rebalancing** — Defence workload redistributes across healthy nodes
6. **Partition Healing** — Split-brain detection and automatic reconciliation
7. **Full Audit Trail** — Every mesh event (join, leave, isolate, heal) is immutably logged
8. **Topology Visualization** — Real-time mesh graph with node states and edge health

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health |
| `GET` | `/v1/mesh/topology` | Current mesh topology |
| `POST` | `/v1/mesh/nodes` | Register a new node |
| `GET` | `/v1/mesh/nodes` | List all nodes with status |
| `GET` | `/v1/mesh/nodes/{id}` | Node details |
| `DELETE` | `/v1/mesh/nodes/{id}` | Deregister a node |
| `POST` | `/v1/mesh/nodes/{id}/heartbeat` | Report heartbeat |
| `POST` | `/v1/mesh/nodes/{id}/isolate` | Manually isolate a node |
| `POST` | `/v1/mesh/nodes/{id}/recover` | Trigger recovery for a node |
| `GET` | `/v1/mesh/quorum` | Quorum status |
| `GET` | `/v1/mesh/events` | Mesh event log |
| `POST` | `/v1/mesh/simulate-failure` | Inject synthetic failure for testing |
| `POST` | `/v1/mesh/rebalance` | Trigger manual rebalance |
| `GET` | `/v1/mesh/partitions` | Detect network partitions |
| `GET` | `/v1/mesh/analytics` | Mesh health analytics |

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 8700 --reload
```

Docs at http://localhost:8700/docs
