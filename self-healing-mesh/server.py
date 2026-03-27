"""
Self-Healing Service Mesh — Phase 23 Service 1 of 5
Port: 9700

Autonomous service recovery with failure prediction, automatic restarts,
traffic rerouting, cascading failure prevention, and real-time health
topology awareness.
"""

from __future__ import annotations

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

class HealthState(str, Enum):
    healthy = "healthy"
    warning = "warning"
    degraded = "degraded"
    failing = "failing"
    dead = "dead"
    recovering = "recovering"


HEALTH_SEVERITY = {
    "healthy": 0, "warning": 1, "degraded": 2,
    "failing": 3, "dead": 4, "recovering": 1,
}


class HealAction(str, Enum):
    restart = "restart"
    reroute = "reroute"
    isolate = "isolate"
    scale_up = "scale_up"
    restore = "restore"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class NodeCreate(BaseModel):
    service_name: str
    endpoint: str
    region: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeRecord(NodeCreate):
    node_id: str
    health_state: HealthState = HealthState.healthy
    health_score: float = 100.0
    restart_count: int = 0
    last_restart_at: Optional[str] = None
    isolated: bool = False
    heartbeat_history: List[Dict[str, Any]] = Field(default_factory=list)
    healing_log: List[Dict[str, Any]] = Field(default_factory=list)
    registered_at: str
    updated_at: str


class HeartbeatPayload(BaseModel):
    latency_ms: float = 0.0
    error_rate: float = 0.0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_connections: int = 0


class RouteCreate(BaseModel):
    source_node: str
    target_node: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class RouteRecord(RouteCreate):
    route_id: str
    active: bool = True
    created_at: str


class HealRequest(BaseModel):
    action: HealAction
    reason: str = ""


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

nodes: Dict[str, NodeRecord] = {}
routes: Dict[str, RouteRecord] = {}
MAX_HEARTBEAT_HISTORY = 50


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_health_score(hb: HeartbeatPayload) -> float:
    """0-100 score: higher = healthier."""
    score = 100.0
    score -= min(hb.error_rate * 100, 40)           # up to -40 for errors
    score -= min(hb.latency_ms / 50, 30)            # up to -30 for latency
    score -= min(hb.cpu_percent / 5, 15)             # up to -15 for CPU
    score -= min(hb.memory_percent / 5, 15)          # up to -15 for memory
    return round(max(0.0, min(100.0, score)), 2)


def _score_to_state(score: float) -> HealthState:
    if score >= 80:
        return HealthState.healthy
    elif score >= 60:
        return HealthState.warning
    elif score >= 40:
        return HealthState.degraded
    elif score >= 15:
        return HealthState.failing
    else:
        return HealthState.dead


def _predict_risk(node: NodeRecord) -> Dict[str, Any]:
    """Predict failure risk based on heartbeat trend."""
    history = node.heartbeat_history[-10:]
    if len(history) < 3:
        return {"risk_score": 0.0, "trend": "insufficient_data", "recommended_action": "none"}

    scores = [h.get("health_score", 100) for h in history]
    # Simple linear trend
    n = len(scores)
    x_mean = (n - 1) / 2
    y_mean = sum(scores) / n
    num = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(scores))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / max(den, 0.001)

    # Error rate trend
    error_rates = [h.get("error_rate", 0) for h in history]
    avg_error = sum(error_rates) / len(error_rates)

    risk = 0.0
    risk += max(0, -slope * 5)          # Declining health
    risk += avg_error * 50              # High error rate
    risk += max(0, (50 - scores[-1]) / 50)  # Low current score
    risk = round(min(1.0, max(0.0, risk)), 4)

    if risk > 0.7:
        action = "restart"
    elif risk > 0.5:
        action = "reroute"
    elif risk > 0.3:
        action = "monitor_closely"
    else:
        action = "none"

    return {
        "risk_score": risk,
        "trend": "declining" if slope < -2 else "stable" if abs(slope) <= 2 else "improving",
        "health_slope": round(slope, 4),
        "avg_error_rate": round(avg_error, 4),
        "current_score": scores[-1],
        "recommended_action": action,
    }


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Self-Healing Service Mesh",
    description="Phase 23 — Autonomous service recovery with failure prediction and traffic rerouting",
    version="23.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    state_counts: Dict[str, int] = defaultdict(int)
    for n in nodes.values():
        state_counts[n.health_state.value] += 1
    return {
        "service": "self-healing-service-mesh",
        "status": "healthy",
        "phase": 23,
        "port": 9700,
        "stats": {
            "nodes": len(nodes),
            "routes": len(routes),
            "health_distribution": dict(state_counts),
        },
        "timestamp": _now(),
    }


