"""
Continuous Defence Learning Loop — Phase 22 Service 2 of 5
Port: 9601

Closed-loop defence adaptation ingesting real incident data, retraining
detection models, measuring defence drift, and continuously improving
defence posture through automated feedback cycles.
"""

from __future__ import annotations

import math
import random
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SampleLabel(str, Enum):
    true_positive = "true_positive"
    false_positive = "false_positive"
    false_negative = "false_negative"
    true_negative = "true_negative"


class ModelState(str, Enum):
    training = "training"
    evaluating = "evaluating"
    candidate = "candidate"
    promoted = "promoted"
    retired = "retired"


class CycleState(str, Enum):
    collecting = "collecting"
    training = "training"
    evaluating = "evaluating"
    promoting = "promoting"
    completed = "completed"
    rolled_back = "rolled_back"


class DriftType(str, Enum):
    concept_drift = "concept_drift"
    data_drift = "data_drift"
    performance_drift = "performance_drift"


class Algorithm(str, Enum):
    random_forest = "random_forest"
    gradient_boosting = "gradient_boosting"
    neural_network = "neural_network"
    svm = "svm"
    ensemble = "ensemble"


AVE_CATEGORIES: list[str] = [
    "prompt_injection", "tool_misuse", "memory_poisoning",
    "goal_hijacking", "identity_spoofing", "privilege_escalation",
    "data_exfiltration", "resource_exhaustion", "multi_agent_manipulation",
    "context_overflow", "guardrail_bypass", "output_manipulation",
    "supply_chain_compromise", "model_extraction", "reward_hacking",
    "capability_elicitation", "alignment_subversion", "delegation_abuse",
]

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class SampleCreate(BaseModel):
    source_incident_id: str = ""
    ave_category: str = ""
    features: Dict[str, Any] = Field(default_factory=dict)
    label: SampleLabel = SampleLabel.true_positive
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SampleRecord(SampleCreate):
    sample_id: str
    ingested_at: str


class ModelCreate(BaseModel):
    name: str
    algorithm: Algorithm = Algorithm.ensemble
    feature_set: List[str] = Field(default_factory=list)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class ModelMetrics(BaseModel):
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0


class ModelRecord(ModelCreate):
    model_id: str
    version: int = 1
    state: ModelState = ModelState.training
    metrics: ModelMetrics = Field(default_factory=ModelMetrics)
    training_sample_count: int = 0
    baseline_metrics: Optional[ModelMetrics] = None
    created_at: str
    updated_at: str


class CycleCreate(BaseModel):
    name: str
    model_id: str
    min_samples: int = Field(default=10, ge=1)
    performance_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    description: str = ""


class CycleRecord(CycleCreate):
    cycle_id: str
    state: CycleState = CycleState.collecting
    samples_collected: int = 0
    candidate_model_id: Optional[str] = None
    evaluation_result: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

samples: Dict[str, SampleRecord] = {}
models: Dict[str, ModelRecord] = {}
cycles: Dict[str, CycleRecord] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _add_event(cycle: CycleRecord, event: str, detail: str = ""):
    cycle.events.append({"event": event, "detail": detail, "timestamp": _now()})
    cycle.updated_at = _now()


# ---------------------------------------------------------------------------
# Simulated Training / Evaluation
# ---------------------------------------------------------------------------

def _simulate_training(model: ModelRecord, sample_count: int) -> None:
    """Simulate model training — in production this calls ML pipeline."""
    base_acc = 0.7 + min(sample_count / 500, 0.25)
    noise = random.uniform(-0.05, 0.05)
    model.metrics.accuracy = round(min(max(base_acc + noise, 0.0), 1.0), 4)
    model.metrics.precision = round(min(max(base_acc + random.uniform(-0.08, 0.08), 0.0), 1.0), 4)
    model.metrics.recall = round(min(max(base_acc + random.uniform(-0.08, 0.08), 0.0), 1.0), 4)
    p, r = model.metrics.precision, model.metrics.recall
    model.metrics.f1_score = round(2 * p * r / max(p + r, 0.001), 4)
    model.training_sample_count = sample_count
    model.state = ModelState.evaluating
    model.updated_at = _now()


