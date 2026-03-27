"""Trust Calibration Engine — Phase 25 Service 4 · Port 9903"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random, math

app = FastAPI(title="Trust Calibration Engine", version="0.25.4")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class EntityType(str, Enum):
    human = "human"
    ai = "ai"

class ExerciseType(str, Enum):
    prediction = "prediction"
    classification = "classification"
    risk_assessment = "risk_assessment"
    anomaly_detection = "anomaly_detection"
    decision_making = "decision_making"

class TrustEventType(str, Enum):
    successful_collaboration = "successful_collaboration"
    failed_task = "failed_task"
    accurate_prediction = "accurate_prediction"
    inaccurate_prediction = "inaccurate_prediction"
    override_accepted = "override_accepted"
    override_rejected = "override_rejected"
    calibration_completed = "calibration_completed"

TRUST_EVENT_DELTAS = {
    "successful_collaboration": 3.0,
    "failed_task": -5.0,
    "accurate_prediction": 4.0,
    "inaccurate_prediction": -4.0,
    "override_accepted": 2.0,
    "override_rejected": -2.0,
    "calibration_completed": 1.5,
}

# ── Models ───────────────────────────────────────────────────────────
class EntityCreate(BaseModel):
    name: str
    entity_type: EntityType
    role: str = ""
    department: str = ""
    capabilities: list[str] = []

class TrustPairCreate(BaseModel):
    trustor_id: str
    trustee_id: str

class TrustEventCreate(BaseModel):
    event_type: TrustEventType
    context: str = ""

class CalibrationCreate(BaseModel):
    exercise_type: ExerciseType
    participant_ids: list[str]
    scenario_description: str
    target_skill: str = "general"

class PredictionSubmit(BaseModel):
    entity_id: str
    predicted_outcome: str
    confidence: float = Field(0.5, ge=0, le=1)

class CalibrationResolve(BaseModel):
    actual_outcome: str

# ── Stores ───────────────────────────────────────────────────────────
entities: dict[str, dict] = {}
trust_pairs: dict[str, dict] = {}
calibrations: dict[str, dict] = {}
trust_events: list[dict] = []

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Trust Dimensions ─────────────────────────────────────────────────
DIMENSION_WEIGHTS = {
    "competence": 0.30,
    "reliability": 0.25,
    "transparency": 0.20,
    "predictability": 0.15,
    "benevolence": 0.10,
}

def _init_dimensions():
    return {dim: 50.0 for dim in DIMENSION_WEIGHTS}

def _composite_score(dims: dict) -> float:
    return round(sum(dims[d] * DIMENSION_WEIGHTS[d] for d in DIMENSION_WEIGHTS), 2)

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "trust-calibration-engine",
        "status": "healthy",
        "version": "0.25.4",
        "entities": len(entities),
        "trust_pairs": len(trust_pairs),
        "calibrations": len(calibrations),
    }

# ── Entity CRUD ──────────────────────────────────────────────────────
@app.post("/v1/entities", status_code=201)
def create_entity(body: EntityCreate):
    eid = str(uuid.uuid4())
    rec = {
        "id": eid,
        **body.model_dump(),
        "accuracy_history": [],
        "created_at": _now(),
    }
    entities[eid] = rec
    return rec

@app.get("/v1/entities")
def list_entities(entity_type: Optional[EntityType] = None):
    out = list(entities.values())
    if entity_type:
        out = [e for e in out if e["entity_type"] == entity_type]
    return out

# ── Trust Pairs ──────────────────────────────────────────────────────
@app.post("/v1/trust-pairs", status_code=201)
def create_trust_pair(body: TrustPairCreate):
    if body.trustor_id not in entities:
        raise HTTPException(404, "Trustor not found")
    if body.trustee_id not in entities:
        raise HTTPException(404, "Trustee not found")
    pid = str(uuid.uuid4())
    rec = {
        "id": pid,
        "trustor_id": body.trustor_id,
        "trustee_id": body.trustee_id,
        "dimensions": _init_dimensions(),
        "composite_score": 50.0,
        "event_count": 0,
        "created_at": _now(),
        "last_event_at": _now(),
    }
    trust_pairs[pid] = rec
    return rec

@app.get("/v1/trust-pairs")
def list_trust_pairs():
    return list(trust_pairs.values())

@app.get("/v1/trust-pairs/{pid}")
def get_trust_pair(pid: str):
    if pid not in trust_pairs:
        raise HTTPException(404, "Trust pair not found")
    return trust_pairs[pid]

# ── Trust Events ─────────────────────────────────────────────────────
@app.post("/v1/trust-pairs/{pid}/event")
def log_trust_event(pid: str, body: TrustEventCreate):
    if pid not in trust_pairs:
        raise HTTPException(404, "Trust pair not found")
    tp = trust_pairs[pid]
    delta = TRUST_EVENT_DELTAS.get(body.event_type, 0)

    # Apply delta to relevant dimensions
    if body.event_type in ("accurate_prediction", "successful_collaboration"):
        tp["dimensions"]["competence"] = min(100, tp["dimensions"]["competence"] + delta)
        tp["dimensions"]["reliability"] = min(100, tp["dimensions"]["reliability"] + delta * 0.5)
    elif body.event_type in ("inaccurate_prediction", "failed_task"):
        tp["dimensions"]["competence"] = max(0, tp["dimensions"]["competence"] + delta)
        tp["dimensions"]["reliability"] = max(0, tp["dimensions"]["reliability"] + delta * 0.5)
    elif body.event_type in ("override_accepted",):
        tp["dimensions"]["transparency"] = min(100, tp["dimensions"]["transparency"] + delta)
    elif body.event_type in ("override_rejected",):
        tp["dimensions"]["predictability"] = max(0, tp["dimensions"]["predictability"] + delta)
    else:
        for dim in tp["dimensions"]:
            tp["dimensions"][dim] = max(0, min(100, tp["dimensions"][dim] + delta * 0.3))

    tp["composite_score"] = _composite_score(tp["dimensions"])
    tp["event_count"] += 1
    tp["last_event_at"] = _now()

    evt = {"trust_pair_id": pid, **body.model_dump(), "delta": delta, "new_composite": tp["composite_score"], "timestamp": _now()}
    trust_events.append(evt)
    return evt

# ── Calibration Exercises ────────────────────────────────────────────
@app.post("/v1/calibrations", status_code=201)
def create_calibration(body: CalibrationCreate):
    for pid in body.participant_ids:
        if pid not in entities:
            raise HTTPException(404, f"Entity {pid} not found")
    cid = str(uuid.uuid4())
    rec = {
        "id": cid,
        **body.model_dump(),
        "state": "active",
        "predictions": {},
        "actual_outcome": None,
        "created_at": _now(),
        "resolved_at": None,
    }
    calibrations[cid] = rec
    return rec

@app.post("/v1/calibrations/{cid}/respond")
def submit_prediction(cid: str, body: PredictionSubmit):
    if cid not in calibrations:
        raise HTTPException(404, "Calibration not found")
    c = calibrations[cid]
    if c["state"] != "active":
        raise HTTPException(400, "Calibration not active")
    c["predictions"][body.entity_id] = {
        "predicted_outcome": body.predicted_outcome,
        "confidence": body.confidence,
        "submitted_at": _now(),
    }
    return {"status": "prediction_recorded", "entity_id": body.entity_id}

@app.post("/v1/calibrations/{cid}/resolve")
def resolve_calibration(cid: str, body: CalibrationResolve):
    if cid not in calibrations:
        raise HTTPException(404, "Calibration not found")
    c = calibrations[cid]
    c["actual_outcome"] = body.actual_outcome
    c["state"] = "resolved"
    c["resolved_at"] = _now()

    results = []
    for eid, pred in c["predictions"].items():
        correct = pred["predicted_outcome"].lower().strip() == body.actual_outcome.lower().strip()
        over_confident = pred["confidence"] > 0.8 and not correct
        under_confident = pred["confidence"] < 0.3 and correct

        # Update entity accuracy
        if eid in entities:
            entities[eid]["accuracy_history"].append({"correct": correct, "confidence": pred["confidence"], "timestamp": _now()})

        results.append({
            "entity_id": eid,
            "correct": correct,
            "confidence": pred["confidence"],
            "over_confident": over_confident,
            "under_confident": under_confident,
        })

    return {"calibration_id": cid, "actual_outcome": body.actual_outcome, "results": results}

# ── Trust Network ────────────────────────────────────────────────────
@app.get("/v1/trust-network")
def trust_network():
    nodes = [{"id": e["id"], "name": e["name"], "type": e["entity_type"]} for e in entities.values()]
    edges = [{"id": tp["id"], "from": tp["trustor_id"], "to": tp["trustee_id"], "score": tp["composite_score"]} for tp in trust_pairs.values()]
    scores = [tp["composite_score"] for tp in trust_pairs.values()]
    return {
        "nodes": nodes,
        "edges": edges,
        "metrics": {
            "avg_trust": round(sum(scores) / max(len(scores), 1), 2),
            "min_trust": min(scores) if scores else 0,
            "max_trust": max(scores) if scores else 0,
            "pair_count": len(edges),
        },
    }

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    scores = [tp["composite_score"] for tp in trust_pairs.values()]
    by_event_type = {}
    for e in trust_events:
        by_event_type[e["event_type"]] = by_event_type.get(e["event_type"], 0) + 1
    cal_states = {}
    for c in calibrations.values():
        cal_states[c["state"]] = cal_states.get(c["state"], 0) + 1
    return {
        "total_entities": len(entities),
        "total_trust_pairs": len(trust_pairs),
        "avg_composite_trust": round(sum(scores) / max(len(scores), 1), 2),
        "trust_events": len(trust_events),
        "events_by_type": by_event_type,
        "calibrations": len(calibrations),
        "calibrations_by_state": cal_states,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9903)
