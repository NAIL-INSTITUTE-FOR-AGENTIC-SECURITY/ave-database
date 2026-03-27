# Continuous Defence Learning Loop

**Phase 22 — Service 2 of 5 · Port `9601`**

Closed-loop defence adaptation that ingests real incident data, retrains
detection models, measures defence drift over time, and continuously improves
defence posture through automated feedback cycles.

---

## Core Concepts

### Learning Cycles
A **cycle** is one complete iteration: ingest incidents → extract features →
retrain model → evaluate → promote or rollback.

### Model Registry
Each detection model is versioned. The registry tracks:
- **model_id** / **version** / **algorithm** / **feature_set**
- **accuracy**, **precision**, **recall**, **f1_score** (evaluation metrics)
- **state**: `training` → `evaluating` → `candidate` → `promoted` → `retired`

### Defence Drift Detection
Drift is measured by comparing current model performance against a baseline.
Three drift types:
- **concept_drift** — underlying attack patterns have changed
- **data_drift** — input feature distributions have shifted
- **performance_drift** — model metrics have degraded beyond threshold

### Feedback Signals
| Signal | Source | Usage |
|--------|--------|-------|
| Incident outcomes | Incident Commander | True positive / false negative |
| Detection latency | Observability Fabric | Speed of detection |
| Analyst verdicts | Human review | Label correction |
| Red-team results | Red-Team Engine | New attack patterns |

---

## Data Model

### Cycle States
`collecting` → `training` → `evaluating` → `promoting` → `completed` | `rolled_back`

### Incident Samples
```
{
  sample_id, source_incident_id, ave_category,
  features: { ... extracted feature vector ... },
  label: "true_positive" | "false_positive" | "false_negative" | "true_negative",
  ingested_at
}
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/samples` | Ingest labelled incident sample |
| `GET` | `/v1/samples` | List samples with filters |
| `POST` | `/v1/models` | Register a detection model |
| `GET` | `/v1/models` | List models |
| `POST` | `/v1/cycles` | Start a learning cycle |
| `GET` | `/v1/cycles` | List cycles |
| `POST` | `/v1/cycles/{id}/evaluate` | Evaluate candidate model |
| `POST` | `/v1/cycles/{id}/promote` | Promote best candidate |
| `GET` | `/v1/drift` | Drift analysis |
| `GET` | `/v1/analytics` | Learning analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9601
```

---

*Part of the NAIL Institute AVE Database — Phase 22: Adaptive Learning & Evolutionary Defence*