def _detect_drift(model: ModelRecord) -> List[Dict[str, Any]]:
    """Compare current metrics against baseline to detect drift."""
    drifts: List[Dict[str, Any]] = []
    if not model.baseline_metrics:
        return drifts
    bl = model.baseline_metrics
    cur = model.metrics
    if bl.accuracy - cur.accuracy > 0.1:
        drifts.append({
            "type": DriftType.performance_drift.value,
            "metric": "accuracy",
            "baseline": bl.accuracy,
            "current": cur.accuracy,
            "delta": round(cur.accuracy - bl.accuracy, 4),
        })
    if bl.f1_score - cur.f1_score > 0.1:
        drifts.append({
            "type": DriftType.performance_drift.value,
            "metric": "f1_score",
            "baseline": bl.f1_score,
            "current": cur.f1_score,
            "delta": round(cur.f1_score - bl.f1_score, 4),
        })
    # Simulated concept drift check
    tp = sum(1 for s in samples.values() if s.label == SampleLabel.true_positive)
    fn = sum(1 for s in samples.values() if s.label == SampleLabel.false_negative)
    if fn > 0 and fn / max(tp + fn, 1) > 0.3:
        drifts.append({
            "type": DriftType.concept_drift.value,
            "detail": f"False negative rate {fn}/{tp + fn} exceeds threshold",
            "false_negative_rate": round(fn / max(tp + fn, 1), 4),
        })
    return drifts


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Continuous Defence Learning Loop",
    description="Phase 22 — Closed-loop defence adaptation with model retraining and drift detection",
    version="22.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    promoted = sum(1 for m in models.values() if m.state == ModelState.promoted)
    return {
        "service": "continuous-defence-learning-loop",
        "status": "healthy",
        "phase": 22,
        "port": 9601,
        "stats": {
            "samples": len(samples),
            "models": len(models),
            "promoted_models": promoted,
            "cycles": len(cycles),
        },
        "timestamp": _now(),
    }


# -- Samples -----------------------------------------------------------------

@app.post("/v1/samples", status_code=201)
def ingest_sample(body: SampleCreate):
    sid = f"SAM-{uuid.uuid4().hex[:12]}"
    record = SampleRecord(**body.dict(), sample_id=sid, ingested_at=_now())
    samples[sid] = record
    return record.dict()


