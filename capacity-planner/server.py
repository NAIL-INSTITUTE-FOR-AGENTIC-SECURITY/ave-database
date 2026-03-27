"""
Predictive Capacity Planner — Phase 23 Service 4 of 5
Port: 9703

ML-driven resource forecasting with auto-scaling recommendations,
cost optimisation, capacity reservation, and trend analysis.
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

class ResourceType(str, Enum):
    compute = "compute"
    memory = "memory"
    storage = "storage"
    network = "network"
    gpu = "gpu"
    api_quota = "api_quota"


class ScalingAction(str, Enum):
    scale_up = "scale_up"
    scale_down = "scale_down"
    reserve = "reserve"
    no_action = "no_action"


class ReservationStatus(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ResourceCreate(BaseModel):
    name: str
    resource_type: ResourceType
    region: str = "default"
    current_capacity: float = 100.0
    min_capacity: float = Field(default=10.0, ge=0)
    max_capacity: float = Field(default=1000.0, ge=1)
    unit_cost_per_hour: float = Field(default=0.10, ge=0)
    currency: str = "USD"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResourceRecord(ResourceCreate):
    resource_id: str
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


MAX_METRICS_PER_RESOURCE = 1000


class MetricIngest(BaseModel):
    metric_name: str
    value: float
    timestamp: Optional[str] = None


class ForecastResult(BaseModel):
    resource_id: str
    metric_name: str
    current_value: float = 0.0
    forecasted_values: List[Dict[str, float]] = Field(default_factory=list)
    trend_slope: float = 0.0
    trend_direction: str = "stable"
    capacity_breach_hour: Optional[int] = None
    confidence: float = 0.0


class Recommendation(BaseModel):
    resource_id: str
    action: ScalingAction
    reason: str
    current_capacity: float
    recommended_capacity: float
    current_cost_per_hour: float
    projected_cost_per_hour: float
    savings_potential: float
    confidence: float


class ReservationCreate(BaseModel):
    resource_id: str
    reserved_capacity: float = Field(ge=1)
    start_at: str
    end_at: str
    reason: str = ""


class ReservationRecord(ReservationCreate):
    reservation_id: str
    status: ReservationStatus = ReservationStatus.pending
    created_at: str


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

resources: Dict[str, ResourceRecord] = {}
reservations: Dict[str, ReservationRecord] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Forecasting Helpers
# ---------------------------------------------------------------------------

def _get_metric_series(resource: ResourceRecord, metric_name: str) -> List[float]:
    return [m["value"] for m in resource.metrics if m.get("metric_name") == metric_name]


def _exponential_smoothing(series: List[float], alpha: float = 0.3) -> List[float]:
    if not series:
        return []
    smoothed = [series[0]]
    for val in series[1:]:
        smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
    return smoothed


def _compute_trend(series: List[float]) -> float:
    """Linear regression slope."""
    n = len(series)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2
    y_mean = sum(series) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(series))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / max(den, 0.001)


def _forecast(resource: ResourceRecord, metric_name: str, horizon_hours: int = 24) -> ForecastResult:
    series = _get_metric_series(resource, metric_name)
    if not series:
        return ForecastResult(resource_id=resource.resource_id, metric_name=metric_name)

    smoothed = _exponential_smoothing(series)
    slope = _compute_trend(smoothed)
    current = smoothed[-1] if smoothed else 0
    direction = "rising" if slope > 0.5 else "falling" if slope < -0.5 else "stable"

    forecasted = []
    breach_hour = None
    for h in range(1, horizon_hours + 1):
        projected = current + slope * h + random.uniform(-1, 1)
        projected = max(0, projected)
        forecasted.append({"hour": h, "value": round(projected, 4)})
        if projected > resource.max_capacity * 0.8 and breach_hour is None:
            breach_hour = h

    # Confidence based on data volume
    confidence = min(1.0, len(series) / 50)

    return ForecastResult(
        resource_id=resource.resource_id,
        metric_name=metric_name,
        current_value=round(current, 4),
        forecasted_values=forecasted,
        trend_slope=round(slope, 4),
        trend_direction=direction,
        capacity_breach_hour=breach_hour,
        confidence=round(confidence, 4),
    )


def _recommend(resource: ResourceRecord) -> Recommendation:
    # Use most recent metric or default
    series = _get_metric_series(resource, "utilisation")
    if not series:
        series = [v["value"] for v in resource.metrics[-20:]] if resource.metrics else []

    if not series:
        return Recommendation(
            resource_id=resource.resource_id,
            action=ScalingAction.no_action,
            reason="Insufficient data",
            current_capacity=resource.current_capacity,
            recommended_capacity=resource.current_capacity,
            current_cost_per_hour=resource.unit_cost_per_hour * resource.current_capacity,
            projected_cost_per_hour=resource.unit_cost_per_hour * resource.current_capacity,
            savings_potential=0.0,
            confidence=0.0,
        )

    avg = sum(series) / len(series)
    utilisation_pct = avg / max(resource.current_capacity, 1) * 100
    slope = _compute_trend(series)

    if utilisation_pct > 80 or slope > 2:
        action = ScalingAction.scale_up
        new_cap = min(resource.max_capacity, resource.current_capacity * 1.5)
        reason = f"Utilisation at {utilisation_pct:.1f}% with rising trend (slope={slope:.2f})"
    elif utilisation_pct < 30 and slope <= 0:
        action = ScalingAction.scale_down
        new_cap = max(resource.min_capacity, resource.current_capacity * 0.6)
        reason = f"Utilisation at {utilisation_pct:.1f}% — over-provisioned"
    else:
        action = ScalingAction.no_action
        new_cap = resource.current_capacity
        reason = f"Utilisation at {utilisation_pct:.1f}% — within bounds"

    cur_cost = resource.unit_cost_per_hour * resource.current_capacity
    new_cost = resource.unit_cost_per_hour * new_cap
    savings = max(0, cur_cost - new_cost)
    confidence = min(1.0, len(series) / 30)

    return Recommendation(
        resource_id=resource.resource_id,
        action=action,
        reason=reason,
        current_capacity=resource.current_capacity,
        recommended_capacity=round(new_cap, 2),
        current_cost_per_hour=round(cur_cost, 4),
        projected_cost_per_hour=round(new_cost, 4),
        savings_potential=round(savings, 4),
        confidence=round(confidence, 4),
    )


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Predictive Capacity Planner",
    description="Phase 23 — ML-driven resource forecasting, auto-scaling recommendations, cost optimisation",
    version="23.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {
        "service": "predictive-capacity-planner",
        "status": "healthy",
        "phase": 23,
        "port": 9703,
        "stats": {
            "resources": len(resources),
            "total_metrics": sum(len(r.metrics) for r in resources.values()),
            "reservations": len(reservations),
        },
        "timestamp": _now(),
    }


# -- Resources ---------------------------------------------------------------

@app.post("/v1/resources", status_code=201)
def register_resource(body: ResourceCreate):
    rid = f"RES-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = ResourceRecord(**body.dict(), resource_id=rid, created_at=now, updated_at=now)
    resources[rid] = record
    return record.dict()


@app.get("/v1/resources")
def list_resources(
    resource_type: Optional[ResourceType] = None,
    region: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(resources.values())
    if resource_type:
        results = [r for r in results if r.resource_type == resource_type]
    if region:
        results = [r for r in results if r.region == region]
    results.sort(key=lambda r: r.name)
    return {"resources": [r.dict() for r in results[:limit]], "total": len(results)}


@app.post("/v1/resources/{res_id}/metrics")
def ingest_metric(res_id: str, body: MetricIngest):
    if res_id not in resources:
        raise HTTPException(404, "Resource not found")
    resource = resources[res_id]
    entry = {
        "metric_name": body.metric_name,
        "value": body.value,
        "timestamp": body.timestamp or _now(),
    }
    resource.metrics.append(entry)
    if len(resource.metrics) > MAX_METRICS_PER_RESOURCE:
        resource.metrics = resource.metrics[-MAX_METRICS_PER_RESOURCE:]
    resource.updated_at = _now()
    return {"resource_id": res_id, "metric_count": len(resource.metrics)}


@app.get("/v1/resources/{res_id}/forecast")
def get_forecast(res_id: str, metric_name: str = "utilisation", horizon_hours: int = 24):
    if res_id not in resources:
        raise HTTPException(404, "Resource not found")
    return _forecast(resources[res_id], metric_name, horizon_hours).dict()


@app.get("/v1/resources/{res_id}/recommendation")
def get_recommendation(res_id: str):
    if res_id not in resources:
        raise HTTPException(404, "Resource not found")
    return _recommend(resources[res_id]).dict()


# -- Reservations ------------------------------------------------------------

@app.post("/v1/reservations", status_code=201)
def create_reservation(body: ReservationCreate):
    if body.resource_id not in resources:
        raise HTTPException(404, "Resource not found")
    rvid = f"RSV-{uuid.uuid4().hex[:12]}"
    record = ReservationRecord(**body.dict(), reservation_id=rvid, created_at=_now())
    reservations[rvid] = record
    return record.dict()


@app.get("/v1/reservations")
def list_reservations(status: Optional[ReservationStatus] = None):
    results = list(reservations.values())
    if status:
        results = [r for r in results if r.status == status]
    return {"reservations": [r.dict() for r in results], "total": len(results)}


# -- Cost Report -------------------------------------------------------------

@app.get("/v1/cost-report")
def cost_report():
    report = []
    total_current = 0.0
    total_optimised = 0.0
    for res in resources.values():
        rec = _recommend(res)
        total_current += rec.current_cost_per_hour
        total_optimised += rec.projected_cost_per_hour
        report.append({
            "resource_id": res.resource_id,
            "name": res.name,
            "resource_type": res.resource_type.value,
            "action": rec.action.value,
            "current_cost_per_hour": rec.current_cost_per_hour,
            "optimised_cost_per_hour": rec.projected_cost_per_hour,
            "savings_per_hour": rec.savings_potential,
        })
    return {
        "resources": report,
        "total_current_cost_per_hour": round(total_current, 4),
        "total_optimised_cost_per_hour": round(total_optimised, 4),
        "total_savings_per_hour": round(max(0, total_current - total_optimised), 4),
        "total_savings_per_month": round(max(0, total_current - total_optimised) * 730, 2),
    }


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    type_dist: Dict[str, int] = defaultdict(int)
    region_dist: Dict[str, int] = defaultdict(int)
    for r in resources.values():
        type_dist[r.resource_type.value] += 1
        region_dist[r.region] += 1

    action_dist: Dict[str, int] = defaultdict(int)
    for r in resources.values():
        rec = _recommend(r)
        action_dist[rec.action.value] += 1

    return {
        "resources": {
            "total": len(resources),
            "type_distribution": dict(type_dist),
            "region_distribution": dict(region_dist),
            "total_metrics": sum(len(r.metrics) for r in resources.values()),
        },
        "recommendations": {
            "action_distribution": dict(action_dist),
        },
        "reservations": {
            "total": len(reservations),
            "active": sum(1 for r in reservations.values() if r.status == ReservationStatus.active),
        },
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9703)
