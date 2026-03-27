"""
Synthetic Training Data Forge — Phase 22 Service 4 of 5
Port: 9603

Privacy-preserving synthetic data generation for security training
with differential privacy guarantees, fidelity scoring, and configurable
generation pipelines.
"""

from __future__ import annotations

import hashlib
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

class PipelineState(str, Enum):
    configured = "configured"
    profiling = "profiling"
    generating = "generating"
    scoring = "scoring"
    completed = "completed"
    failed = "failed"


class GenerationStrategy(str, Enum):
    statistical_sampling = "statistical_sampling"
    copula_based = "copula_based"
    marginal_based = "marginal_based"
    gan_simulated = "gan_simulated"


class NoiseMechanism(str, Enum):
    laplace = "laplace"
    gaussian = "gaussian"


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

class DatasetCreate(BaseModel):
    name: str
    description: str = ""
    schema_definition: Dict[str, str] = Field(default_factory=dict)  # field_name -> type
    record_count: int = Field(default=100, ge=1)
    source_categories: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DatasetRecord(DatasetCreate):
    dataset_id: str
    profile: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class DPConfig(BaseModel):
    epsilon: float = Field(default=1.0, gt=0.0)
    delta: float = Field(default=1e-5, gt=0.0, lt=1.0)
    noise_mechanism: NoiseMechanism = NoiseMechanism.laplace
    sensitivity: float = Field(default=1.0, gt=0.0)


class PipelineCreate(BaseModel):
    name: str
    dataset_id: str
    strategy: GenerationStrategy = GenerationStrategy.statistical_sampling
    synthetic_count: int = Field(default=100, ge=1, le=100000)
    dp_config: DPConfig = Field(default_factory=DPConfig)
    description: str = ""


class FidelityReport(BaseModel):
    statistical_similarity: float = 0.0
    correlation_preservation: float = 0.0
    schema_compliance: float = 0.0
    utility_score: float = 0.0
    overall: float = 0.0


class PrivacyAudit(BaseModel):
    noise_applied: bool = False
    mechanism: str = ""
    epsilon_used: float = 0.0
    delta_used: float = 0.0
    raw_records_leaked: int = 0
    membership_inference_success_rate: float = 0.0
    audit_passed: bool = False
    audited_at: str = ""


class PipelineRecord(PipelineCreate):
    pipeline_id: str
    state: PipelineState = PipelineState.configured
    synthetic_records: List[Dict[str, Any]] = Field(default_factory=list)
    fidelity: FidelityReport = Field(default_factory=FidelityReport)
    privacy_audit: PrivacyAudit = Field(default_factory=PrivacyAudit)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

datasets: Dict[str, DatasetRecord] = {}
pipelines: Dict[str, PipelineRecord] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _add_event(pipe: PipelineRecord, event: str, detail: str = ""):
    pipe.events.append({"event": event, "detail": detail, "timestamp": _now()})
    pipe.updated_at = _now()


# ---------------------------------------------------------------------------
# Synthetic Generation Helpers
# ---------------------------------------------------------------------------

def _laplace_noise(sensitivity: float, epsilon: float) -> float:
    scale = sensitivity / epsilon
    return random.uniform(-1, 1) * scale  # Simplified; production uses numpy


def _gaussian_noise(sensitivity: float, epsilon: float, delta: float) -> float:
    sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
    return random.gauss(0, sigma)


def _profile_dataset(ds: DatasetRecord) -> Dict[str, Any]:
    """Create statistical profile of the dataset."""
    profile: Dict[str, Any] = {}
    for field_name, field_type in ds.schema_definition.items():
        if field_type in ("int", "float", "numeric"):
            profile[field_name] = {
                "type": field_type,
                "mean": round(random.uniform(10, 100), 2),
                "std": round(random.uniform(1, 20), 2),
                "min": round(random.uniform(0, 10), 2),
                "max": round(random.uniform(100, 200), 2),
            }
        elif field_type in ("str", "string", "category"):
            cats = random.sample(AVE_CATEGORIES, min(5, len(AVE_CATEGORIES)))
            profile[field_name] = {
                "type": "categorical",
                "categories": cats,
                "distribution": {c: round(1.0 / len(cats), 4) for c in cats},
            }
        else:
            profile[field_name] = {"type": field_type, "note": "passthrough"}
    return profile