@app.get("/v1/samples")
def list_samples(
    label: Optional[SampleLabel] = None,
    ave_category: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(samples.values())
    if label:
        results = [s for s in results if s.label == label]
    if ave_category:
        results = [s for s in results if s.ave_category == ave_category]
    results.sort(key=lambda s: s.ingested_at, reverse=True)
    return {"samples": [s.dict() for s in results[:limit]], "total": len(results)}


# -- Models ------------------------------------------------------------------

@app.post("/v1/models", status_code=201)
def register_model(body: ModelCreate):
    mid = f"MDL-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = ModelRecord(**body.dict(), model_id=mid, created_at=now, updated_at=now)
    models[mid] = record
    return record.dict()


@app.get("/v1/models")
def list_models(state: Optional[ModelState] = None):
    results = list(models.values())
    if state:
        results = [m for m in results if m.state == state]
    return {"models": [m.dict() for m in results], "total": len(results)}


# -- Learning Cycles ---------------------------------------------------------

@app.post("/v1/cycles", status_code=201)
def start_cycle(body: CycleCreate):
    if body.model_id not in models:
        raise HTTPException(404, "Model not found")
    cid = f"CYC-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = CycleRecord(**body.dict(), cycle_id=cid, created_at=now, updated_at=now)
    record.samples_collected = len(samples)
    _add_event(record, "cycle_started", f"Model: {body.model_id}, samples: {record.samples_collected}")

    # Auto-advance to training if enough samples
    if record.samples_collected >= body.min_samples:
        record.state = CycleState.training
        _add_event(record, "training_started", f"{record.samples_collected} samples available")
        model = models[body.model_id]
        _simulate_training(model, record.samples_collected)
        record.state = CycleState.evaluating
        _add_event(record, "training_completed", f"Accuracy: {model.metrics.accuracy}")

    cycles[cid] = record
    return record.dict()


@app.get("/v1/cycles")
def list_cycles(state: Optional[CycleState] = None):
    results = list(cycles.values())
    if state:
        results = [c for c in results if c.state == state]
    results.sort(key=lambda c: c.created_at, reverse=True)
    return {"cycles": [c.dict() for c in results], "total": len(results)}


@app.post("/v1/cycles/{cycle_id}/evaluate")
def evaluate_cycle(cycle_id: str):
    if cycle_id not in cycles:
        raise HTTPException(404, "Cycle not found")
    cyc = cycles[cycle_id]
    if cyc.state not in (CycleState.evaluating, CycleState.training):
        raise HTTPException(422, f"Cycle in state {cyc.state.value}, cannot evaluate")

    model = models.get(cyc.model_id)
    if not model:
        raise HTTPException(404, "Model not found")

    # If still training, simulate
    if model.state == ModelState.training:
        _simulate_training(model, cyc.samples_collected)

    passed = model.metrics.f1_score >= cyc.performance_threshold
    cyc.evaluation_result = {
        "f1_score": model.metrics.f1_score,
        "threshold": cyc.performance_threshold,
        "passed": passed,
        "accuracy": model.metrics.accuracy,
        "precision": model.metrics.precision,
        "recall": model.metrics.recall,
    }
    model.state = ModelState.candidate if passed else ModelState.training
    cyc.candidate_model_id = model.model_id if passed else None
    _add_event(cyc, "evaluation_completed", f"F1={model.metrics.f1_score}, passed={passed}")
    return cyc.evaluation_result


@app.post("/v1/cycles/{cycle_id}/promote")
def promote_cycle(cycle_id: str):
    if cycle_id not in cycles:
        raise HTTPException(404, "Cycle not found")
    cyc = cycles[cycle_id]
    if not cyc.candidate_model_id:
        raise HTTPException(422, "No candidate model to promote — run evaluation first")

    model = models[cyc.candidate_model_id]
    # Retire previously promoted models
    for m in models.values():
        if m.state == ModelState.promoted and m.model_id != model.model_id:
            m.state = ModelState.retired
            m.updated_at = _now()

    model.baseline_metrics = model.metrics.copy()
    model.state = ModelState.promoted
    model.version += 1
    model.updated_at = _now()

    cyc.state = CycleState.completed
    _add_event(cyc, "model_promoted", f"{model.model_id} v{model.version}")
    return {"cycle_id": cycle_id, "promoted_model": model.model_id, "version": model.version}


# -- Drift -------------------------------------------------------------------

@app.get("/v1/drift")
def drift_analysis():
    all_drifts: List[Dict[str, Any]] = []
    for model in models.values():
        if model.state == ModelState.promoted:
            drifts = _detect_drift(model)
            if drifts:
                all_drifts.append({
                    "model_id": model.model_id,
                    "model_name": model.name,
                    "drifts": drifts,
                })
    label_dist: Dict[str, int] = defaultdict(int)
    for s in samples.values():
        label_dist[s.label.value] += 1
    return {
        "models_with_drift": len(all_drifts),
        "drift_reports": all_drifts,
        "sample_label_distribution": dict(label_dist),
        "total_samples": len(samples),
    }


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    model_states: Dict[str, int] = defaultdict(int)
    cycle_states: Dict[str, int] = defaultdict(int)
    label_dist: Dict[str, int] = defaultdict(int)
    category_dist: Dict[str, int] = defaultdict(int)

    for m in models.values():
        model_states[m.state.value] += 1
    for c in cycles.values():
        cycle_states[c.state.value] += 1
    for s in samples.values():
        label_dist[s.label.value] += 1
        if s.ave_category:
            category_dist[s.ave_category] += 1

    promoted = [m for m in models.values() if m.state == ModelState.promoted]
    return {
        "samples": {
            "total": len(samples),
            "label_distribution": dict(label_dist),
            "category_distribution": dict(category_dist),
        },
        "models": {
            "total": len(models),
            "state_distribution": dict(model_states),
            "promoted_count": len(promoted),
            "best_f1": round(max((m.metrics.f1_score for m in models.values()), default=0), 4),
        },
        "cycles": {
            "total": len(cycles),
            "state_distribution": dict(cycle_states),
            "completed": sum(1 for c in cycles.values() if c.state == CycleState.completed),
        },
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9601)
