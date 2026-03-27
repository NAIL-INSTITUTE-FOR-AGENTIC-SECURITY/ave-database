"""
Chaos Engineering Orchestrator — Phase 23 Service 2 of 5
Port: 9701

Automated fault injection framework with blast radius control,
steady-state validation, experiment scheduling, and automated
rollback on safety violations.
"""

from __future__ import annotations

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

class FaultType(str, Enum):
    latency_injection = "latency_injection"
    error_injection = "error_injection"
    cpu_stress = "cpu_stress"
    memory_pressure = "memory_pressure"
    network_partition = "network_partition"
    dependency_failure = "dependency_failure"
    clock_skew = "clock_skew"
    disk_pressure = "disk_pressure"


class ExperimentState(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    running = "running"
    validating = "validating"
    completed = "completed"
    aborted = "aborted"
    rolled_back = "rolled_back"


class Operator(str, Enum):
    lt = "lt"
    gt = "gt"
    eq = "eq"
    lte = "lte"
    gte = "gte"


class ScheduleFrequency(str, Enum):
    once = "once"
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class SteadyStateCheck(BaseModel):
    metric_name: str
    operator: Operator
    threshold: float


class BlastRadiusConfig(BaseModel):
    max_affected_services: int = Field(default=3, ge=1)
    max_error_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    geographic_scope: List[str] = Field(default_factory=list)


class ExperimentCreate(BaseModel):
    name: str
    hypothesis: str
    fault_type: FaultType
    target_services: List[str] = Field(default_factory=list)
    duration_seconds: int = Field(default=60, ge=5, le=3600)
    blast_radius: BlastRadiusConfig = Field(default_factory=BlastRadiusConfig)
    steady_state_checks: List[SteadyStateCheck] = Field(default_factory=list)
    rollback_on_violation: bool = True
    fault_parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class ExperimentResult(BaseModel):
    hypothesis_validated: bool = False
    steady_state_maintained: bool = True
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    metrics_before: Dict[str, float] = Field(default_factory=dict)
    metrics_during: Dict[str, float] = Field(default_factory=dict)
    metrics_after: Dict[str, float] = Field(default_factory=dict)
    blast_radius_actual: int = 0
    duration_actual_seconds: float = 0.0
    rolled_back: bool = False


class ExperimentRecord(ExperimentCreate):
    experiment_id: str
    state: ExperimentState = ExperimentState.draft
    result: ExperimentResult = Field(default_factory=ExperimentResult)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ScheduleCreate(BaseModel):
    experiment_id: str
    frequency: ScheduleFrequency = ScheduleFrequency.weekly
    enabled: bool = True
    description: str = ""


class ScheduleRecord(ScheduleCreate):
    schedule_id: str
    last_run_at: Optional[str] = None
    run_count: int = 0
    created_at: str


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

experiments: Dict[str, ExperimentRecord] = {}
schedules: Dict[str, ScheduleRecord] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _add_event(exp: ExperimentRecord, event: str, detail: str = ""):
    exp.events.append({"event": event, "detail": detail, "timestamp": _now()})
    exp.updated_at = _now()


# ---------------------------------------------------------------------------
# Simulation Helpers
# ---------------------------------------------------------------------------

def _simulate_metric(metric_name: str, fault: FaultType, phase: str) -> float:
    """Simulate metric values before/during/after fault."""
    base = {"error_rate": 0.02, "p99_latency": 50, "availability": 99.9, "cpu_usage": 40}
    val = base.get(metric_name, 50.0)
    if phase == "during":
        if fault in (FaultType.error_injection, FaultType.dependency_failure):
            if metric_name == "error_rate":
                val += random.uniform(0.05, 0.3)
            elif metric_name == "availability":
                val -= random.uniform(1, 10)
        elif fault in (FaultType.latency_injection, FaultType.network_partition):
            if metric_name == "p99_latency":
                val += random.uniform(100, 500)
        elif fault in (FaultType.cpu_stress, FaultType.memory_pressure):
            if metric_name == "cpu_usage":
                val += random.uniform(20, 50)
    elif phase == "after":
        val += random.uniform(-2, 2)  # Slight variation post-recovery
    return round(val, 4)


def _check_steady_state(checks: List[SteadyStateCheck], metrics: Dict[str, float]) -> List[Dict[str, Any]]:
    violations = []
    for check in checks:
        actual = metrics.get(check.metric_name)
        if actual is None:
            continue
        violated = False
        if check.operator == Operator.lt and not (actual < check.threshold):
            violated = True
        elif check.operator == Operator.gt and not (actual > check.threshold):
            violated = True
        elif check.operator == Operator.eq and not (abs(actual - check.threshold) < 0.001):
            violated = True
        elif check.operator == Operator.lte and not (actual <= check.threshold):
            violated = True
        elif check.operator == Operator.gte and not (actual >= check.threshold):
            violated = True
        if violated:
            violations.append({
                "metric": check.metric_name,
                "operator": check.operator.value,
                "threshold": check.threshold,
                "actual": actual,
            })
    return violations


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Chaos Engineering Orchestrator",
    description="Phase 23 — Automated fault injection with blast radius control and steady-state validation",
    version="23.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    running = sum(1 for e in experiments.values() if e.state == ExperimentState.running)
    return {
        "service": "chaos-engineering-orchestrator",
        "status": "healthy",
        "phase": 23,
        "port": 9701,
        "stats": {
            "experiments": len(experiments),
            "running": running,
            "schedules": len(schedules),
        },
        "timestamp": _now(),
    }


# -- Experiments -------------------------------------------------------------

@app.post("/v1/experiments", status_code=201)
def create_experiment(body: ExperimentCreate):
    eid = f"EXP-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = ExperimentRecord(**body.dict(), experiment_id=eid, created_at=now, updated_at=now)
    _add_event(record, "experiment_created", f"Fault: {body.fault_type.value}, targets: {len(body.target_services)}")
    experiments[eid] = record
    return record.dict()


@app.get("/v1/experiments")
def list_experiments(
    state: Optional[ExperimentState] = None,
    fault_type: Optional[FaultType] = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    results = list(experiments.values())
    if state:
        results = [e for e in results if e.state == state]
    if fault_type:
        results = [e for e in results if e.fault_type == fault_type]
    results.sort(key=lambda e: e.created_at, reverse=True)
    return {"experiments": [e.dict() for e in results[:limit]], "total": len(results)}


@app.get("/v1/experiments/{exp_id}")
def get_experiment(exp_id: str):
    if exp_id not in experiments:
        raise HTTPException(404, "Experiment not found")
    return experiments[exp_id].dict()


@app.post("/v1/experiments/{exp_id}/run")
def run_experiment(exp_id: str):
    if exp_id not in experiments:
        raise HTTPException(404, "Experiment not found")
    exp = experiments[exp_id]
    if exp.state in (ExperimentState.running, ExperimentState.completed):
        raise HTTPException(409, f"Experiment already {exp.state.value}")

    exp.state = ExperimentState.running
    exp.started_at = _now()
    _add_event(exp, "experiment_started")

    # Collect all steady-state metric names
    metric_names = list(set(c.metric_name for c in exp.steady_state_checks))
    if not metric_names:
        metric_names = ["error_rate", "p99_latency", "availability"]

    # Phase 1: Measure before
    metrics_before = {m: _simulate_metric(m, exp.fault_type, "before") for m in metric_names}
    exp.result.metrics_before = metrics_before
    _add_event(exp, "baseline_measured", str(metrics_before))

    # Phase 2: Inject fault + measure during
    _add_event(exp, "fault_injected", f"{exp.fault_type.value} on {len(exp.target_services)} services")
    metrics_during = {m: _simulate_metric(m, exp.fault_type, "during") for m in metric_names}
    exp.result.metrics_during = metrics_during
    exp.result.blast_radius_actual = min(len(exp.target_services), exp.blast_radius.max_affected_services)
    exp.result.duration_actual_seconds = float(exp.duration_seconds)

    # Phase 3: Validate steady state
    exp.state = ExperimentState.validating
    _add_event(exp, "validating_steady_state")
    violations = _check_steady_state(exp.steady_state_checks, metrics_during)
    exp.result.violations = violations

    if violations:
        exp.result.steady_state_maintained = False
        _add_event(exp, "steady_state_violated", f"{len(violations)} violations")
        if exp.rollback_on_violation:
            exp.state = ExperimentState.rolled_back
            exp.result.rolled_back = True
            _add_event(exp, "rollback_executed")
        else:
            exp.state = ExperimentState.completed
    else:
        exp.result.steady_state_maintained = True
        exp.state = ExperimentState.completed
        _add_event(exp, "steady_state_maintained")

    # Phase 4: Measure after
    metrics_after = {m: _simulate_metric(m, exp.fault_type, "after") for m in metric_names}
    exp.result.metrics_after = metrics_after

    # Hypothesis validation
    exp.result.hypothesis_validated = exp.result.steady_state_maintained
    exp.completed_at = _now()
    _add_event(exp, "experiment_completed", f"Hypothesis validated: {exp.result.hypothesis_validated}")

    return exp.result.dict()


@app.post("/v1/experiments/{exp_id}/abort")
def abort_experiment(exp_id: str):
    if exp_id not in experiments:
        raise HTTPException(404, "Experiment not found")
    exp = experiments[exp_id]
    if exp.state != ExperimentState.running:
        raise HTTPException(409, "Experiment not running")
    exp.state = ExperimentState.aborted
    exp.completed_at = _now()
    _add_event(exp, "experiment_aborted")
    return {"experiment_id": exp_id, "state": exp.state.value}


@app.get("/v1/experiments/{exp_id}/results")
def get_results(exp_id: str):
    if exp_id not in experiments:
        raise HTTPException(404, "Experiment not found")
    exp = experiments[exp_id]
    return {"experiment_id": exp_id, "state": exp.state.value, "result": exp.result.dict()}


# -- Schedules ---------------------------------------------------------------

@app.post("/v1/schedules", status_code=201)
def create_schedule(body: ScheduleCreate):
    if body.experiment_id not in experiments:
        raise HTTPException(404, "Experiment not found")
    sid = f"SCHED-{uuid.uuid4().hex[:12]}"
    record = ScheduleRecord(**body.dict(), schedule_id=sid, created_at=_now())
    schedules[sid] = record
    return record.dict()


@app.get("/v1/schedules")
def list_schedules():
    return {"schedules": [s.dict() for s in schedules.values()], "total": len(schedules)}


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    state_dist: Dict[str, int] = defaultdict(int)
    fault_dist: Dict[str, int] = defaultdict(int)
    for e in experiments.values():
        state_dist[e.state.value] += 1
        fault_dist[e.fault_type.value] += 1

    completed = [e for e in experiments.values() if e.state in (ExperimentState.completed, ExperimentState.rolled_back)]
    validated = sum(1 for e in completed if e.result.hypothesis_validated)
    rolled = sum(1 for e in completed if e.result.rolled_back)
    violations_total = sum(len(e.result.violations) for e in completed)

    return {
        "experiments": {
            "total": len(experiments),
            "state_distribution": dict(state_dist),
            "fault_type_distribution": dict(fault_dist),
        },
        "outcomes": {
            "completed": len(completed),
            "hypothesis_validated": validated,
            "hypothesis_invalidated": len(completed) - validated,
            "rollbacks": rolled,
            "total_violations": violations_total,
        },
        "schedules": {
            "total": len(schedules),
            "enabled": sum(1 for s in schedules.values() if s.enabled),
        },
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9701)
