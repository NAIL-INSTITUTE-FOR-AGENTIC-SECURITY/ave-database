# Agent Reputation System

**Phase 30 · Service 3 of 5 · Port 9927**

Tracks agent reliability, accuracy, and trustworthiness over time to weight contributions in collective decision-making and identify compromised agents.

## Quick Start

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 9927
```

## Capabilities

| Capability | Description |
|---|---|
| Agent Registry | Register agents (8 types: detector / classifier / responder / analyst / scanner / monitor / orchestrator / advisor) with initial reputation 50.0 (0-100 scale), domain, and deployment context |
| Event Recording | Record reputation events (7 types: correct_detection / false_positive / false_negative / timely_response / delayed_response / accurate_classification / inaccurate_classification) with magnitude 0-1 and context |
| Reputation Scoring | Rolling reputation calculation using exponential decay weighting (recent events weighted more heavily); 5 tiers: exemplary ≥ 85 / trusted ≥ 70 / neutral ≥ 50 / suspect ≥ 30 / compromised < 30 |
| Trend Analysis | Reputation trajectory over time windows (7/14/30 day) with slope detection: improving / stable / declining / volatile |
| Anomaly Detection | Detects sudden reputation drops (> 15 points in 24 hours) or erratic behaviour (high variance in recent events) flagging potential compromise |
| Trust Decay | Idle agents experience gradual trust decay towards neutral (0.1 points per inactivity period) to prevent stale high-trust agents |
| Peer Comparison | Rank agents within same type; percentile scoring; identify top/bottom performers |
| Compromise Detection | Multi-signal compromise detection: sudden accuracy drop + pattern change + peer divergence → quarantine recommendation |
| Rehabilitation Tracking | Quarantined agents can earn reputation back through supervised probationary events with reduced weight |
| Analytics | Tier distribution, avg reputation by type, compromise rate, rehabilitation success rate |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/v1/agents` | Register agent |
| `GET` | `/v1/agents` | List agents (filter by type, tier) |
| `GET` | `/v1/agents/{id}` | Agent detail with reputation history |
| `POST` | `/v1/agents/{id}/events` | Record reputation event |
| `GET` | `/v1/agents/{id}/trend` | Reputation trend analysis |
| `GET` | `/v1/agents/{id}/anomalies` | Anomaly detection for agent |
| `PATCH` | `/v1/agents/{id}/quarantine` | Quarantine/unquarantine agent |
| `GET` | `/v1/rankings` | Agent rankings by reputation |
| `GET` | `/v1/compromise-scan` | Scan all agents for compromise indicators |
| `GET` | `/v1/analytics` | Reputation system analytics |

## Design Notes

- In-memory stores — production would use persistent time-series database
- Exponential decay weighting ensures recent behaviour matters more
- 5-tier system maps directly to vote weight multipliers in Swarm Consensus Engine
- Quarantine status propagates to other Phase 30 services for collective decision exclusion
