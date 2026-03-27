# Emergent Strategy Detector

**Phase 30 · Service 4 of 5 · Port 9928**

Monitors multi-agent interactions to identify emergent strategies, both beneficial and adversarial, that arise from agent collaboration patterns.

## Quick Start

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 9928
```

## Capabilities

| Capability | Description |
|---|---|
| Interaction Registry | Record agent-to-agent interactions (7 types: coordination / delegation / information_sharing / conflict / negotiation / resource_competition / alliance_formation) with outcome (positive / neutral / negative) and strength 0-1 |
| Pattern Detection | Detect recurring interaction patterns from interaction graphs; pattern types: clustering / specialisation / hierarchy_formation / free_riding / collusion / load_balancing / emergent_leadership |
| Strategy Classification | Classify detected strategies as beneficial / neutral / adversarial / unknown with confidence scoring; beneficial strategies promoted, adversarial strategies flagged |
| Temporal Analysis | Track strategy emergence over time windows; detect when strategies form, stabilise, or dissolve; lifecycle: emerging → active → stable → dissolving → extinct |
| Coalition Detection | Identify agent coalitions (subgroups with dense internal interactions); measure coalition stability, exclusivity, and influence on swarm behaviour |
| Free-Rider Detection | Identify agents that consume collective resources without proportional contribution; contribution ratio analysis |
| Collusion Detection | Detect coordinated adversarial behaviour: agents consistently voting together against swarm consensus with low diversity scores |
| Strategy Impact Assessment | Measure impact of detected strategies on overall swarm performance (throughput, accuracy, response time) |
| Intervention Recommendations | Auto-generated recommendations to encourage beneficial strategies or disrupt adversarial ones: role_reassignment / isolation / incentive_adjustment / coalition_break |
| Analytics | Strategy distribution, emergence rate, adversarial detection rate, intervention effectiveness |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/v1/interactions` | Record agent interaction |
| `GET` | `/v1/interactions` | List interactions (filter by type, agents) |
| `POST` | `/v1/detect-patterns` | Run pattern detection on interaction graph |
| `GET` | `/v1/strategies` | List detected strategies |
| `GET` | `/v1/strategies/{id}` | Strategy detail with lifecycle |
| `GET` | `/v1/strategies/{id}/impact` | Strategy impact assessment |
| `GET` | `/v1/coalitions` | Detected coalitions |
| `GET` | `/v1/free-riders` | Free-rider analysis |
| `GET` | `/v1/collusion-scan` | Collusion detection scan |
| `GET` | `/v1/interventions` | Recommended interventions |
| `GET` | `/v1/analytics` | Emergent strategy analytics |

## Design Notes

- In-memory interaction graph — production would use graph database
- Pattern detection uses frequency analysis and graph clustering heuristics
- Coalition detection via density analysis of interaction subgraphs
- Collusion scoring based on voting alignment + low contribution diversity
