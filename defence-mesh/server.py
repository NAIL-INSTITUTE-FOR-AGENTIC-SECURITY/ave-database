"""
Self-Healing Defence Mesh — Core mesh server.

Distributed defence network that autonomously detects, isolates, and
recovers from compromised nodes without human intervention.  Implements
heartbeat monitoring, quorum-based consensus, automatic isolation,
zero-downtime recovery, and dynamic rebalancing.
"""

from __future__ import annotations

import math
import random
import statistics
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NAIL Self-Healing Defence Mesh",
    description=(
        "Distributed defence network with autonomous failure detection, "
        "isolation, recovery, and rebalancing."
    ),
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NodeRole(str, Enum):
    GUARDRAIL = "guardrail"
    MONITOR = "monitor"
    ROUTER = "router"
    SENTINEL = "sentinel"
    COORDINATOR = "coordinator"


class NodeState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    SUSPECTED = "suspected"
    ISOLATED = "isolated"
    RECOVERING = "recovering"
    OFFLINE = "offline"


class MeshState(str, Enum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    PARTITIONED = "partitioned"
    HEALING = "healing"


class EventKind(str, Enum):
    NODE_JOINED = "node_joined"
    NODE_LEFT = "node_left"
    HEARTBEAT_MISSED = "heartbeat_missed"
    NODE_SUSPECTED = "node_suspected"
    NODE_ISOLATED = "node_isolated"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETE = "recovery_complete"
    RECOVERY_FAILED = "recovery_failed"
    REBALANCE_TRIGGERED = "rebalance_triggered"
    REBALANCE_COMPLETE = "rebalance_complete"
    PARTITION_DETECTED = "partition_detected"
    PARTITION_HEALED = "partition_healed"
    QUORUM_LOST = "quorum_lost"
    QUORUM_RESTORED = "quorum_restored"
    FAILURE_INJECTED = "failure_injected"
    CONFIG_ROLLBACK = "config_rollback"


class RecoveryStrategy(str, Enum):
    RESTART = "restart"
    REPLACE = "replace"
    CONFIG_ROLLBACK = "config_rollback"
    PROMOTE_STANDBY = "promote_standby"
    FULL_REBUILD = "full_rebuild"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class NodeConfig(BaseModel):
    role: NodeRole
    region: str = "default"
    capabilities: list[str] = Field(default_factory=list)
    max_load: float = 100.0
    standby_for: Optional[str] = None  # node ID this node is standby for


class MeshNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: NodeRole
    state: NodeState = NodeState.HEALTHY
    region: str = "default"
    capabilities: list[str] = Field(default_factory=list)
    max_load: float = 100.0
    current_load: float = 0.0
    standby_for: Optional[str] = None
    last_heartbeat: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    heartbeat_misses: int = 0
    joined_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    anomaly_score: float = 0.0
    recovery_attempts: int = 0
    config_version: int = 1
    neighbours: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MeshEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kind: EventKind
    node_id: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class QuorumStatus(BaseModel):
    total_nodes: int
    healthy_nodes: int
    quorum_threshold: float
    quorum_met: bool
    mesh_state: MeshState
    healthy_ratio: float
    required_healthy: int


class TopologyView(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, str]]
    regions: dict[str, list[str]]
    mesh_state: MeshState
    quorum: QuorumStatus


class PartitionInfo(BaseModel):
    partition_id: str
    node_ids: list[str]
    is_majority: bool
    size: int


class RebalanceResult(BaseModel):
    moved: int
    from_nodes: list[str]
    to_nodes: list[str]
    reason: str


class NodeRegistration(BaseModel):
    name: str
    role: NodeRole
    region: str = "default"
    capabilities: list[str] = Field(default_factory=list)
    max_load: float = 100.0
    standby_for: Optional[str] = None


class FailureInjection(BaseModel):
    target_node_id: str
    failure_type: str = "heartbeat_timeout"
    duration_seconds: int = 60


class AnalyticsSummary(BaseModel):
    total_nodes: int
    by_state: dict[str, int]
    by_role: dict[str, int]
    by_region: dict[str, int]
    avg_load: float
    avg_anomaly_score: float
    total_events: int
    events_last_hour: int
    recoveries_attempted: int
    recoveries_succeeded: int
    mttr_seconds: float
    uptime_ratio: float
    mesh_state: MeshState


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → etcd / Redis + PostgreSQL)
# ---------------------------------------------------------------------------

