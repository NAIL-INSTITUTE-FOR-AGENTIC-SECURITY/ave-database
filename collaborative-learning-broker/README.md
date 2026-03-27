# Collaborative Learning Broker

**Phase 30 · Service 2 of 5 · Port 9926**

Manages federated and collaborative learning sessions across distributed security agents while preserving data privacy and preventing model poisoning.

## Quick Start

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 9926
```

## Capabilities

| Capability | Description |
|---|---|
| Participant Registry | Register learning participants (6 types: endpoint_agent / network_monitor / cloud_sentinel / identity_guardian / threat_hunter / siem_collector) with data_size_estimate, privacy_level (public / anonymised / differential_privacy / encrypted), and trust_score 0-1 |
| Session Lifecycle | 6-state session lifecycle (created → recruiting → training → aggregating → validating → completed/failed) with configurable min/max participants and rounds |
| Learning Modes | 4 federated learning modes: federated_averaging / secure_aggregation / gossip_protocol / split_learning — each with distinct aggregation semantics |
| Round Management | Per-round gradient/update submission from participants with simulated local training metrics (loss, accuracy, samples_used) |
| Aggregation Engine | Weighted aggregation across participant updates using trust_score × data_weight; outlier detection for poisoning attempts (z-score > 2.5 from mean) |
| Poisoning Detection | Flags anomalous updates as potential model poisoning; quarantines suspicious participants; tracks poisoning attempt history |
| Privacy Accounting | Cumulative privacy budget tracking (epsilon accumulation per round); alerts when privacy budget approaches exhaustion threshold |
| Model Versioning | Global model version incremented each round with accuracy/loss tracking; rollback to previous version if regression detected |
| Convergence Monitoring | Tracks loss trajectory across rounds; detects convergence (delta < threshold) or divergence (loss increasing 3+ consecutive rounds) |
| Analytics | Sessions by mode, avg rounds to convergence, poisoning detection rate, privacy budget usage |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/v1/participants` | Register participant |
| `GET` | `/v1/participants` | List participants (filter by type) |
| `POST` | `/v1/sessions` | Create learning session |
| `GET` | `/v1/sessions` | List sessions (filter by state) |
| `GET` | `/v1/sessions/{id}` | Session detail with round history |
| `POST` | `/v1/sessions/{id}/join` | Participant joins session |
| `PATCH` | `/v1/sessions/{id}/advance` | Advance session state |
| `POST` | `/v1/sessions/{id}/rounds/{n}/submit` | Submit round update |
| `POST` | `/v1/sessions/{id}/rounds/{n}/aggregate` | Aggregate round updates |
| `GET` | `/v1/sessions/{id}/convergence` | Convergence analysis |
| `GET` | `/v1/sessions/{id}/privacy` | Privacy budget status |
| `GET` | `/v1/analytics` | Collaborative learning analytics |

## Design Notes

- In-memory stores — production would use secure enclaves and MPC
- Simulated gradient updates — real deployment would use actual model parameters
- Privacy budget is tracked per-session with configurable epsilon threshold
- Poisoning detection uses statistical outlier analysis on update magnitudes
