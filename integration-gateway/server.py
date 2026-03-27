"""
Cross-Phase Integration Gateway — Phase 22 Service 5 of 5
Port: 9604

Unified API gateway federating all 22 phases with service discovery,
rate limiting, circuit breaking, unified authentication, and request
routing.
"""

from __future__ import annotations

import hashlib
import time
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

class ServiceHealth(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"
    unknown = "unknown"


class CircuitState(str, Enum):
    closed = "closed"
    open = "open"
    half_open = "half_open"


class ClientTier(str, Enum):
    free = "free"
    standard = "standard"
    premium = "premium"
    enterprise = "enterprise"


TIER_LIMITS = {
    "free": {"rpm": 60, "burst": 10},
    "standard": {"rpm": 300, "burst": 50},
    "premium": {"rpm": 1000, "burst": 200},
    "enterprise": {"rpm": 5000, "burst": 1000},
}

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ServiceCreate(BaseModel):
    name: str
    phase: int = Field(ge=1, le=50)
    base_url: str
    port: int = Field(ge=1, le=65535)
    capabilities: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServiceRecord(ServiceCreate):
    service_id: str
    health_status: ServiceHealth = ServiceHealth.unknown
    last_heartbeat: Optional[str] = None
    registered_at: str
    updated_at: str


class CircuitBreaker(BaseModel):
    service_id: str
    state: CircuitState = CircuitState.closed
    failure_count: int = 0
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 30
    half_open_max_requests: int = 3
    half_open_requests: int = 0
    last_failure_at: Optional[str] = None
    last_state_change: str = ""


class ApiKeyCreate(BaseModel):
    client_name: str
    tier: ClientTier = ClientTier.free
    scopes: List[str] = Field(default_factory=list)  # list of service_ids or '*'
    rate_limit_override: Optional[int] = None
    expires_at: Optional[str] = None


class ApiKeyRecord(ApiKeyCreate):
    api_key_id: str
    key_hash: str
    revoked: bool = False
    requests_today: int = 0
    total_requests: int = 0
    created_at: str


class RouteRequest(BaseModel):
    target_service_id: str
    method: str = "GET"
    path: str = "/"
    api_key_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class RouteLog(BaseModel):
    log_id: str
    target_service_id: str
    method: str
    path: str
    api_key_id: Optional[str]
    response_status: int
    latency_ms: float
    circuit_state: str
    routed_at: str


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

services: Dict[str, ServiceRecord] = {}
circuit_breakers: Dict[str, CircuitBreaker] = {}  # service_id -> breaker
api_keys: Dict[str, ApiKeyRecord] = {}
route_logs: List[RouteLog] = []
MAX_ROUTE_LOGS = 10000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_breaker(service_id: str) -> CircuitBreaker:
    if service_id not in circuit_breakers:
        circuit_breakers[service_id] = CircuitBreaker(
            service_id=service_id, last_state_change=_now()
        )
    return circuit_breakers[service_id]


def _check_rate_limit(key: ApiKeyRecord) -> bool:
    tier = key.tier.value
    limit = key.rate_limit_override or TIER_LIMITS.get(tier, {}).get("rpm", 60)
    return key.requests_today < limit * 60  # Simplified daily cap


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Cross-Phase Integration Gateway",
    description="Phase 22 — Unified API gateway with service discovery, rate limiting, circuit breaking, auth",
    version="22.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    healthy_count = sum(1 for s in services.values() if s.health_status == ServiceHealth.healthy)
    return {
        "service": "cross-phase-integration-gateway",
        "status": "healthy",
        "phase": 22,
        "port": 9604,
        "stats": {
            "registered_services": len(services),
            "healthy_services": healthy_count,
            "api_keys": len(api_keys),
            "total_routes_logged": len(route_logs),
        },
        "timestamp": _now(),
    }


# -- Service Registry --------------------------------------------------------

@app.post("/v1/services", status_code=201)
def register_service(body: ServiceCreate):
    sid = f"SVC-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = ServiceRecord(**body.dict(), service_id=sid, registered_at=now, updated_at=now)
    services[sid] = record
    _ensure_breaker(sid)
    return record.dict()


@app.get("/v1/services")
def list_services(
    phase: Optional[int] = None,
    health_status: Optional[ServiceHealth] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(services.values())
    if phase is not None:
        results = [s for s in results if s.phase == phase]
    if health_status:
        results = [s for s in results if s.health_status == health_status]
    results.sort(key=lambda s: (s.phase, s.name))
    return {"services": [s.dict() for s in results[:limit]], "total": len(results)}


@app.get("/v1/services/{svc_id}")
def get_service(svc_id: str):
    if svc_id not in services:
        raise HTTPException(404, "Service not found")
    return services[svc_id].dict()


@app.post("/v1/services/{svc_id}/heartbeat")
def service_heartbeat(svc_id: str):
    if svc_id not in services:
        raise HTTPException(404, "Service not found")
    svc = services[svc_id]
    svc.health_status = ServiceHealth.healthy
    svc.last_heartbeat = _now()
    svc.updated_at = _now()

    # Reset circuit breaker on healthy heartbeat
    breaker = _ensure_breaker(svc_id)
    if breaker.state == CircuitState.half_open:
        breaker.state = CircuitState.closed
        breaker.failure_count = 0
        breaker.half_open_requests = 0
        breaker.last_state_change = _now()

    return {"service_id": svc_id, "health_status": svc.health_status.value, "heartbeat_at": svc.last_heartbeat}


# -- API Keys ----------------------------------------------------------------

@app.post("/v1/api-keys", status_code=201)
def create_api_key(body: ApiKeyCreate):
    kid = f"KEY-{uuid.uuid4().hex[:12]}"
    raw_key = f"ave_{uuid.uuid4().hex}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    record = ApiKeyRecord(**body.dict(), api_key_id=kid, key_hash=key_hash, created_at=_now())
    api_keys[kid] = record
    return {**record.dict(), "raw_key": raw_key}  # raw_key returned only at creation


@app.get("/v1/api-keys")
def list_api_keys():
    return {"api_keys": [k.dict() for k in api_keys.values()], "total": len(api_keys)}


@app.post("/v1/api-keys/{key_id}/revoke")
def revoke_api_key(key_id: str):
    if key_id not in api_keys:
        raise HTTPException(404, "API key not found")
    api_keys[key_id].revoked = True
    return {"api_key_id": key_id, "revoked": True}


# -- Routing -----------------------------------------------------------------

@app.post("/v1/route")
def route_request(body: RouteRequest):
    if body.target_service_id not in services:
        raise HTTPException(404, "Target service not found")

    svc = services[body.target_service_id]

    # Auth check
    if body.api_key_id:
        if body.api_key_id not in api_keys:
            raise HTTPException(401, "Invalid API key")
        key = api_keys[body.api_key_id]
        if key.revoked:
            raise HTTPException(403, "API key revoked")
        if key.scopes and "*" not in key.scopes and body.target_service_id not in key.scopes:
            raise HTTPException(403, "API key not scoped for this service")
        if not _check_rate_limit(key):
            raise HTTPException(429, "Rate limit exceeded")
        key.requests_today += 1
        key.total_requests += 1

    # Circuit breaker check
    breaker = _ensure_breaker(body.target_service_id)
    if breaker.state == CircuitState.open:
        # Check if recovery timeout elapsed
        if breaker.last_failure_at:
            try:
                fail_time = datetime.fromisoformat(breaker.last_failure_at)
                elapsed = (datetime.now(timezone.utc) - fail_time).total_seconds()
                if elapsed >= breaker.recovery_timeout_seconds:
                    breaker.state = CircuitState.half_open
                    breaker.half_open_requests = 0
                    breaker.last_state_change = _now()
                else:
                    raise HTTPException(503, f"Circuit open for {svc.name} — retry after {breaker.recovery_timeout_seconds - int(elapsed)}s")
            except (ValueError, TypeError):
                raise HTTPException(503, f"Circuit open for {svc.name}")
        else:
            raise HTTPException(503, f"Circuit open for {svc.name}")

    if breaker.state == CircuitState.half_open:
        if breaker.half_open_requests >= breaker.half_open_max_requests:
            raise HTTPException(503, "Half-open probe limit reached")
        breaker.half_open_requests += 1

    # Simulate routing
    start = time.monotonic()
    response_status = 200 if svc.health_status in (ServiceHealth.healthy, ServiceHealth.unknown) else 503
    latency_ms = round((time.monotonic() - start) * 1000 + 0.5, 2)  # Simulated

    # Update circuit breaker based on response
    if response_status >= 500:
        breaker.failure_count += 1
        breaker.last_failure_at = _now()
        if breaker.failure_count >= breaker.failure_threshold:
            breaker.state = CircuitState.open
            breaker.last_state_change = _now()
    else:
        if breaker.state == CircuitState.half_open:
            breaker.state = CircuitState.closed
            breaker.failure_count = 0
            breaker.last_state_change = _now()

    # Log
    log = RouteLog(
        log_id=f"LOG-{uuid.uuid4().hex[:8]}",
        target_service_id=body.target_service_id,
        method=body.method,
        path=body.path,
        api_key_id=body.api_key_id,
        response_status=response_status,
        latency_ms=latency_ms,
        circuit_state=breaker.state.value,
        routed_at=_now(),
    )
    route_logs.append(log)
    if len(route_logs) > MAX_ROUTE_LOGS:
        route_logs.pop(0)

    return {
        "log_id": log.log_id,
        "target_service": svc.name,
        "response_status": response_status,
        "latency_ms": latency_ms,
        "circuit_state": breaker.state.value,
    }


# -- Circuit Breakers --------------------------------------------------------

@app.get("/v1/circuit-breakers")
def list_circuit_breakers():
    breakers = []
    for sid, breaker in circuit_breakers.items():
        svc_name = services[sid].name if sid in services else "unknown"
        breakers.append({
            "service_id": sid,
            "service_name": svc_name,
            "state": breaker.state.value,
            "failure_count": breaker.failure_count,
            "failure_threshold": breaker.failure_threshold,
            "last_failure_at": breaker.last_failure_at,
            "last_state_change": breaker.last_state_change,
        })
    return {"circuit_breakers": breakers, "total": len(breakers)}


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    phase_dist: Dict[int, int] = defaultdict(int)
    health_dist: Dict[str, int] = defaultdict(int)
    for s in services.values():
        phase_dist[s.phase] += 1
        health_dist[s.health_status.value] += 1

    tier_dist: Dict[str, int] = defaultdict(int)
    for k in api_keys.values():
        tier_dist[k.tier.value] += 1

    status_dist: Dict[int, int] = defaultdict(int)
    latencies: List[float] = []
    for log in route_logs:
        status_dist[log.response_status] += 1
        latencies.append(log.latency_ms)

    circuit_dist: Dict[str, int] = defaultdict(int)
    for b in circuit_breakers.values():
        circuit_dist[b.state.value] += 1

    return {
        "services": {
            "total": len(services),
            "phase_distribution": dict(phase_dist),
            "health_distribution": dict(health_dist),
        },
        "api_keys": {
            "total": len(api_keys),
            "active": sum(1 for k in api_keys.values() if not k.revoked),
            "tier_distribution": dict(tier_dist),
        },
        "routing": {
            "total_requests": len(route_logs),
            "status_distribution": dict(status_dist),
            "avg_latency_ms": round(sum(latencies) / max(len(latencies), 1), 2) if latencies else None,
        },
        "circuit_breakers": {
            "total": len(circuit_breakers),
            "state_distribution": dict(circuit_dist),
        },
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9604)