NODES: dict[str, MeshNode] = {}
EVENTS: list[MeshEvent] = []
QUORUM_THRESHOLD: float = 0.6  # 60% healthy = quorum
HEARTBEAT_DEADLINE_SECONDS: int = 30
MAX_HEARTBEAT_MISSES: int = 3
ANOMALY_THRESHOLD: float = 0.75
RECOVERY_LOG: list[dict[str, Any]] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


def _emit(kind: EventKind, node_id: str | None = None, **details: Any) -> MeshEvent:
    evt = MeshEvent(kind=kind, node_id=node_id, details=details)
    EVENTS.append(evt)
    return evt


def _quorum() -> QuorumStatus:
    total = len(NODES)
    healthy = sum(1 for n in NODES.values() if n.state == NodeState.HEALTHY)
    required = max(1, math.ceil(total * QUORUM_THRESHOLD)) if total else 0
    met = healthy >= required if total else False
    ratio = healthy / total if total else 0.0

    if total == 0:
        state = MeshState.NOMINAL
    elif ratio >= 0.8:
        state = MeshState.NOMINAL
    elif ratio >= QUORUM_THRESHOLD:
        state = MeshState.DEGRADED
    elif ratio > 0:
        state = MeshState.CRITICAL
    else:
        state = MeshState.CRITICAL

    return QuorumStatus(
        total_nodes=total,
        healthy_nodes=healthy,
        quorum_threshold=QUORUM_THRESHOLD,
        quorum_met=met,
        mesh_state=state,
        healthy_ratio=round(ratio, 4),
        required_healthy=required,
    )


def _compute_anomaly(node: MeshNode) -> float:
    """Score 0–1 based on heartbeat misses, load, and recovery history."""
    miss_score = min(node.heartbeat_misses / MAX_HEARTBEAT_MISSES, 1.0)
    load_score = min(node.current_load / node.max_load, 1.0) if node.max_load else 0.0
    recovery_score = min(node.recovery_attempts / 5, 1.0)
    return round(0.5 * miss_score + 0.3 * load_score + 0.2 * recovery_score, 4)


def _build_edges() -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for node in NODES.values():
        for nb in node.neighbours:
            pair = tuple(sorted([node.id, nb]))
            if pair not in seen and nb in NODES:
                seen.add(pair)
                edges.append({"source": pair[0], "target": pair[1]})
    return edges


def _assign_neighbours(node: MeshNode) -> None:
    """Connect new node to up to 3 random healthy peers."""
    peers = [
        n.id
        for n in NODES.values()
        if n.id != node.id and n.state == NodeState.HEALTHY
    ]
    chosen = random.sample(peers, min(3, len(peers)))
    node.neighbours = chosen
    for pid in chosen:
        if node.id not in NODES[pid].neighbours:
            NODES[pid].neighbours.append(node.id)


def _detect_partitions() -> list[PartitionInfo]:
    """Simple BFS-based partition detection on healthy/degraded nodes."""
    active_ids = {
        n.id
        for n in NODES.values()
        if n.state in (NodeState.HEALTHY, NodeState.DEGRADED)
    }
    visited: set[str] = set()
    partitions: list[PartitionInfo] = []

    for nid in active_ids:
        if nid in visited:
            continue
        queue = [nid]
        component: list[str] = []
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            component.append(cur)
            for nb in NODES[cur].neighbours:
                if nb in active_ids and nb not in visited:
                    queue.append(nb)
        partitions.append(
            PartitionInfo(
                partition_id=str(uuid.uuid4()),
                node_ids=component,
                is_majority=len(component) > len(active_ids) / 2,
                size=len(component),
            )
        )
    return partitions


