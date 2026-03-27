"""
API Gateway & Service Mesh — Core gateway server.

Unified API gateway providing authentication, rate limiting, circuit
breaking, and service discovery across all NAIL microservices.
Every external and internal request flows through this gateway,
which enforces security policies, manages traffic, and routes to
dynamically-registered backend services.
"""

from __future__ import annotations

import hashlib
import math
import random
import secrets
import statistics
import time
import uuid
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NAIL API Gateway & Service Mesh",
    description=(
        "Unified API gateway — authentication, rate limiting, circuit "
        "breaking, service discovery, and request proxying."
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
# Constants / Enums
# ---------------------------------------------------------------------------


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    READONLY = "readonly"


class RateLimitTier(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


TIER_LIMITS: dict[RateLimitTier, dict[str, Any]] = {
    RateLimitTier.FREE: {"requests_per_minute": 60, "burst_capacity": 120, "refill_rate": 1.0},
    RateLimitTier.STANDARD: {"requests_per_minute": 300, "burst_capacity": 600, "refill_rate": 5.0},
    RateLimitTier.PROFESSIONAL: {"requests_per_minute": 1200, "burst_capacity": 2400, "refill_rate": 20.0},
    RateLimitTier.ENTERPRISE: {"requests_per_minute": 6000, "burst_capacity": 12000, "refill_rate": 100.0},
}

ROLE_PERMISSIONS: dict[Role, list[str]] = {
    Role.ADMIN: ["read", "write", "delete", "admin", "audit"],
    Role.OPERATOR: ["read", "write", "delete"],
    Role.ANALYST: ["read", "write"],
    Role.AUDITOR: ["read", "audit"],
    Role.READONLY: ["read"],
}


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: f"KEY-{uuid.uuid4().hex[:12].upper()}")
    key: str = Field(default_factory=lambda: f"nail_{secrets.token_urlsafe(32)}")
    name: str = ""
    role: Role = Role.READONLY
    tier: RateLimitTier = RateLimitTier.FREE
    scopes: list[str] = Field(default_factory=list)
    active: bool = True
    request_count: int = 0
    last_used: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None


class KeyCreate(BaseModel):
    name: str
    role: Role = Role.READONLY
    tier: RateLimitTier = RateLimitTier.FREE
    scopes: list[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = None


class BackendService(BaseModel):
    id: str = Field(default_factory=lambda: f"SVC-{uuid.uuid4().hex[:8].upper()}")
    name: str
    base_url: str
    health_url: str = ""
    version: str = "1.0.0"
    port: int = 8000
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: Optional[str] = None
    consecutive_failures: int = 0
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ServiceRegister(BaseModel):
    name: str
    base_url: str
    health_url: str = ""
    version: str = "1.0.0"
    port: int = 8000
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class CircuitBreaker(BaseModel):
    service_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    failure_threshold: int = 5
    recovery_timeout_sec: int = 30
    last_failure: Optional[str] = None
    last_state_change: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    half_open_attempts: int = 0
    total_trips: int = 0


class TokenBucket(BaseModel):
    key_id: str
    tier: RateLimitTier
    tokens: float
    capacity: float
    refill_rate: float  # tokens per second
    last_refill: float = Field(default_factory=time.time)


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: str  # auth_success, auth_failure, rate_limited, circuit_trip, proxy_request, etc
    key_id: str = ""
    service_id: str = ""
    path: str = ""
    method: str = ""
    status_code: int = 0
    latency_ms: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class ProxyResult(BaseModel):
    service: str = ""
    path: str = ""
    status_code: int = 200
    latency_ms: float = 0.0
    body: dict[str, Any] = Field(default_factory=dict)
    proxied: bool = True


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → Redis + PostgreSQL + Consul)
# ---------------------------------------------------------------------------

API_KEYS: dict[str, APIKey] = {}  # key_id → APIKey
KEY_LOOKUP: dict[str, str] = {}  # key_value → key_id
SERVICES: dict[str, BackendService] = {}
CIRCUITS: dict[str, CircuitBreaker] = {}  # service_id → CircuitBreaker
BUCKETS: dict[str, TokenBucket] = {}  # key_id → TokenBucket
AUDIT_LOG: list[AuditEntry] = []
REQUEST_LOG: list[dict[str, Any]] = []  # Recent requests for analytics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731
_rng = random.Random(42)


def _audit(action: str, **kwargs: Any) -> None:
    entry = AuditEntry(action=action, **kwargs)
    AUDIT_LOG.append(entry)
    if len(AUDIT_LOG) > 10000:
        AUDIT_LOG.pop(0)


def _log_request(service: str, method: str, path: str, status_code: int, latency_ms: float) -> None:
    REQUEST_LOG.append({
        "service": service,
        "method": method,
        "path": path,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
        "timestamp": _now().isoformat(),
    })
    if len(REQUEST_LOG) > 5000:
        REQUEST_LOG.pop(0)


def _authenticate(api_key_value: str) -> APIKey:
    """Validate API key and return the key object."""
    if not api_key_value:
        raise HTTPException(401, "Missing API key")

    key_id = KEY_LOOKUP.get(api_key_value)
    if not key_id or key_id not in API_KEYS:
        _audit("auth_failure", details={"reason": "invalid_key"})
        raise HTTPException(401, "Invalid API key")

    key = API_KEYS[key_id]
    if not key.active:
        _audit("auth_failure", key_id=key_id, details={"reason": "key_revoked"})
        raise HTTPException(403, "API key has been revoked")

    if key.expires_at and key.expires_at < _now().isoformat():
        _audit("auth_failure", key_id=key_id, details={"reason": "key_expired"})
        raise HTTPException(403, "API key has expired")

    # Update usage
    key.request_count += 1
    key.last_used = _now().isoformat()

    return key


def _check_rate_limit(key: APIKey) -> None:
    """Token bucket rate limiting."""
    bucket = BUCKETS.get(key.id)
    if not bucket:
        tier_config = TIER_LIMITS[key.tier]
        bucket = TokenBucket(
            key_id=key.id,
            tier=key.tier,
            tokens=float(tier_config["burst_capacity"]),
            capacity=float(tier_config["burst_capacity"]),
            refill_rate=tier_config["refill_rate"],
        )
        BUCKETS[key.id] = bucket

    # Refill tokens
    now = time.time()
    elapsed = now - bucket.last_refill
    bucket.tokens = min(bucket.capacity, bucket.tokens + elapsed * bucket.refill_rate)
    bucket.last_refill = now

    # Consume token
    if bucket.tokens < 1.0:
        _audit("rate_limited", key_id=key.id, details={"tier": key.tier.value, "tokens": bucket.tokens})
        raise HTTPException(
            429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(int(bucket.capacity)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(now + (1.0 / bucket.refill_rate))),
                "Retry-After": str(int(1.0 / bucket.refill_rate)),
            },
        )

    bucket.tokens -= 1.0