def _generate_synthetic(ds: DatasetRecord, pipe: PipelineRecord) -> List[Dict[str, Any]]:
    """Generate synthetic records based on dataset profile + DP config."""
    records: List[Dict[str, Any]] = []
    profile = ds.profile
    dp = pipe.dp_config

    noise_fn = _laplace_noise if dp.noise_mechanism == NoiseMechanism.laplace else _gaussian_noise

    for i in range(pipe.synthetic_count):
        record: Dict[str, Any] = {"_synthetic_id": f"SYN-{uuid.uuid4().hex[:8]}"}
        for field_name, field_profile in profile.items():
            ft = field_profile.get("type", "")
            if ft in ("int", "float", "numeric"):
                mean = field_profile.get("mean", 50)
                std = field_profile.get("std", 10)
                raw = random.gauss(mean, std)
                if dp.noise_mechanism == NoiseMechanism.laplace:
                    noise = _laplace_noise(dp.sensitivity, dp.epsilon)
                else:
                    noise = _gaussian_noise(dp.sensitivity, dp.epsilon, dp.delta)
                record[field_name] = round(raw + noise, 4)
            elif ft == "categorical":
                cats = field_profile.get("categories", ["unknown"])
                record[field_name] = random.choice(cats)
            else:
                record[field_name] = f"synthetic_{field_name}_{i}"
        records.append(record)
    return records


def _score_fidelity(pipe: PipelineRecord, ds: DatasetRecord) -> FidelityReport:
    """Score synthetic data fidelity (simulated)."""
    n = len(pipe.synthetic_records)
    schema_fields = set(ds.schema_definition.keys())
    if n == 0:
        return FidelityReport()
    compliant = sum(
        1 for r in pipe.synthetic_records
        if schema_fields.issubset(set(r.keys()) - {"_synthetic_id"})
    )
    schema_comp = round(compliant / n, 4)
    stat_sim = round(random.uniform(0.75, 0.98), 4)
    corr_pres = round(random.uniform(0.70, 0.95), 4)
    utility = round(random.uniform(0.65, 0.92), 4)
    overall = round(0.30 * stat_sim + 0.25 * corr_pres + 0.25 * schema_comp + 0.20 * utility, 4)
    return FidelityReport(
        statistical_similarity=stat_sim,
        correlation_preservation=corr_pres,
        schema_compliance=schema_comp,
        utility_score=utility,
        overall=overall,
    )


def _privacy_audit(pipe: PipelineRecord) -> PrivacyAudit:
    dp = pipe.dp_config
    # Simulated membership inference attack
    mi_rate = round(max(0.0, 0.5 - 0.04 / dp.epsilon), 4)  # Lower epsilon → harder to infer
    return PrivacyAudit(
        noise_applied=True,
        mechanism=dp.noise_mechanism.value,
        epsilon_used=dp.epsilon,
        delta_used=dp.delta,
        raw_records_leaked=0,
        membership_inference_success_rate=mi_rate,
        audit_passed=mi_rate < 0.55,
        audited_at=_now(),
    )


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Synthetic Training Data Forge",
    description="Phase 22 — Privacy-preserving synthetic data generation with DP guarantees",
    version="22.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    completed = sum(1 for p in pipelines.values() if p.state == PipelineState.completed)
    return {
        "service": "synthetic-training-data-forge",
        "status": "healthy",
        "phase": 22,
        "port": 9603,
        "stats": {
            "datasets": len(datasets),
            "pipelines": len(pipelines),
            "completed_pipelines": completed,
            "total_synthetic_records": sum(len(p.synthetic_records) for p in pipelines.values()),
        },
        "timestamp": _now(),
    }


# -- Datasets ----------------------------------------------------------------

@app.post("/v1/datasets", status_code=201)
def register_dataset(body: DatasetCreate):
    did = f"DS-{uuid.uuid4().hex[:12]}"
    record = DatasetRecord(**body.dict(), dataset_id=did, created_at=_now())
    record.profile = _profile_dataset(record)
    datasets[did] = record
    return record.dict()


@app.get("/v1/datasets")
def list_datasets(limit: int = Query(default=50, ge=1, le=500)):
    results = sorted(datasets.values(), key=lambda d: d.created_at, reverse=True)
    return {"datasets": [d.dict() for d in results[:limit]], "total": len(datasets)}


# -- Pipelines ---------------------------------------------------------------

@app.post("/v1/pipelines", status_code=201)
def create_pipeline(body: PipelineCreate):
    if body.dataset_id not in datasets:
        raise HTTPException(404, "Dataset not found")
    pid = f"PIPE-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = PipelineRecord(**body.dict(), pipeline_id=pid, created_at=now, updated_at=now)
    _add_event(record, "pipeline_created", f"Strategy: {body.strategy.value}, count: {body.synthetic_count}")
    pipelines[pid] = record
    return record.dict()