def _attempt_recovery(node: MeshNode) -> dict[str, Any]:
    """Choose strategy and simulate recovery."""
    node.state = NodeState.RECOVERING
    node.recovery_attempts += 1
    _emit(EventKind.RECOVERY_STARTED, node.id, attempt=node.recovery_attempts)

    # Strategy selection
    if node.recovery_attempts <= 1:
        strategy = RecoveryStrategy.RESTART
    elif node.recovery_attempts == 2:
        strategy = RecoveryStrategy.CONFIG_ROLLBACK
    elif node.standby_for or any(
        n.standby_for == node.id for n in NODES.values()
    ):
        strategy = RecoveryStrategy.PROMOTE_STANDBY
    elif node.recovery_attempts <= 4:
        strategy = RecoveryStrategy.REPLACE
    else:
        strategy = RecoveryStrategy.FULL_REBUILD

    # Simulate recovery success (90% first attempt, decaying)
    success_prob = max(0.3, 0.95 - 0.15 * (node.recovery_attempts - 1))
    success = random.random() < success_prob

    result = {
        "node_id": node.id,
        "strategy": strategy.value,
        "attempt": node.recovery_attempts,
        "success": success,
        "timestamp": _now().isoformat(),
    }

    if success:
        node.state = NodeState.HEALTHY
        node.heartbeat_misses = 0
        node.anomaly_score = 0.0
        node.last_heartbeat = _now().isoformat()
        if strategy == RecoveryStrategy.CONFIG_ROLLBACK:
            node.config_version = max(1, node.config_version - 1)
            _emit(EventKind.CONFIG_ROLLBACK, node.id, version=node.config_version)
        _emit(EventKind.RECOVERY_COMPLETE, node.id, strategy=strategy.value)
    else:
        node.state = NodeState.ISOLATED
        _emit(EventKind.RECOVERY_FAILED, node.id, strategy=strategy.value)

    RECOVERY_LOG.append(result)
    return result


def _rebalance() -> RebalanceResult:
    """Redistribute load from overloaded to underloaded healthy nodes."""
    healthy = [n for n in NODES.values() if n.state == NodeState.HEALTHY]
    if not healthy:
        return RebalanceResult(moved=0, from_nodes=[], to_nodes=[], reason="no healthy nodes")

    avg_load = statistics.mean(n.current_load for n in healthy)
    over = [n for n in healthy if n.current_load > avg_load * 1.3]
    under = [n for n in healthy if n.current_load < avg_load * 0.7]

    moved = 0
    from_ids: list[str] = []
    to_ids: list[str] = []

    for o in over:
        for u in under:
            transfer = min(o.current_load - avg_load, avg_load - u.current_load, 10.0)
            if transfer > 0:
                o.current_load -= transfer
                u.current_load += transfer
                moved += 1
                if o.id not in from_ids:
                    from_ids.append(o.id)
                if u.id not in to_ids:
                    to_ids.append(u.id)

    _emit(EventKind.REBALANCE_COMPLETE, details={"moved": moved})
    return RebalanceResult(
        moved=moved,
        from_nodes=from_ids,
        to_nodes=to_ids,
        reason="load_imbalance" if moved else "balanced",
    )


# ---------------------------------------------------------------------------
# Seed Data — 6 starter nodes across 2 regions
# ---------------------------------------------------------------------------

def _seed() -> None:
    seed_specs = [
        ("mesh-guard-alpha", NodeRole.GUARDRAIL, "us-east", ["prompt_filter", "output_scan"], 100.0, 42.0),
        ("mesh-monitor-bravo", NodeRole.MONITOR, "us-east", ["telemetry", "anomaly_detect"], 80.0, 35.0),
        ("mesh-router-charlie", NodeRole.ROUTER, "us-east", ["traffic_split", "fallback"], 120.0, 60.0),
        ("mesh-sentinel-delta", NodeRole.SENTINEL, "eu-west", ["perimeter_scan", "intrusion_detect"], 90.0, 28.0),
        ("mesh-guard-echo", NodeRole.GUARDRAIL, "eu-west", ["tool_sandbox", "memory_guard"], 100.0, 50.0),
        ("mesh-coord-foxtrot", NodeRole.COORDINATOR, "eu-west", ["orchestration", "quorum_vote"], 60.0, 15.0),
    ]
    for name, role, region, caps, max_l, cur_l in seed_specs:
        node = MeshNode(
            name=name,
            role=role,
            region=region,
            capabilities=caps,
            max_load=max_l,
            current_load=cur_l,
        )
        NODES[node.id] = node

    # Wire neighbours
    ids = list(NODES.keys())
    for i, nid in enumerate(ids):
        NODES[nid].neighbours = [ids[(i + 1) % len(ids)], ids[(i - 1) % len(ids)]]
        if len(ids) > 3:
            NODES[nid].neighbours.append(ids[(i + 3) % len(ids)])

    for nid in ids:
        _emit(EventKind.NODE_JOINED, nid, name=NODES[nid].name)


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    q = _quorum()
    return {
        "status": "healthy" if q.quorum_met else "degraded",
        "service": "self-healing-defence-mesh",
        "version": "1.0.0",
        "mesh_state": q.mesh_state.value,
        "nodes": q.total_nodes,
        "healthy_nodes": q.healthy_nodes,
    }