def _check_circuit(service_id: str) -> None:
    """Check circuit breaker state for a service."""
    circuit = CIRCUITS.get(service_id)
    if not circuit:
        return  # No circuit = closed (pass through)

    if circuit.state == CircuitState.OPEN:
        # Check if recovery timeout has elapsed
        if circuit.last_failure:
            last = datetime.fromisoformat(circuit.last_failure)
            elapsed = (_now() - last).total_seconds()
            if elapsed >= circuit.recovery_timeout_sec:
                # Transition to half-open
                circuit.state = CircuitState.HALF_OPEN
                circuit.last_state_change = _now().isoformat()
                circuit.half_open_attempts = 0
            else:
                retry_after = circuit.recovery_timeout_sec - int(elapsed)
                raise HTTPException(
                    503,
                    detail=f"Service '{service_id}' circuit is OPEN — backend unavailable",
                    headers={"Retry-After": str(retry_after)},
                )
        else:
            raise HTTPException(503, f"Service '{service_id}' circuit is OPEN")

    elif circuit.state == CircuitState.HALF_OPEN:
        circuit.half_open_attempts += 1
        if circuit.half_open_attempts > 1:
            raise HTTPException(503, "Circuit half-open — only one probe request allowed")


def _record_success(service_id: str) -> None:
    """Record a successful request for circuit breaker."""
    circuit = CIRCUITS.get(service_id)
    if not circuit:
        return

    if circuit.state == CircuitState.HALF_OPEN:
        circuit.state = CircuitState.CLOSED
        circuit.failure_count = 0
        circuit.last_state_change = _now().isoformat()
    elif circuit.state == CircuitState.CLOSED:
        circuit.failure_count = max(0, circuit.failure_count - 1)