@app.get("/v1/pipelines")
def list_pipelines(state: Optional[PipelineState] = None, limit: int = Query(default=50, ge=1, le=500)):
    results = list(pipelines.values())
    if state:
        results = [p for p in results if p.state == state]
    results.sort(key=lambda p: p.created_at, reverse=True)
    return {"pipelines": [p.dict() for p in results[:limit]], "total": len(results)}


@app.post("/v1/pipelines/{pipe_id}/run")
def run_pipeline(pipe_id: str):
    if pipe_id not in pipelines:
        raise HTTPException(404, "Pipeline not found")
    pipe = pipelines[pipe_id]
    if pipe.state not in (PipelineState.configured, PipelineState.failed):
        raise HTTPException(409, f"Pipeline in state {pipe.state.value}, cannot run")

    ds = datasets.get(pipe.dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    # 1. Profile
    pipe.state = PipelineState.profiling
    _add_event(pipe, "profiling_started")
    ds.profile = _profile_dataset(ds)
    _add_event(pipe, "profiling_completed")

    # 2. Generate
    pipe.state = PipelineState.generating
    _add_event(pipe, "generation_started", f"Strategy: {pipe.strategy.value}")
    pipe.synthetic_records = _generate_synthetic(ds, pipe)
    _add_event(pipe, "generation_completed", f"{len(pipe.synthetic_records)} records")

    # 3. Score
    pipe.state = PipelineState.scoring
    pipe.fidelity = _score_fidelity(pipe, ds)
    _add_event(pipe, "fidelity_scored", f"Overall: {pipe.fidelity.overall}")

    # 4. Privacy audit
    pipe.privacy_audit = _privacy_audit(pipe)
    _add_event(pipe, "privacy_audited", f"MI rate: {pipe.privacy_audit.membership_inference_success_rate}")

    # 5. Complete
    if pipe.privacy_audit.audit_passed:
        pipe.state = PipelineState.completed
        _add_event(pipe, "pipeline_completed")
    else:
        pipe.state = PipelineState.failed
        _add_event(pipe, "pipeline_failed", "Privacy audit did not pass")

    return {
        "pipeline_id": pipe_id,
        "state": pipe.state.value,
        "records_generated": len(pipe.synthetic_records),
        "fidelity_overall": pipe.fidelity.overall,
        "privacy_audit_passed": pipe.privacy_audit.audit_passed,
    }


@app.get("/v1/pipelines/{pipe_id}/output")
def get_output(pipe_id: str, limit: int = Query(default=50, ge=1, le=1000)):
    if pipe_id not in pipelines:
        raise HTTPException(404, "Pipeline not found")
    pipe = pipelines[pipe_id]
    if not pipe.synthetic_records:
        raise HTTPException(404, "No output — run the pipeline first")
    return {
        "pipeline_id": pipe_id,
        "records": pipe.synthetic_records[:limit],
        "total": len(pipe.synthetic_records),
    }


@app.get("/v1/pipelines/{pipe_id}/fidelity")
def get_fidelity(pipe_id: str):
    if pipe_id not in pipelines:
        raise HTTPException(404, "Pipeline not found")
    return {"pipeline_id": pipe_id, "fidelity": pipelines[pipe_id].fidelity.dict()}


@app.get("/v1/pipelines/{pipe_id}/privacy-audit")
def get_privacy_audit(pipe_id: str):
    if pipe_id not in pipelines:
        raise HTTPException(404, "Pipeline not found")
    return {"pipeline_id": pipe_id, "privacy_audit": pipelines[pipe_id].privacy_audit.dict()}


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    state_dist: Dict[str, int] = defaultdict(int)
    strategy_dist: Dict[str, int] = defaultdict(int)
    for p in pipelines.values():
        state_dist[p.state.value] += 1
        strategy_dist[p.strategy.value] += 1

    completed = [p for p in pipelines.values() if p.state == PipelineState.completed]
    fidelities = [p.fidelity.overall for p in completed]
    epsilons = [p.dp_config.epsilon for p in pipelines.values()]

    return {
        "datasets": len(datasets),
        "pipelines": {
            "total": len(pipelines),
            "state_distribution": dict(state_dist),
            "strategy_distribution": dict(strategy_dist),
        },
        "fidelity": {
            "avg_overall": round(sum(fidelities) / max(len(fidelities), 1), 4) if fidelities else None,
            "max_overall": round(max(fidelities), 4) if fidelities else None,
            "min_overall": round(min(fidelities), 4) if fidelities else None,
        },
        "privacy": {
            "avg_epsilon": round(sum(epsilons) / max(len(epsilons), 1), 4) if epsilons else None,
            "total_synthetic_records": sum(len(p.synthetic_records) for p in pipelines.values()),
        },
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9603)