# ---- Topology -----------------------------------------------------------

@app.get("/v1/mesh/topology")
async def get_topology():
    q = _quorum()
    regions: dict[str, list[str]] = defaultdict(list)
    node_views: list[dict[str, Any]] = []
    for n in NODES.values():
        regions[n.region].append(n.id)
        node_views.append({
            "id": n.id,
            "name": n.name,
            "role": n.role.value,
            "state": n.state.value,
            "region": n.region,
            "current_load": n.current_load,
            "anomaly_score": n.anomaly_score,
        })

    return TopologyView(
        nodes=node_views,
        edges=_build_edges(),
        regions=dict(regions),
        mesh_state=q.mesh_state,
        quorum=q,
    )


# ---- Node CRUD ----------------------------------------------------------

@app.post("/v1/mesh/nodes", status_code=status.HTTP_201_CREATED)
async def register_node(reg: NodeRegistration):
    node = MeshNode(
        name=reg.name,
        role=reg.role,
        region=reg.region,
        capabilities=reg.capabilities,
        max_load=reg.max_load,
        standby_for=reg.standby_for,
    )
    NODES[node.id] = node
    _assign_neighbours(node)
    _emit(EventKind.NODE_JOINED, node.id, name=node.name, role=node.role.value)

    # Check quorum change
    q = _quorum()
    if q.quorum_met and any(
        e.kind == EventKind.QUORUM_LOST for e in EVENTS[-10:]
    ):
        _emit(EventKind.QUORUM_RESTORED)

    return {"id": node.id, "state": node.state.value, "neighbours": node.neighbours}


@app.get("/v1/mesh/nodes")
async def list_nodes(
    state: Optional[NodeState] = None,
    role: Optional[NodeRole] = None,
    region: Optional[str] = None,
):
    nodes = list(NODES.values())
    if state:
        nodes = [n for n in nodes if n.state == state]
    if role:
        nodes = [n for n in nodes if n.role == role]
    if region:
        nodes = [n for n in nodes if n.region == region]
    return {"count": len(nodes), "nodes": [n.dict() for n in nodes]}


@app.get("/v1/mesh/nodes/{node_id}")
async def get_node(node_id: str):
    if node_id not in NODES:
        raise HTTPException(404, "Node not found")
    return NODES[node_id].dict()


@app.delete("/v1/mesh/nodes/{node_id}")
async def deregister_node(node_id: str):
    if node_id not in NODES:
        raise HTTPException(404, "Node not found")
    node = NODES.pop(node_id)
    # Remove from neighbours
    for n in NODES.values():
        if node_id in n.neighbours:
            n.neighbours.remove(node_id)
    _emit(EventKind.NODE_LEFT, node_id, name=node.name)

    q = _quorum()
    if not q.quorum_met:
        _emit(EventKind.QUORUM_LOST)

    return {"removed": node_id, "mesh_state": q.mesh_state.value}


# ---- Heartbeat -----------------------------------------------------------

@app.post("/v1/mesh/nodes/{node_id}/heartbeat")
async def report_heartbeat(node_id: str, load: Optional[float] = None):
    if node_id not in NODES:
        raise HTTPException(404, "Node not found")
    node = NODES[node_id]

    if node.state == NodeState.ISOLATED:
        raise HTTPException(409, "Node is isolated — recover first")

    node.last_heartbeat = _now().isoformat()
    node.heartbeat_misses = 0
    if load is not None:
        node.current_load = max(0.0, min(load, node.max_load))
    node.anomaly_score = _compute_anomaly(node)

    if node.state in (NodeState.SUSPECTED, NodeState.DEGRADED):
        node.state = NodeState.HEALTHY

    return {
        "acknowledged": True,
        "state": node.state.value,
        "anomaly_score": node.anomaly_score,
    }


