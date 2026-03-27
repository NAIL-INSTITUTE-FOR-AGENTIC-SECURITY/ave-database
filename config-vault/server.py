"""
Distributed Configuration Vault — Phase 23 Service 3 of 5
Port: 9702

Encrypted configuration management with versioning, rollback, audit trails,
environment-aware secret rotation, and policy-based access control.
"""

from __future__ import annotations

import hashlib
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

class AccessPolicy(str, Enum):
    read_only = "read_only"
    read_write = "read_write"
    admin = "admin"
    rotate_only = "rotate_only"


class RotationPolicy(str, Enum):
    manual = "manual"
    scheduled = "scheduled"
    on_access = "on_access"


class AuditAction(str, Enum):
    config_set = "config_set"
    config_read = "config_read"
    config_delete = "config_delete"
    config_rollback = "config_rollback"
    secret_created = "secret_created"
    secret_rotated = "secret_rotated"
    secret_read = "secret_read"
    namespace_created = "namespace_created"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class NamespaceCreate(BaseModel):
    name: str
    environment: str = "production"
    description: str = ""
    default_policy: AccessPolicy = AccessPolicy.read_only


class NamespaceRecord(NamespaceCreate):
    namespace_id: str
    config_count: int = 0
    secret_count: int = 0
    created_at: str


class ConfigCreate(BaseModel):
    key: str
    value: str
    namespace: str
    environment: str = "production"
    encrypted: bool = False
    actor: str = "system"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfigVersion(BaseModel):
    version: int
    value_hash: str
    encrypted_value: str  # In production: actual AES-256-GCM ciphertext
    changed_by: str
    changed_at: str


class ConfigRecord(BaseModel):
    config_id: str
    key: str
    namespace: str
    environment: str
    current_value: str
    encrypted: bool
    version: int = 1
    history: List[ConfigVersion] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class SecretCreate(BaseModel):
    key: str
    value: str
    namespace: str
    environment: str = "production"
    rotation_policy: RotationPolicy = RotationPolicy.manual
    rotation_interval_hours: int = Field(default=720, ge=1)
    actor: str = "system"


class SecretRecord(BaseModel):
    secret_id: str
    key: str
    namespace: str
    environment: str
    value_hash: str
    encrypted_value: str
    rotation_policy: RotationPolicy
    rotation_interval_hours: int
    access_count: int = 0
    version: int = 1
    last_rotated_at: str
    next_rotation_at: Optional[str] = None
    created_at: str
    updated_at: str


class AuditEntry(BaseModel):
    audit_id: str
    actor: str
    action: AuditAction
    key: str
    namespace: str
    old_value_hash: str = ""
    new_value_hash: str = ""
    timestamp: str


class RollbackRequest(BaseModel):
    target_version: int
    actor: str = "system"


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

namespaces: Dict[str, NamespaceRecord] = {}
configs: Dict[str, ConfigRecord] = {}         # config_id -> record
config_index: Dict[str, str] = {}             # "namespace:key" -> config_id
secrets: Dict[str, SecretRecord] = {}         # secret_id -> record
secret_index: Dict[str, str] = {}             # "namespace:key" -> secret_id
audit_log: List[AuditEntry] = []
MAX_AUDIT = 10000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _encrypt(value: str) -> str:
    """Simulated AES-256-GCM encryption. Production: use cryptography library."""
    return f"ENC[{_hash(value)[:16]}:{value[:4]}...]"


def _audit(actor: str, action: AuditAction, key: str, namespace: str,
           old_hash: str = "", new_hash: str = ""):
    entry = AuditEntry(
        audit_id=f"AUD-{uuid.uuid4().hex[:8]}",
        actor=actor, action=action, key=key, namespace=namespace,
        old_value_hash=old_hash, new_value_hash=new_hash,
        timestamp=_now(),
    )
    audit_log.append(entry)
    if len(audit_log) > MAX_AUDIT:
        audit_log.pop(0)


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Distributed Configuration Vault",
    description="Phase 23 — Encrypted config management with versioning, rollback, audit, secret rotation",
    version="23.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {
        "service": "distributed-configuration-vault",
        "status": "healthy",
        "phase": 23,
        "port": 9702,
        "stats": {
            "namespaces": len(namespaces),
            "configs": len(configs),
            "secrets": len(secrets),
            "audit_entries": len(audit_log),
        },
        "timestamp": _now(),
    }