def _record_failure(service_id: str) -> None:
    """Record a failed request for circuit breaker."""
    circuit = CIRCUITS.get(service_id)
    if not circuit:
        circuit = CircuitBreaker(service_id=service_id)
        CIRCUITS[service_id] = circuit

    circuit.failure_count += 1
    circuit.last_failure = _now().isoformat()

    if circuit.state == CircuitState.HALF_OPEN:
        circuit.state = CircuitState.OPEN
        circuit.total_trips += 1
        circuit.last_state_change = _now().isoformat()
        _audit("circuit_trip", service_id=service_id, details={"reason": "half_open_failure"})

    elif circuit.state == CircuitState.CLOSED and circuit.failure_count >= circuit.failure_threshold:
        circuit.state = CircuitState.OPEN
        circuit.total_trips += 1
        circuit.last_state_change = _now().isoformat()
        _audit("circuit_trip", service_id=service_id,
               details={"failures": circuit.failure_count, "threshold": circuit.failure_threshold})


def _simulate_proxy(service: BackendService, method: str, path: str) -> ProxyResult:
    """Simulate proxying a request to a backend service.
    Production → actual HTTP client (httpx/aiohttp) forwarding.
    """
    start = time.time()

    # Simulate latency and occasional errors
    latency = _rng.uniform(5, 150)
    time.sleep(min(latency / 1000, 0.05))  # Cap actual sleep

    if service.status == ServiceStatus.UNHEALTHY:
        _record_failure(service.id)
        elapsed = (time.time() - start) * 1000
        _log_request(service.name, method, path, 502, elapsed)
        return ProxyResult(service=service.name, path=path, status_code=502,
                           latency_ms=round(elapsed, 2),
                           body={"error": "Bad Gateway", "detail": "Backend service unhealthy"},
                           proxied=True)

    error_chance = 0.05 if service.status == ServiceStatus.HEALTHY else 0.15
    if _rng.random() < error_chance:
        _record_failure(service.id)
        elapsed = (time.time() - start) * 1000
        _log_request(service.name, method, path, 500, elapsed)
        return ProxyResult(service=service.name, path=path, status_code=500,
                           latency_ms=round(elapsed, 2),
                           body={"error": "Internal Server Error", "detail": "Upstream error"},
                           proxied=True)

    _record_success(service.id)
    elapsed = (time.time() - start) * 1000
    _log_request(service.name, method, path, 200, elapsed)

    return ProxyResult(
        service=service.name, path=path, status_code=200,
        latency_ms=round(elapsed, 2),
        body={"message": f"Proxied {method} /{path} to {service.name}", "simulated": True},
    )


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    rng = random.Random(42)

    # Seed API keys
    key_defs = [
        ("NAIL Admin Key", Role.ADMIN, RateLimitTier.ENTERPRISE),
        ("Ops Team Key", Role.OPERATOR, RateLimitTier.PROFESSIONAL),
        ("Analyst Key", Role.ANALYST, RateLimitTier.STANDARD),
        ("Auditor Key", Role.AUDITOR, RateLimitTier.STANDARD),
        ("Public Read Key", Role.READONLY, RateLimitTier.FREE),
    ]

    for name, role, tier in key_defs:
        key = APIKey(name=name, role=role, tier=tier,
                     scopes=ROLE_PERMISSIONS[role],
                     request_count=rng.randint(0, 5000))
        API_KEYS[key.id] = key
        KEY_LOOKUP[key.key] = key.id

    # Seed backend services
    service_defs = [
        ("threat-intel", "http://threat-intel:8700", 8700, "Threat Intelligence Aggregator"),
        ("autonomous-redteam", "http://autonomous-redteam:8701", 8701, "Autonomous Red Team"),
        ("defence-mesh", "http://defence-mesh:8702", 8702, "Defence Mesh Orchestrator"),
        ("predictive-engine", "http://predictive-engine:8703", 8703, "Predictive Threat Engine"),
        ("incident-commander", "http://incident-commander:9002", 9002, "Autonomous Incident Commander"),
        ("ethical-reasoning", "http://ethical-reasoning:9102", 9102, "Ethical Reasoning Framework"),
        ("civilisational-risk", "http://civilisational-risk:9103", 9103, "Civilisational Risk Dashboard"),
        ("standards-evolution", "http://standards-evolution:9104", 9104, "Autonomous Standards Evolution"),
        ("recursive-self-improvement", "http://recursive-self-improvement:9100", 9100, "Recursive Self-Improvement"),
        ("temporal-forensics", "http://temporal-forensics:9101", 9101, "Temporal Attack Forensics"),
    ]

    statuses = [ServiceStatus.HEALTHY, ServiceStatus.HEALTHY, ServiceStatus.HEALTHY,
                ServiceStatus.HEALTHY, ServiceStatus.DEGRADED, ServiceStatus.HEALTHY,
                ServiceStatus.HEALTHY, ServiceStatus.HEALTHY, ServiceStatus.HEALTHY, ServiceStatus.HEALTHY]

    for i, (name, url, port, desc) in enumerate(service_defs):
        svc = BackendService(
            name=name, base_url=url, health_url=f"{url}/health",
            port=port, description=desc, version="1.0.0",
            status=statuses[i], tags=["nail", "ave"],
            last_health_check=_now().isoformat(),
        )
        SERVICES[svc.id] = svc

        # Initialise circuit breakers
        circuit = CircuitBreaker(service_id=svc.id)
        if svc.status == ServiceStatus.DEGRADED:
            circuit.failure_count = 3
        CIRCUITS[svc.id] = circuit

    # Seed audit log
    for i in range(50):
        actions = ["auth_success", "proxy_request", "auth_success", "proxy_request", "rate_limited"]
        _audit(
            rng.choice(actions),
            key_id=rng.choice(list(API_KEYS.keys())),
            service_id=rng.choice(list(SERVICES.keys())),
            path=f"/v1/{rng.choice(['threats', 'incidents', 'defences', 'analytics'])}",
            method=rng.choice(["GET", "POST"]),
            status_code=rng.choice([200, 200, 200, 201, 429, 500]),
            latency_ms=round(rng.uniform(5, 200), 2),
        )


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    healthy_svcs = sum(1 for s in SERVICES.values() if s.status == ServiceStatus.HEALTHY)
    open_circuits = sum(1 for c in CIRCUITS.values() if c.state == CircuitState.OPEN)

    return {
        "status": "healthy",
        "service": "api-gateway-service-mesh",
        "version": "1.0.0",
        "registered_services": len(SERVICES),
        "healthy_services": healthy_svcs,
        "open_circuits": open_circuits,
        "api_keys": len(API_KEYS),
        "audit_entries": len(AUDIT_LOG),
    }


