# Swarm Consensus Engine

**Phase 30 · Service 1 of 5 · Port 9925**

Distributed consensus mechanism for multi-agent security decisions, enabling agent swarms to collectively assess threats and reach agreement through configurable voting protocols.

## Quick Start

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 9925
```

## Capabilities

| Capability | Description |
|---|---|
| Agent Registry | Register swarm participants (8 types: threat_detector / anomaly_analyser / policy_enforcer / response_coordinator / intel_gatherer / vulnerability_scanner / access_monitor / forensic_investigator) with weight, reliability score 0-1, and domain specialisation |
| Proposal Lifecycle | 5-state proposal lifecycle (submitted → voting → tallying → decided → archived) with configurable quorum and deadline |
| Voting Protocols | 6 protocol types: simple_majority / supermajority_66 / supermajority_75 / unanimous / weighted_majority / ranked_choice — each with distinct threshold rules |
| Vote Casting | Agents cast votes (approve / reject / abstain) with confidence 0-1 and optional rationale; weight × confidence × reliability = effective vote power |
| Quorum Enforcement | Configurable minimum participation threshold; proposals cannot be decided without quorum |
| Tally Engine | Real-time tally computation with effective weight aggregation, quorum check, and automatic decision based on protocol rules |
| Dissent Analysis | Identifies dissenting agents, calculates dissent strength, and flags high-confidence dissenters for review |
| Deadlock Detection | Detects voting deadlocks (neither side meets threshold after all votes in) with auto-escalation suggestions |
| Voting History | Per-agent voting history with consistency tracking and flip detection |
| Analytics | Protocol usage, avg participation rate, consensus speed, dissent patterns |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/v1/agents` | Register swarm agent |
| `GET` | `/v1/agents` | List agents (filter by type) |
| `GET` | `/v1/agents/{id}` | Agent detail with voting history |
| `POST` | `/v1/proposals` | Create consensus proposal |
| `GET` | `/v1/proposals` | List proposals (filter by state) |
| `GET` | `/v1/proposals/{id}` | Proposal detail |
| `POST` | `/v1/proposals/{id}/vote` | Cast vote on proposal |
| `POST` | `/v1/proposals/{id}/tally` | Compute tally and decide |
| `GET` | `/v1/proposals/{id}/dissent` | Dissent analysis |
| `GET` | `/v1/proposals/{id}/deadlock` | Deadlock detection |
| `GET` | `/v1/analytics` | Swarm consensus analytics |

## Design Notes

- In-memory stores — production would use distributed state (Raft/PBFT)
- Vote immutability — once cast, votes cannot be changed
- Weight × confidence × reliability = effective vote power
- Quorum is checked before any decision is rendered
