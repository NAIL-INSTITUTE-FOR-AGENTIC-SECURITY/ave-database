# Cross-Domain Knowledge Fuser

**Phase 30 · Service 5 of 5 · Port 9929**

Synthesises security knowledge from multiple domains (network, endpoint, identity, cloud) into unified threat intelligence through cross-domain reasoning.

## Quick Start

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 9929
```

## Capabilities

| Capability | Description |
|---|---|
| Domain Registry | Register knowledge domains (6 types: network / endpoint / identity / cloud / application / physical) with schema descriptors, freshness requirements, and reliability rating 0-1 |
| Knowledge Fragment Ingestion | Ingest typed knowledge fragments (8 types: indicator / tactic / vulnerability / behaviour_pattern / policy_rule / threat_actor / attack_chain / mitigation) with domain source, confidence 0-1, and temporal validity |
| Cross-Domain Linking | Automatically link related fragments across domains using shared attributes (IPs, hashes, user IDs, CVEs, techniques); link types: correlates_with / enables / mitigates / contradicts / reinforces |
| Fusion Jobs | 5-state fusion lifecycle (queued → linking → reasoning → synthesised → published) with configurable fusion strategies: union / intersection / weighted_merge / conflict_resolution / temporal_priority |
| Conflict Resolution | Detect contradicting fragments across domains; 4 resolution strategies: domain_priority / confidence_weighted / temporal_latest / human_review; track resolution audit trail |
| Unified Intelligence Products | Generate fused intelligence products combining cross-domain fragments into coherent threat narratives with multi-domain evidence chains and aggregate confidence |
| Confidence Propagation | Aggregate confidence across linked fragments with domain reliability weighting; decay for indirect links; minimum evidence threshold for high-confidence assertions |
| Temporal Coherence | Enforce temporal validity windows; auto-expire stale fragments; detect temporal contradictions (new evidence invalidating older conclusions) |
| Coverage Analysis | Identify domain blind spots — areas where only single-domain evidence exists; recommend cross-domain enrichment targets |
| Analytics | Fragments by domain, link density, fusion success rate, conflict rate, coverage gaps |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/v1/domains` | Register knowledge domain |
| `GET` | `/v1/domains` | List domains |
| `POST` | `/v1/fragments` | Ingest knowledge fragment |
| `GET` | `/v1/fragments` | List fragments (filter by domain, type) |
| `GET` | `/v1/fragments/{id}` | Fragment detail with links |
| `POST` | `/v1/fragments/{id}/link` | Create cross-domain link |
| `POST` | `/v1/fusions` | Create fusion job |
| `GET` | `/v1/fusions` | List fusion jobs (filter by state) |
| `GET` | `/v1/fusions/{id}` | Fusion detail with intelligence product |
| `POST` | `/v1/fusions/{id}/execute` | Execute fusion |
| `GET` | `/v1/conflicts` | Unresolved cross-domain conflicts |
| `POST` | `/v1/conflicts/{id}/resolve` | Resolve conflict |
| `GET` | `/v1/coverage` | Domain coverage analysis |
| `GET` | `/v1/analytics` | Cross-domain fusion analytics |

## Design Notes

- In-memory stores — production would use knowledge graph (Neo4j / TigerGraph)
- Link detection uses shared attribute matching heuristics
- Confidence propagation applies domain reliability as multiplier
- Temporal validity enforced at query time; stale fragments flagged but retained for audit