# ---- API Keys ---------------------------------------------------------------

@app.post("/v1/keys", status_code=status.HTTP_201_CREATED)
async def create_key(data: KeyCreate):
    key = APIKey(
        name=data.name,
        role=data.role,
        tier=data.tier,
        scopes=data.scopes or ROLE_PERMISSIONS[data.role],
    )
    if data.expires_in_days:
        key.expires_at = (_now() + timedelta(days=data.expires_in_days)).isoformat()

    API_KEYS[key.id] = key
    KEY_LOOKUP[key.key] = key.id

    _audit("key_created", key_id=key.id, details={"name": data.name, "role": data.role.value})

    return {
        "id": key.id,
        "key": key.key,  # Only returned on creation
        "name": key.name,
        "role": key.role.value,
        "tier": key.tier.value,
        "expires_at": key.expires_at,
    }


@app.get("/v1/keys")
async def list_keys():
    return {
        "count": len(API_KEYS),
        "keys": [
            {"id": k.id, "name": k.name, "role": k.role.value,
             "tier": k.tier.value, "active": k.active,
             "request_count": k.request_count, "last_used": k.last_used}
            for k in API_KEYS.values()
        ],
    }


@app.delete("/v1/keys/{key_id}")
async def revoke_key(key_id: str):
    if key_id not in API_KEYS:
        raise HTTPException(404, "API key not found")

    API_KEYS[key_id].active = False
    _audit("key_revoked", key_id=key_id)

    return {"id": key_id, "status": "revoked"}