# -- Nodes -------------------------------------------------------------------

@app.post("/v1/nodes", status_code=201)
def register_node(body: NodeCreate):
    nid = f"NODE-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = NodeRecord(**body.dict(), node_id=nid, registered_at=now, updated_at=now)
    nodes[nid] = record
    return record.dict()


@app.get("/v1/nodes")
def list_nodes(
    health_state: Optional[HealthState] = None,
    region: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(nodes.values())
    if health_state:
        results = [n for n in results if n.health_state == health_state]
    if region:
        results = [n for n in results if n.region == region]
    results.sort(key=lambda n: n.health_score)
    return {"nodes": [n.dict() for n in results[:limit]], "total": len(results)}


@app.get("/v1/nodes/{node_id}")
def get_node(node_id: str):
    if node_id not in nodes:
        raise HTTPException(404, "Node not found")
    return nodes[node_id].dict()


@app.post("/v1/nodes/{node_id}/heartbeat")
def node_heartbeat(node_id: str, body: HeartbeatPayload):
    if node_id not in nodes:
        raise HTTPException(404, "Node not found")
    node = nodes[node_id]

    score = _compute_health_score(body)
    new_state = _score_to_state(score)

    # If node was recovering and now healthy, complete recovery
    if node.health_state == HealthState.recovering and score >= 60:
        new_state = HealthState.healthy

    node.health_score = score
    node.health_state = new_state
    node.updated_at = _now()

    hb_entry = {
        "health_score": score,
        "state": new_state.value,
        "latency_ms": body.latency_ms,
        "error_rate": body.error_rate,
        "cpu_percent": body.cpu_percent,
        "memory_percent": body.memory_percent,
        "timestamp": _now(),
    }
    node.heartbeat_history.append(hb_entry)
    if len(node.heartbeat_history) > MAX_HEARTBEAT_HISTORY:
        node.heartbeat_history = node.heartbeat_history[-MAX_HEARTBEAT_HISTORY:]

    # Auto-reroute if degraded
    if HEALTH_SEVERITY[new_state.value] >= 2:
        for route in routes.values():
            if route.target_node == node_id and route.active:
                route.weight = max(0.1, route.weight * 0.5)

    # Auto-restore routes if healthy
    if new_state == HealthState.healthy and not node.isolated:
        for route in routes.values():
            if route.target_node == node_id:
                route.weight = 1.0
                route.active = True

    return {"node_id": node_id, "health_score": score, "health_state": new_state.value}


# -- Routes ------------------------------------------------------------------

@app.post("/v1/routes", status_code=201)
def create_route(body: RouteCreate):
    if body.source_node not in nodes:
        raise HTTPException(404, f"Source node {body.source_node} not found")
    if body.target_node not in nodes:
        raise HTTPException(404, f"Target node {body.target_node} not found")
    rid = f"RT-{uuid.uuid4().hex[:12]}"
    record = RouteRecord(**body.dict(), route_id=rid, created_at=_now())
    routes[rid] = record
    return record.dict()


@app.get("/v1/routes")
def list_routes(active_only: bool = False):
    results = list(routes.values())
    if active_only:
        results = [r for r in results if r.active]
    return {"routes": [r.dict() for r in results], "total": len(results)}


# -- Prediction --------------------------------------------------------------

@app.get("/v1/nodes/{node_id}/predict")
def predict_failure(node_id: str):
    if node_id not in nodes:
        raise HTTPException(404, "Node not found")
    prediction = _predict_risk(nodes[node_id])
    return {"node_id": node_id, **prediction}


# -- Healing -----------------------------------------------------------------

@app.post("/v1/nodes/{node_id}/heal")
def heal_node(node_id: str, body: HealRequest):
    if node_id not in nodes:
        raise HTTPException(404, "Node not found")
    node = nodes[node_id]
    action = body.action
    result: Dict[str, Any] = {"node_id": node_id, "action": action.value, "timestamp": _now()}

    if action == HealAction.restart:
        node.restart_count += 1
        node.last_restart_at = _now()
        node.health_state = HealthState.recovering
        node.health_score = 50.0
        result["detail"] = f"Restart #{node.restart_count} initiated"

    elif action == HealAction.reroute:
        rerouted = 0
        for route in routes.values():
            if route.target_node == node_id and route.active:
                route.weight = 0.0
                rerouted += 1
        result["routes_rerouted"] = rerouted

    elif action == HealAction.isolate:
        node.isolated = True
        for route in routes.values():
            if route.target_node == node_id or route.source_node == node_id:
                route.active = False
        result["detail"] = "Node isolated from mesh"

    elif action == HealAction.scale_up:
        result["detail"] = "Scale-up request logged (production: triggers orchestrator)"

    elif action == HealAction.restore:
        node.isolated = False
        node.health_state = HealthState.recovering
        for route in routes.values():
            if route.target_node == node_id or route.source_node == node_id:
                route.active = True
                route.weight = 0.5  # Gradually restore
        result["detail"] = "Node restoration initiated"

    node.healing_log.append({
        "action": action.value,
        "reason": body.reason,
        "result": result.get("detail", ""),
        "timestamp": _now(),
    })
    node.updated_at = _now()
    return result


# -- Topology ----------------------------------------------------------------

@app.get("/v1/topology")
def topology():
    node_list = []
    for n in nodes.values():
        connected_routes = [
            r.route_id for r in routes.values()
            if r.source_node == n.node_id or r.target_node == n.node_id
        ]
        node_list.append({
            "node_id": n.node_id,
            "service_name": n.service_name,
            "region": n.region,
            "health_state": n.health_state.value,
            "health_score": n.health_score,
            "isolated": n.isolated,
            "connected_routes": len(connected_routes),
        })

    region_groups: Dict[str, List[str]] = defaultdict(list)
    for n in nodes.values():
        region_groups[n.region].append(n.node_id)

    return {
        "nodes": node_list,
        "routes": [r.dict() for r in routes.values()],
        "regions": {k: len(v) for k, v in region_groups.items()},
        "total_nodes": len(nodes),
        "total_routes": len(routes),
    }


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    state_dist: Dict[str, int] = defaultdict(int)
    region_dist: Dict[str, int] = defaultdict(int)
    for n in nodes.values():
        state_dist[n.health_state.value] += 1
        region_dist[n.region] += 1

    scores = [n.health_score for n in nodes.values()]
    total_restarts = sum(n.restart_count for n in nodes.values())
    isolated = sum(1 for n in nodes.values() if n.isolated)

    return {
        "nodes": {
            "total": len(nodes),
            "state_distribution": dict(state_dist),
            "region_distribution": dict(region_dist),
            "isolated": isolated,
        },
        "health": {
            "avg_score": round(sum(scores) / max(len(scores), 1), 2) if scores else None,
            "min_score": round(min(scores), 2) if scores else None,
            "max_score": round(max(scores), 2) if scores else None,
        },
        "healing": {
            "total_restarts": total_restarts,
            "total_healing_events": sum(len(n.healing_log) for n in nodes.values()),
        },
        "routes": {
            "total": len(routes),
            "active": sum(1 for r in routes.values() if r.active),
        },
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9700)