# ---- Simulate heartbeat aging (called by a background task in prod) ------

@app.post("/v1/mesh/_tick")
async def tick_heartbeats():
    """Advance heartbeat clock — simulate time passing.  In production
    this would be a periodic scheduler, not an endpoint."""
    now = _now()
    affected: list[str] = []

    for node in NODES.values():
        if node.state in (NodeState.ISOLATED, NodeState.OFFLINE):
            continue
        last = datetime.fromisoformat(node.last_heartbeat)
        elapsed = (now - last).total_seconds()
        if elapsed > HEARTBEAT_DEADLINE_SECONDS:
            node.heartbeat_misses += 1
            node.anomaly_score = _compute_anomaly(node)
            affected.append(node.id)

            if node.heartbeat_misses >= MAX_HEARTBEAT_MISSES:
                node.state = NodeState.SUSPECTED
                _emit(EventKind.NODE_SUSPECTED, node.id, misses=node.heartbeat_misses)

                # Auto-isolate and recover
                node.state = NodeState.ISOLATED
                _emit(EventKind.NODE_ISOLATED, node.id, reason="heartbeat_timeout")
                _attempt_recovery(node)
            elif node.heartbeat_misses >= 1:
                if node.state == NodeState.HEALTHY:
                    node.state = NodeState.DEGRADED
                _emit(
                    EventKind.HEARTBEAT_MISSED,
                    node.id,
                    misses=node.heartbeat_misses,
                )

    q = _quorum()
    return {
        "ticked": len(affected),
        "affected_nodes": affected,
        "mesh_state": q.mesh_state.value,
        "quorum_met": q.quorum_met,
    }


# ---- Isolation & Recovery ------------------------------------------------

@app.post("/v1/mesh/nodes/{node_id}/isolate")
async def isolate_node(node_id: str, reason: str = "manual"):
    if node_id not in NODES:
        raise HTTPException(404, "Node not found")
    node = NODES[node_id]
    node.state = NodeState.ISOLATED
    _emit(EventKind.NODE_ISOLATED, node_id, reason=reason)

    q = _quorum()
    if not q.quorum_met:
        _emit(EventKind.QUORUM_LOST)

    return {
        "isolated": node_id,
        "mesh_state": q.mesh_state.value,
        "quorum_met": q.quorum_met,
    }


@app.post("/v1/mesh/nodes/{node_id}/recover")
async def recover_node(node_id: str):
    if node_id not in NODES:
        raise HTTPException(404, "Node not found")
    node = NODES[node_id]
    if node.state == NodeState.HEALTHY:
        return {"message": "Node already healthy", "node_id": node_id}

    result = _attempt_recovery(node)

    q = _quorum()
    if q.quorum_met and result["success"]:
        # Check if quorum was just restored
        lost_events = [e for e in EVENTS if e.kind == EventKind.QUORUM_LOST]
        restored_events = [e for e in EVENTS if e.kind == EventKind.QUORUM_RESTORED]
        if len(lost_events) > len(restored_events):
            _emit(EventKind.QUORUM_RESTORED)

    return {**result, "mesh_state": q.mesh_state.value}


# ---- Quorum --------------------------------------------------------------

@app.get("/v1/mesh/quorum")
async def get_quorum():
    return _quorum()


# ---- Events --------------------------------------------------------------