# ---- Service Registry -------------------------------------------------------

@app.post("/v1/services", status_code=status.HTTP_201_CREATED)
async def register_service(data: ServiceRegister):
    # Check for duplicate name
    existing = [s for s in SERVICES.values() if s.name == data.name]
    if existing:
        raise HTTPException(409, f"Service '{data.name}' already registered")

    svc = BackendService(
        name=data.name,
        base_url=data.base_url,
        health_url=data.health_url or f"{data.base_url}/health",
        version=data.version,
        port=data.port,
        description=data.description,
        tags=data.tags,
        status=ServiceStatus.UNKNOWN,
    )
    SERVICES[svc.id] = svc

    # Initialise circuit breaker
    CIRCUITS[svc.id] = CircuitBreaker(service_id=svc.id)

    _audit("service_registered", service_id=svc.id, details={"name": data.name, "url": data.base_url})

    return {"id": svc.id, "name": svc.name, "status": svc.status.value}


@app.get("/v1/services")
async def list_services(svc_status: Optional[ServiceStatus] = Query(None, alias="status"),
                        tag: Optional[str] = None):
    svcs = list(SERVICES.values())
    if svc_status:
        svcs = [s for s in svcs if s.status == svc_status]
    if tag:
        svcs = [s for s in svcs if tag in s.tags]

    return {
        "count": len(svcs),
        "services": [
            {"id": s.id, "name": s.name, "base_url": s.base_url,
             "port": s.port, "version": s.version, "status": s.status.value,
             "description": s.description, "tags": s.tags,
             "last_health_check": s.last_health_check}
            for s in svcs
        ],
    }


@app.delete("/v1/services/{service_id}")
async def deregister_service(service_id: str):
    if service_id not in SERVICES:
        raise HTTPException(404, "Service not found")

    svc = SERVICES.pop(service_id)
    CIRCUITS.pop(service_id, None)
    _audit("service_deregistered", service_id=service_id, details={"name": svc.name})

    return {"id": service_id, "name": svc.name, "status": "deregistered"}


@app.get("/v1/services/{service_id}/health")
async def check_service_health(service_id: str):
    if service_id not in SERVICES:
        raise HTTPException(404, "Service not found")

    svc = SERVICES[service_id]
    # Simulate health check (production → actual HTTP call to health_url)
    svc.last_health_check = _now().isoformat()

    if svc.status == ServiceStatus.UNHEALTHY:
        svc.consecutive_failures += 1
    else:
        svc.consecutive_failures = 0

    return {
        "service_id": service_id,
        "name": svc.name,
        "status": svc.status.value,
        "consecutive_failures": svc.consecutive_failures,
        "last_check": svc.last_health_check,
        "health_url": svc.health_url,
    }


# ---- Circuit Breakers -------------------------------------------------------

@app.get("/v1/circuits")
async def list_circuits():
    return {
        "count": len(CIRCUITS),
        "circuits": [
            {"service_id": c.service_id,
             "service_name": SERVICES[c.service_id].name if c.service_id in SERVICES else "unknown",
             "state": c.state.value,
             "failure_count": c.failure_count,
             "failure_threshold": c.failure_threshold,
             "total_trips": c.total_trips,
             "last_state_change": c.last_state_change}
            for c in CIRCUITS.values()
        ],
    }


@app.post("/v1/circuits/{service_id}/reset")
async def reset_circuit(service_id: str):
    if service_id not in CIRCUITS:
        raise HTTPException(404, "Circuit not found")

    circuit = CIRCUITS[service_id]
    circuit.state = CircuitState.CLOSED
    circuit.failure_count = 0
    circuit.half_open_attempts = 0
    circuit.last_state_change = _now().isoformat()

    _audit("circuit_reset", service_id=service_id)

    return {"service_id": service_id, "state": "closed", "message": "Circuit reset to closed"}


# ---- Rate Limits ------------------------------------------------------------