# -- Namespaces --------------------------------------------------------------

@app.post("/v1/namespaces", status_code=201)
def create_namespace(body: NamespaceCreate):
    if any(ns.name == body.name for ns in namespaces.values()):
        raise HTTPException(409, f"Namespace '{body.name}' already exists")
    nid = f"NS-{uuid.uuid4().hex[:12]}"
    record = NamespaceRecord(**body.dict(), namespace_id=nid, created_at=_now())
    namespaces[nid] = record
    _audit("system", AuditAction.namespace_created, body.name, body.name)
    return record.dict()


@app.get("/v1/namespaces")
def list_namespaces():
    # Update counts
    for ns in namespaces.values():
        ns.config_count = sum(1 for c in configs.values() if c.namespace == ns.name)
        ns.secret_count = sum(1 for s in secrets.values() if s.namespace == ns.name)
    return {"namespaces": [ns.dict() for ns in namespaces.values()], "total": len(namespaces)}


# -- Configs -----------------------------------------------------------------

@app.post("/v1/configs", status_code=201)
def set_config(body: ConfigCreate):
    idx_key = f"{body.namespace}:{body.key}"

    if idx_key in config_index:
        # Update existing
        cid = config_index[idx_key]
        record = configs[cid]
        old_hash = _hash(record.current_value)
        new_hash = _hash(body.value)

        record.version += 1
        record.history.append(ConfigVersion(
            version=record.version,
            value_hash=new_hash,
            encrypted_value=_encrypt(body.value) if body.encrypted else body.value,
            changed_by=body.actor,
            changed_at=_now(),
        ))
        record.current_value = body.value
        record.encrypted = body.encrypted
        record.updated_at = _now()
        _audit(body.actor, AuditAction.config_set, body.key, body.namespace, old_hash, new_hash)
        return record.dict()

    # New config
    cid = f"CFG-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = ConfigRecord(
        config_id=cid, key=body.key, namespace=body.namespace,
        environment=body.environment, current_value=body.value,
        encrypted=body.encrypted, version=1,
        metadata=body.metadata, created_at=now, updated_at=now,
    )
    record.history.append(ConfigVersion(
        version=1,
        value_hash=_hash(body.value),
        encrypted_value=_encrypt(body.value) if body.encrypted else body.value,
        changed_by=body.actor,
        changed_at=now,
    ))
    configs[cid] = record
    config_index[idx_key] = cid
    _audit(body.actor, AuditAction.config_set, body.key, body.namespace, "", _hash(body.value))
    return record.dict()


