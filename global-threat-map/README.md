# 🌍 Real-Time Global Threat Map

> Live geospatial visualisation of agentic AI threats worldwide with heat maps,
> attack flow animations, and regional intelligence overlays.

**Phase 13 · Item 3 · Port 8702**

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       REAL-TIME GLOBAL THREAT MAP                         │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ Ingestion│ Geo      │ Heat Map │ Attack   │ Regional │ WebSocket           │
│ Pipeline │ Resolver │ Engine   │ Flow     │ Intel    │ Broadcaster         │
│          │          │          │ Tracker  │ Overlay  │                     │
├──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────────┤
│                         EVENT STREAM BUS                                  │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ Live Feed│ Federated│ Predict- │ Defence  │ Red Team │ External            │
│ API      │ Intel    │ ive Eng. │ Mesh     │ Agent    │ Feeds               │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────────┘
```

## Key Features

1. **Live Threat Ingestion** — Aggregates threat events from internal services and external feeds
2. **Geospatial Resolution** — Maps threat origins and targets to coordinates with city/country/region
3. **Heat Map Generation** — Density-based heat map of threat concentration by region
4. **Attack Flow Visualization** — Source → target attack paths animated on the map
5. **Regional Intelligence** — Threat summaries, top categories, and trend data per region
6. **Alert Zones** — Configurable watch zones with threshold-based alerting
7. **Time-Series Replay** — Historical threat map state at any past timestamp
8. **WebSocket Broadcasting** — Real-time push of new threats to connected dashboards

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health |
| `POST` | `/v1/threats` | Ingest a threat event |
| `GET` | `/v1/threats` | List threats (filtered, paginated) |
| `GET` | `/v1/threats/{id}` | Threat event details |
| `GET` | `/v1/map/heatmap` | Heat map data (GeoJSON) |
| `GET` | `/v1/map/flows` | Attack flow paths |
| `GET` | `/v1/map/regions` | Regional threat summaries |
| `GET` | `/v1/map/regions/{code}` | Detailed region intelligence |
| `POST` | `/v1/map/alert-zones` | Create alert zone |
| `GET` | `/v1/map/alert-zones` | List alert zones |
| `GET` | `/v1/map/alerts` | Triggered alerts |
| `GET` | `/v1/map/timeline` | Time-series threat counts |
| `GET` | `/v1/map/replay` | Historical map state at timestamp |
| `GET` | `/v1/map/analytics` | Global analytics |

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 8702 --reload
```

Docs at http://localhost:8702/docs