@app.get("/v1/rate-limits")
async def get_rate_limits():
    return {
        "tiers": {
            tier.value: {
                "requests_per_minute": config["requests_per_minute"],
                "burst_capacity": config["burst_capacity"],
                "refill_rate_per_second": config["refill_rate"],
            }
            for tier, config in TIER_LIMITS.items()
        },
        "active_buckets": len(BUCKETS),
    }


# ---- Proxy ------------------------------------------------------------------

@app.api_route("/v1/proxy/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_request(service_name: str, path: str, request: Request,
                        x_api_key: str = Header("", alias="X-API-Key")):
    # Find service by name
    svc = None
    for s in SERVICES.values():
        if s.name == service_name:
            svc = s
            break

    if not svc:
        raise HTTPException(404, f"Service '{service_name}' not found in registry")

    # Authentication (skip for health checks in dev mode)
    key = None
    if x_api_key:
        key = _authenticate(x_api_key)
        _check_rate_limit(key)
        _audit("auth_success", key_id=key.id, path=f"/v1/proxy/{service_name}/{path}",
               method=request.method)

    # Circuit breaker check
    _check_circuit(svc.id)

    # Proxy the request
    result = _simulate_proxy(svc, request.method, path)

    _audit("proxy_request", key_id=key.id if key else "",
           service_id=svc.id, path=path, method=request.method,
           status_code=result.status_code, latency_ms=result.latency_ms)

    if result.status_code >= 500:
        raise HTTPException(result.status_code, detail=result.body)

    return {
        "proxied": True,
        "service": result.service,
        "path": result.path,
        "status_code": result.status_code,
        "latency_ms": result.latency_ms,
        "response": result.body,
    }


# ---- Audit Log --------------------------------------------------------------

@app.get("/v1/audit")
async def query_audit(
    action: Optional[str] = None,
    key_id: Optional[str] = None,
    service_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    entries = list(AUDIT_LOG)
    if action:
        entries = [e for e in entries if e.action == action]
    if key_id:
        entries = [e for e in entries if e.key_id == key_id]
    if service_id:
        entries = [e for e in entries if e.service_id == service_id]

    entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    return {
        "count": len(entries),
        "entries": [
            {"id": e.id, "timestamp": e.timestamp, "action": e.action,
             "key_id": e.key_id, "service_id": e.service_id,
             "path": e.path, "method": e.method,
             "status_code": e.status_code, "latency_ms": e.latency_ms}
            for e in entries
        ],
    }


# ---- Analytics --------------------------------------------------------------

@app.get("/v1/analytics")
async def gateway_analytics():
    # Request stats
    recent = REQUEST_LOG[-1000:]
    total_requests = len(recent)
    error_count = sum(1 for r in recent if r["status_code"] >= 400)
    latencies = [r["latency_ms"] for r in recent]

    p50 = round(statistics.median(latencies), 2) if latencies else 0
    p95 = round(sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else 0, 2)
    p99 = round(sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else 0, 2)

    by_service = Counter(r["service"] for r in recent)
    by_status = Counter(r["status_code"] for r in recent)
    by_method = Counter(r["method"] for r in recent)

    # Top consumers
    key_usage = Counter()
    for entry in AUDIT_LOG:
        if entry.key_id:
            key_usage[entry.key_id] += 1
    top_consumers = [
        {"key_id": kid, "name": API_KEYS[kid].name if kid in API_KEYS else "unknown", "requests": cnt}
        for kid, cnt in key_usage.most_common(10)
    ]

    # Circuit states
    circuit_states = Counter(c.state.value for c in CIRCUITS.values())

    # Service health
    health_counts = Counter(s.status.value for s in SERVICES.values())

    return {
        "total_requests_tracked": total_requests,
        "error_rate_pct": round(error_count / max(total_requests, 1) * 100, 2),
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "latency_p99_ms": p99,
        "requests_by_service": dict(by_service),
        "requests_by_status": dict(by_status),
        "requests_by_method": dict(by_method),
        "top_consumers": top_consumers,
        "circuit_states": dict(circuit_states),
        "service_health": dict(health_counts),
        "registered_services": len(SERVICES),
        "active_api_keys": sum(1 for k in API_KEYS.values() if k.active),
        "total_audit_entries": len(AUDIT_LOG),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9200)