@app.get("/v1/configs")
def list_configs(
    namespace: Optional[str] = None,
    environment: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(configs.values())
    if namespace:
        results = [c for c in results if c.namespace == namespace]
    if environment:
        results = [c for c in results if c.environment == environment]
    results.sort(key=lambda c: c.key)
    return {"configs": [c.dict() for c in results[:limit]], "total": len(results)}


@app.get("/v1/configs/{key}")
def get_config(key: str, namespace: str = "default"):
    idx_key = f"{namespace}:{key}"
    if idx_key not in config_index:
        raise HTTPException(404, f"Config '{key}' not found in namespace '{namespace}'")
    record = configs[config_index[idx_key]]
    _audit("reader", AuditAction.config_read, key, namespace)
    return record.dict()


@app.post("/v1/configs/{key}/rollback")
def rollback_config(key: str, body: RollbackRequest, namespace: str = "default"):
    idx_key = f"{namespace}:{key}"
    if idx_key not in config_index:
        raise HTTPException(404, f"Config '{key}' not found")
    record = configs[config_index[idx_key]]
    target_ver = [v for v in record.history if v.version == body.target_version]
    if not target_ver:
        raise HTTPException(404, f"Version {body.target_version} not found")

    old_hash = _hash(record.current_value)
    # The rollback value — in production we'd decrypt
    rollback_val = target_ver[0].encrypted_value
    record.version += 1
    record.current_value = rollback_val
    record.history.append(ConfigVersion(
        version=record.version,
        value_hash=target_ver[0].value_hash,
        encrypted_value=rollback_val,
        changed_by=f"rollback:{body.actor}",
        changed_at=_now(),
    ))
    record.updated_at = _now()
    _audit(body.actor, AuditAction.config_rollback, key, namespace, old_hash, target_ver[0].value_hash)
    return {"key": key, "rolled_back_to_version": body.target_version, "new_version": record.version}


@app.get("/v1/configs/{key}/history")
def config_history(key: str, namespace: str = "default"):
    idx_key = f"{namespace}:{key}"
    if idx_key not in config_index:
        raise HTTPException(404, f"Config '{key}' not found")
    record = configs[config_index[idx_key]]
    return {"key": key, "namespace": namespace, "versions": [v.dict() for v in record.history]}


# -- Secrets -----------------------------------------------------------------

@app.post("/v1/secrets", status_code=201)
def create_secret(body: SecretCreate):
    idx_key = f"{body.namespace}:{body.key}"
    if idx_key in secret_index:
        raise HTTPException(409, f"Secret '{body.key}' already exists in namespace '{body.namespace}'")

    sid = f"SEC-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = SecretRecord(
        secret_id=sid, key=body.key, namespace=body.namespace,
        environment=body.environment,
        value_hash=_hash(body.value),
        encrypted_value=_encrypt(body.value),
        rotation_policy=body.rotation_policy,
        rotation_interval_hours=body.rotation_interval_hours,
        last_rotated_at=now, created_at=now, updated_at=now,
    )
    secrets[sid] = record
    secret_index[idx_key] = sid
    _audit(body.actor, AuditAction.secret_created, body.key, body.namespace, "", _hash(body.value))
    return record.dict()


@app.post("/v1/secrets/{key}/rotate")
def rotate_secret(key: str, namespace: str = "default", actor: str = "system"):
    idx_key = f"{namespace}:{key}"
    if idx_key not in secret_index:
        raise HTTPException(404, f"Secret '{key}' not found")
    record = secrets[secret_index[idx_key]]
    old_hash = record.value_hash
    new_value = f"rotated-{uuid.uuid4().hex[:16]}"
    record.value_hash = _hash(new_value)
    record.encrypted_value = _encrypt(new_value)
    record.version += 1
    record.last_rotated_at = _now()
    record.access_count = 0
    record.updated_at = _now()
    _audit(actor, AuditAction.secret_rotated, key, namespace, old_hash, record.value_hash)
    return {"key": key, "version": record.version, "rotated_at": record.last_rotated_at}


# -- Audit -------------------------------------------------------------------

@app.get("/v1/audit")
def get_audit(
    namespace: Optional[str] = None,
    action: Optional[AuditAction] = None,
    actor: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(audit_log)
    if namespace:
        results = [a for a in results if a.namespace == namespace]
    if action:
        results = [a for a in results if a.action == action]
    if actor:
        results = [a for a in results if a.actor == actor]
    results = results[-limit:]
    results.reverse()
    return {"audit_entries": [a.dict() for a in results], "total": len(results)}


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    action_dist: Dict[str, int] = defaultdict(int)
    ns_dist: Dict[str, int] = defaultdict(int)
    for a in audit_log:
        action_dist[a.action.value] += 1
        ns_dist[a.namespace] += 1

    rotation_dist: Dict[str, int] = defaultdict(int)
    for s in secrets.values():
        rotation_dist[s.rotation_policy.value] += 1

    return {
        "namespaces": len(namespaces),
        "configs": {
            "total": len(configs),
            "total_versions": sum(len(c.history) for c in configs.values()),
            "encrypted": sum(1 for c in configs.values() if c.encrypted),
        },
        "secrets": {
            "total": len(secrets),
            "rotation_policy_distribution": dict(rotation_dist),
            "total_rotations": sum(s.version - 1 for s in secrets.values()),
        },
        "audit": {
            "total_entries": len(audit_log),
            "action_distribution": dict(action_dist),
            "namespace_distribution": dict(ns_dist),
        },
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9702)