@app.get("/v1/mesh/events")
async def get_events(
    kind: Optional[EventKind] = None,
    node_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    evts = EVENTS[:]
    if kind:
        evts = [e for e in evts if e.kind == kind]
    if node_id:
        evts = [e for e in evts if e.node_id == node_id]
    return {"count": len(evts[-limit:]), "events": [e.dict() for e in evts[-limit:]]}


# ---- Failure Injection ---------------------------------------------------

@app.post("/v1/mesh/simulate-failure")
async def simulate_failure(injection: FailureInjection):
    if injection.target_node_id not in NODES:
        raise HTTPException(404, "Target node not found")
    node = NODES[injection.target_node_id]

    if injection.failure_type == "heartbeat_timeout":
        node.heartbeat_misses = MAX_HEARTBEAT_MISSES
        node.anomaly_score = 1.0
        node.state = NodeState.SUSPECTED
        _emit(EventKind.FAILURE_INJECTED, node.id, failure_type="heartbeat_timeout")
        # Auto-isolate
        node.state = NodeState.ISOLATED
        _emit(EventKind.NODE_ISOLATED, node.id, reason="injected_failure")
        recovery = _attempt_recovery(node)
    elif injection.failure_type == "high_load":
        node.current_load = node.max_load * 1.5
        node.anomaly_score = _compute_anomaly(node)
        node.state = NodeState.DEGRADED
        _emit(EventKind.FAILURE_INJECTED, node.id, failure_type="high_load")
        recovery = None
    elif injection.failure_type == "network_partition":
        node.neighbours = []
        node.state = NodeState.DEGRADED
        _emit(EventKind.FAILURE_INJECTED, node.id, failure_type="network_partition")
        recovery = None
    else:
        node.state = NodeState.OFFLINE
        _emit(EventKind.FAILURE_INJECTED, node.id, failure_type=injection.failure_type)
        recovery = None

    q = _quorum()
    return {
        "injected": injection.failure_type,
        "target": injection.target_node_id,
        "node_state": node.state.value,
        "recovery": recovery,
        "mesh_state": q.mesh_state.value,
    }


# ---- Rebalance -----------------------------------------------------------

@app.post("/v1/mesh/rebalance")
async def trigger_rebalance():
    _emit(EventKind.REBALANCE_TRIGGERED)
    result = _rebalance()
    return result


# ---- Partitions ----------------------------------------------------------

@app.get("/v1/mesh/partitions")
async def detect_partitions():
    parts = _detect_partitions()
    is_partitioned = len(parts) > 1
    if is_partitioned:
        _emit(EventKind.PARTITION_DETECTED, details={"partitions": len(parts)})
    return {
        "partitioned": is_partitioned,
        "partition_count": len(parts),
        "partitions": [p.dict() for p in parts],
    }


# ---- Analytics -----------------------------------------------------------

@app.get("/v1/mesh/analytics")
async def mesh_analytics():
    by_state = Counter(n.state.value for n in NODES.values())
    by_role = Counter(n.role.value for n in NODES.values())
    by_region = Counter(n.region for n in NODES.values())

    loads = [n.current_load for n in NODES.values()]
    anomalies = [n.anomaly_score for n in NODES.values()]

    now = _now()
    hour_ago = (now - timedelta(hours=1)).isoformat()
    events_last_hour = sum(1 for e in EVENTS if e.timestamp >= hour_ago)

    recoveries_attempted = len(RECOVERY_LOG)
    recoveries_succeeded = sum(1 for r in RECOVERY_LOG if r["success"])

    # Mean time to recovery (MTTR) — average seconds between recovery_started and recovery_complete
    mttr_values: list[float] = []
    started_map: dict[str, str] = {}
    for e in EVENTS:
        if e.kind == EventKind.RECOVERY_STARTED and e.node_id:
            started_map[e.node_id] = e.timestamp
        elif e.kind == EventKind.RECOVERY_COMPLETE and e.node_id:
            if e.node_id in started_map:
                s = datetime.fromisoformat(started_map[e.node_id])
                f = datetime.fromisoformat(e.timestamp)
                mttr_values.append((f - s).total_seconds())
                del started_map[e.node_id]

    uptime_nodes = sum(
        1 for n in NODES.values() if n.state in (NodeState.HEALTHY, NodeState.DEGRADED)
    )
    uptime_ratio = uptime_nodes / len(NODES) if NODES else 0.0

    q = _quorum()

    return AnalyticsSummary(
        total_nodes=len(NODES),
        by_state=dict(by_state),
        by_role=dict(by_role),
        by_region=dict(by_region),
        avg_load=round(statistics.mean(loads), 2) if loads else 0.0,
        avg_anomaly_score=round(statistics.mean(anomalies), 4) if anomalies else 0.0,
        total_events=len(EVENTS),
        events_last_hour=events_last_hour,
        recoveries_attempted=recoveries_attempted,
        recoveries_succeeded=recoveries_succeeded,
        mttr_seconds=round(statistics.mean(mttr_values), 2) if mttr_values else 0.0,
        uptime_ratio=round(uptime_ratio, 4),
        mesh_state=q.mesh_state,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8700)
