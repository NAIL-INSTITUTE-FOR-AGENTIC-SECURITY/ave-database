# 🐝 Collective Intelligence Swarm

> Decentralised swarm intelligence system where autonomous defence agents
> across organisations collaborate to detect, analyse, and respond to
> novel threats in real-time without central coordination.

## Overview

The Collective Intelligence Swarm implements stigmergic communication
and emergent behaviour patterns that allow distributed defence agents
to self-organise into threat response formations.  Each agent operates
autonomously with local information, yet the swarm collectively
achieves global threat awareness through pheromone-inspired signalling,
consensus protocols, and adaptive specialisation.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                  Collective Intelligence Swarm                 │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ Swarm    │  │ Agent    │  │ Signal   │  │ Formation    │ │
│  │ Registry │  │ Runtime  │  │ Network  │  │ Manager      │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │
│       │              │              │               │         │
│  ┌────▼──────────────▼──────────────▼───────────────▼───────┐ │
│  │              Stigmergic Communication Layer               │ │
│  │  Pheromone Trails │ Consensus Protocol │ Quorum Voting   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Adaptive │  │ Threat       │  │ Emergence│  │ Swarm    │ │
│  │ Speciali-│  │ Aggregation  │  │ Detector │  │ Analytics│ │
│  │ sation   │  │ Engine       │  │          │  │          │ │
│  └──────────┘  └──────────────┘  └──────────┘  └──────────┘ │
└───────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Stigmergic Signals** | Pheromone-inspired threat/safe/rally/retreat signals with decay |
| **Swarm Formations** | Hunting, defensive wall, scouting, patrol, rapid response patterns |
| **Adaptive Specialisation** | Agents dynamically specialise based on swarm needs |
| **Quorum Consensus** | Decentralised voting on threat classification and response |
| **Emergent Behaviour** | Global coordination from local-only agent interactions |
| **Threat Aggregation** | Distributed evidence collection and confidence building |
| **Signal Decay** | Pheromone evaporation ensuring freshness of intelligence |
| **Formation Triggers** | Auto-formation based on signal density thresholds |
| **Agent Roles** | Scout, sentinel, responder, analyst, coordinator, healer |
| **Swarm Health** | Aggregate fitness, diversity index, signal entropy metrics |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Swarm health and agent count |
| `POST` | `/v1/agents` | Register a new swarm agent |
| `GET` | `/v1/agents` | List swarm agents |
| `GET` | `/v1/agents/{agent_id}` | Get agent status and specialisation |
| `POST` | `/v1/signals/emit` | Emit a stigmergic signal |
| `GET` | `/v1/signals` | Read current signal landscape |
| `POST` | `/v1/signals/decay` | Trigger signal decay cycle |
| `POST` | `/v1/formations` | Create / trigger a swarm formation |
| `GET` | `/v1/formations` | List active formations |
| `POST` | `/v1/consensus` | Initiate a quorum vote |
| `GET` | `/v1/consensus` | List consensus rounds |
| `GET` | `/v1/emergence` | Detect emergent patterns |
| `GET` | `/v1/analytics` | Swarm-wide analytics |

## Running

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 8901
```

## Port

| Service | Port |
|---------|------|
| Collective Intelligence Swarm | **8901** |

## Production Notes

- Replace in-memory stores with **Redis Streams** + **CockroachDB**
- Deploy agents as **independent microservices** with gRPC mesh
- Add real **distributed consensus** (Raft / PBFT)
- Integrate with real threat detection pipelines
