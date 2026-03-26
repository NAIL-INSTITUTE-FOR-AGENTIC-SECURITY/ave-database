"""
Defence Orchestration Platform — Core API server.

Manages defence profiles, guardrails, monitors, circuit-breakers,
and automated playbooks driven by AVE threat intelligence.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NAIL Defence Orchestration Platform",
    description="AVE-driven defence lifecycle management for agentic AI systems.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("dop.server")

# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class DeploymentStatus(str, Enum):
    DRAFT = "draft"
    CANARY = "canary"
    STAGED = "staged"
    FULL = "full"
    ROLLED_BACK = "rolled_back"
    DISABLED = "disabled"


class GuardrailType(str, Enum):
    INPUT_FILTER = "input_filter"
    OUTPUT_FILTER = "output_filter"
    TOOL_GUARD = "tool_guard"
    MEMORY_GUARD = "memory_guard"
    DELEGATION_GUARD = "delegation_guard"
    CONTEXT_GUARD = "context_guard"


class MonitorType(str, Enum):
    ANOMALY_DETECTOR = "anomaly_detector"
    BEHAVIOUR_MONITOR = "behaviour_monitor"
    CIRCUIT_BREAKER = "circuit_breaker"
    COMPLIANCE_MONITOR = "compliance_monitor"
    COST_MONITOR = "cost_monitor"


class ActionType(str, Enum):
    BLOCK = "block"
    BLOCK_AND_LOG = "block_and_log"
    LOG = "log"
    REDACT = "redact"
    THROTTLE = "throttle"
    ALERT = "alert"
    DENY_AND_ALERT = "deny_and_alert"


class AVETrigger(BaseModel):
    """Defines when a guardrail/monitor should activate based on AVE intelligence."""

    ave_id: Optional[str] = None
    category: Optional[str] = None
    min_severity: Optional[str] = None


class GuardrailConfig(BaseModel):
    """Configuration for a single guardrail."""

    guardrail_id: str = Field(default_factory=lambda: f"grd-{uuid.uuid4().hex[:8]}")
    type: GuardrailType
    name: str
    description: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    action: ActionType = ActionType.BLOCK_AND_LOG
    ave_triggers: list[AVETrigger] = Field(default_factory=list)
    enabled: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class MonitorConfig(BaseModel):
    """Configuration for a single monitor."""

    monitor_id: str = Field(default_factory=lambda: f"mon-{uuid.uuid4().hex[:8]}")
    type: MonitorType
    name: str
    description: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    ave_triggers: list[AVETrigger] = Field(default_factory=list)
    enabled: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PlaybookAction(BaseModel):
    """A single action within a playbook."""

    action_type: str  # enable_guardrail, set_circuit_breaker, notify, log
    parameters: dict[str, Any] = Field(default_factory=dict)


class Playbook(BaseModel):
    """Automated response playbook triggered by AVE events."""

    playbook_id: str = Field(default_factory=lambda: f"pb-{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    trigger: dict[str, Any] = Field(default_factory=dict)
    actions: list[PlaybookAction] = Field(default_factory=list)
    enabled: bool = True
    executions: int = 0
    last_executed: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class DefenceProfile(BaseModel):
    """A complete defence profile for one or more agents."""

    profile_id: str = Field(default_factory=lambda: f"prof-{uuid.uuid4().hex[:8]}")
    name: str
    version: str = "1.0.0"
    description: str = ""
    target_agents: list[str] = Field(default_factory=list)
    guardrails: list[GuardrailConfig] = Field(default_factory=list)
    monitors: list[MonitorConfig] = Field(default_factory=list)
    playbooks: list[Playbook] = Field(default_factory=list)
    deployment_status: DeploymentStatus = DeploymentStatus.DRAFT
    deployment_percentage: float = 0.0
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# In-memory stores (production → PostgreSQL + Redis)
# ---------------------------------------------------------------------------

profiles_store: dict[str, DefenceProfile] = {}
guardrails_store: dict[str, GuardrailConfig] = {}
monitors_store: dict[str, MonitorConfig] = {}
playbooks_store: dict[str, Playbook] = {}
audit_log: list[dict[str, Any]] = []


def _audit(action: str, resource_id: str, detail: str = "") -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "resource_id": resource_id,
        "detail": detail,
    }
    audit_log.append(entry)
    logger.info("[AUDIT] %s %s — %s", action, resource_id, detail)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CreateProfileRequest(BaseModel):
    name: str
    description: str = ""
    target_agents: list[str] = Field(default_factory=list)
    version: str = "1.0.0"


class AddGuardrailRequest(BaseModel):
    type: GuardrailType
    name: str
    description: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    action: ActionType = ActionType.BLOCK_AND_LOG
    ave_triggers: list[AVETrigger] = Field(default_factory=list)


class AddMonitorRequest(BaseModel):
    type: MonitorType
    name: str
    description: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    ave_triggers: list[AVETrigger] = Field(default_factory=list)


class CreatePlaybookRequest(BaseModel):
    name: str
    description: str = ""
    trigger: dict[str, Any] = Field(default_factory=dict)
    actions: list[PlaybookAction] = Field(default_factory=list)


class DeployRequest(BaseModel):
    strategy: str = "canary"  # canary | staged | full
    canary_percentage: float = 5.0


class AVEWebhookEvent(BaseModel):
    """Incoming AVE live feed event."""

    event_id: str
    event_type: str  # ave.created, ave.updated, ave.severity_changed, ave.deprecated
    ave_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------


@app.post("/v1/profiles", status_code=status.HTTP_201_CREATED)
async def create_profile(req: CreateProfileRequest) -> DefenceProfile:
    profile = DefenceProfile(
        name=req.name,
        description=req.description,
        target_agents=req.target_agents,
        version=req.version,
    )
    profiles_store[profile.profile_id] = profile
    _audit("PROFILE_CREATED", profile.profile_id, profile.name)
    return profile


@app.get("/v1/profiles")
async def list_profiles(
    status_filter: Optional[DeploymentStatus] = Query(None, alias="status"),
) -> list[DefenceProfile]:
    profiles = list(profiles_store.values())
    if status_filter:
        profiles = [p for p in profiles if p.deployment_status == status_filter]
    return profiles


@app.get("/v1/profiles/{profile_id}")
async def get_profile(profile_id: str) -> DefenceProfile:
    if profile_id not in profiles_store:
        raise HTTPException(404, "Profile not found")
    return profiles_store[profile_id]


@app.put("/v1/profiles/{profile_id}")
async def update_profile(profile_id: str, req: CreateProfileRequest) -> DefenceProfile:
    if profile_id not in profiles_store:
        raise HTTPException(404, "Profile not found")
    profile = profiles_store[profile_id]
    profile.name = req.name
    profile.description = req.description
    profile.target_agents = req.target_agents
    profile.version = req.version
    profile.updated_at = datetime.now(timezone.utc).isoformat()
    _audit("PROFILE_UPDATED", profile_id, profile.name)
    return profile


@app.delete("/v1/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: str) -> None:
    if profile_id not in profiles_store:
        raise HTTPException(404, "Profile not found")
    profiles_store[profile_id].deployment_status = DeploymentStatus.DISABLED
    _audit("PROFILE_DELETED", profile_id)


@app.post("/v1/profiles/{profile_id}/deploy")
async def deploy_profile(profile_id: str, req: DeployRequest) -> dict[str, Any]:
    if profile_id not in profiles_store:
        raise HTTPException(404, "Profile not found")
    profile = profiles_store[profile_id]

    if req.strategy == "canary":
        profile.deployment_status = DeploymentStatus.CANARY
        profile.deployment_percentage = req.canary_percentage
    elif req.strategy == "staged":
        profile.deployment_status = DeploymentStatus.STAGED
        profile.deployment_percentage = 50.0
    elif req.strategy == "full":
        profile.deployment_status = DeploymentStatus.FULL
        profile.deployment_percentage = 100.0

    profile.updated_at = datetime.now(timezone.utc).isoformat()
    _audit("PROFILE_DEPLOYED", profile_id, f"strategy={req.strategy}")

    return {
        "profile_id": profile_id,
        "deployment_status": profile.deployment_status.value,
        "deployment_percentage": profile.deployment_percentage,
        "deployed_at": profile.updated_at,
    }


@app.post("/v1/profiles/{profile_id}/rollback")
async def rollback_profile(profile_id: str) -> dict[str, Any]:
    if profile_id not in profiles_store:
        raise HTTPException(404, "Profile not found")
    profile = profiles_store[profile_id]
    profile.deployment_status = DeploymentStatus.ROLLED_BACK
    profile.deployment_percentage = 0.0
    profile.updated_at = datetime.now(timezone.utc).isoformat()
    _audit("PROFILE_ROLLED_BACK", profile_id)
    return {
        "profile_id": profile_id,
        "deployment_status": "rolled_back",
        "rolled_back_at": profile.updated_at,
    }


@app.get("/v1/profiles/{profile_id}/status")
async def profile_status(profile_id: str) -> dict[str, Any]:
    if profile_id not in profiles_store:
        raise HTTPException(404, "Profile not found")
    p = profiles_store[profile_id]
    return {
        "profile_id": profile_id,
        "name": p.name,
        "deployment_status": p.deployment_status.value,
        "deployment_percentage": p.deployment_percentage,
        "guardrails_active": sum(1 for g in p.guardrails if g.enabled),
        "monitors_active": sum(1 for m in p.monitors if m.enabled),
        "playbooks_active": sum(1 for pb in p.playbooks if pb.enabled),
        "target_agents": p.target_agents,
    }


# ---------------------------------------------------------------------------
# Guardrail endpoints
# ---------------------------------------------------------------------------


@app.post("/v1/guardrails", status_code=status.HTTP_201_CREATED)
async def create_guardrail(req: AddGuardrailRequest) -> GuardrailConfig:
    g = GuardrailConfig(
        type=req.type,
        name=req.name,
        description=req.description,
        config=req.config,
        action=req.action,
        ave_triggers=req.ave_triggers,
    )
    guardrails_store[g.guardrail_id] = g
    _audit("GUARDRAIL_CREATED", g.guardrail_id, g.name)
    return g


@app.get("/v1/guardrails")
async def list_guardrails(
    gtype: Optional[GuardrailType] = Query(None, alias="type"),
) -> list[GuardrailConfig]:
    results = list(guardrails_store.values())
    if gtype:
        results = [g for g in results if g.type == gtype]
    return results


@app.get("/v1/guardrails/{guardrail_id}")
async def get_guardrail(guardrail_id: str) -> GuardrailConfig:
    if guardrail_id not in guardrails_store:
        raise HTTPException(404, "Guardrail not found")
    return guardrails_store[guardrail_id]


@app.put("/v1/guardrails/{guardrail_id}/config")
async def update_guardrail_config(
    guardrail_id: str, config: dict[str, Any]
) -> GuardrailConfig:
    if guardrail_id not in guardrails_store:
        raise HTTPException(404, "Guardrail not found")
    g = guardrails_store[guardrail_id]
    g.config.update(config)
    g.updated_at = datetime.now(timezone.utc).isoformat()
    _audit("GUARDRAIL_CONFIG_UPDATED", guardrail_id)
    return g


@app.post("/v1/guardrails/{guardrail_id}/test")
async def test_guardrail(
    guardrail_id: str, sample: dict[str, Any]
) -> dict[str, Any]:
    if guardrail_id not in guardrails_store:
        raise HTTPException(404, "Guardrail not found")
    g = guardrails_store[guardrail_id]

    # Simulate guardrail evaluation
    result = {
        "guardrail_id": guardrail_id,
        "guardrail_name": g.name,
        "guardrail_type": g.type.value,
        "input": sample,
        "action_taken": g.action.value,
        "blocked": g.action in (ActionType.BLOCK, ActionType.BLOCK_AND_LOG, ActionType.DENY_AND_ALERT),
        "latency_ms": 12.5,
        "tested_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


@app.get("/v1/guardrails/{guardrail_id}/metrics")
async def guardrail_metrics(guardrail_id: str) -> dict[str, Any]:
    if guardrail_id not in guardrails_store:
        raise HTTPException(404, "Guardrail not found")
    return {
        "guardrail_id": guardrail_id,
        "total_evaluations": 0,
        "blocks": 0,
        "allows": 0,
        "avg_latency_ms": 0.0,
        "false_positive_rate": 0.0,
        "last_24h": {"evaluations": 0, "blocks": 0},
    }


# ---------------------------------------------------------------------------
# Monitor endpoints
# ---------------------------------------------------------------------------


@app.post("/v1/monitors", status_code=status.HTTP_201_CREATED)
async def create_monitor(req: AddMonitorRequest) -> MonitorConfig:
    m = MonitorConfig(
        type=req.type,
        name=req.name,
        description=req.description,
        config=req.config,
        ave_triggers=req.ave_triggers,
    )
    monitors_store[m.monitor_id] = m
    _audit("MONITOR_CREATED", m.monitor_id, m.name)
    return m


@app.get("/v1/monitors")
async def list_monitors() -> list[MonitorConfig]:
    return list(monitors_store.values())


@app.get("/v1/monitors/{monitor_id}/alerts")
async def monitor_alerts(
    monitor_id: str,
    limit: int = Query(50, ge=1, le=500),
) -> list[dict[str, Any]]:
    if monitor_id not in monitors_store:
        raise HTTPException(404, "Monitor not found")
    return []  # Would query alert store


# ---------------------------------------------------------------------------
# Playbook endpoints
# ---------------------------------------------------------------------------


@app.post("/v1/playbooks", status_code=status.HTTP_201_CREATED)
async def create_playbook(req: CreatePlaybookRequest) -> Playbook:
    pb = Playbook(
        name=req.name,
        description=req.description,
        trigger=req.trigger,
        actions=req.actions,
    )
    playbooks_store[pb.playbook_id] = pb
    _audit("PLAYBOOK_CREATED", pb.playbook_id, pb.name)
    return pb


@app.get("/v1/playbooks")
async def list_playbooks() -> list[Playbook]:
    return list(playbooks_store.values())


@app.post("/v1/playbooks/{playbook_id}/execute")
async def execute_playbook(playbook_id: str) -> dict[str, Any]:
    if playbook_id not in playbooks_store:
        raise HTTPException(404, "Playbook not found")
    pb = playbooks_store[playbook_id]
    pb.executions += 1
    pb.last_executed = datetime.now(timezone.utc).isoformat()
    _audit("PLAYBOOK_EXECUTED", playbook_id, f"execution #{pb.executions}")

    results = []
    for action in pb.actions:
        results.append(
            {
                "action_type": action.action_type,
                "parameters": action.parameters,
                "status": "completed",
            }
        )

    return {
        "playbook_id": playbook_id,
        "execution_number": pb.executions,
        "actions_executed": len(results),
        "results": results,
        "executed_at": pb.last_executed,
    }


@app.get("/v1/playbooks/{playbook_id}/history")
async def playbook_history(playbook_id: str) -> dict[str, Any]:
    if playbook_id not in playbooks_store:
        raise HTTPException(404, "Playbook not found")
    pb = playbooks_store[playbook_id]
    return {
        "playbook_id": playbook_id,
        "name": pb.name,
        "total_executions": pb.executions,
        "last_executed": pb.last_executed,
    }


# ---------------------------------------------------------------------------
# AVE integration endpoints
# ---------------------------------------------------------------------------

AVE_CATEGORIES = [
    "prompt_injection", "tool_abuse", "memory_poisoning", "identity_spoofing",
    "goal_hijacking", "knowledge_poisoning", "resource_exhaustion",
    "output_manipulation", "privilege_escalation", "trust_exploitation",
    "context_overflow", "model_denial_of_service", "data_exfiltration",
    "supply_chain", "model_poisoning", "multi_agent_coordination",
    "reward_hacking", "emergent_behavior",
]


@app.post("/v1/ave/webhook")
async def ave_webhook(event: AVEWebhookEvent) -> dict[str, Any]:
    """Process incoming AVE live feed events and trigger matching playbooks."""
    _audit("AVE_EVENT_RECEIVED", event.ave_id, event.event_type)

    triggered_playbooks: list[str] = []
    ave_severity = event.payload.get("severity", "info")
    ave_category = event.payload.get("category", "")

    for pb_id, pb in playbooks_store.items():
        if not pb.enabled:
            continue
        trigger_severity = pb.trigger.get("ave_severity")
        trigger_category = pb.trigger.get("ave_category")

        severity_match = trigger_severity and _severity_gte(
            ave_severity, trigger_severity
        )
        category_match = trigger_category and ave_category == trigger_category
        event_type_match = pb.trigger.get("event_type") == event.event_type

        if severity_match or category_match or event_type_match:
            triggered_playbooks.append(pb_id)
            pb.executions += 1
            pb.last_executed = datetime.now(timezone.utc).isoformat()
            _audit("PLAYBOOK_AUTO_TRIGGERED", pb_id, f"by AVE event {event.event_id}")

    return {
        "event_id": event.event_id,
        "processed": True,
        "playbooks_triggered": triggered_playbooks,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/v1/ave/coverage")
async def ave_coverage() -> dict[str, Any]:
    """Show which AVE categories are covered by active guardrails/monitors."""
    covered: set[str] = set()
    for g in guardrails_store.values():
        if g.enabled:
            for trigger in g.ave_triggers:
                if trigger.category:
                    covered.add(trigger.category)
    for m in monitors_store.values():
        if m.enabled:
            for trigger in m.ave_triggers:
                if trigger.category:
                    covered.add(trigger.category)

    return {
        "total_categories": len(AVE_CATEGORIES),
        "covered_categories": sorted(covered),
        "coverage_percentage": round(len(covered) / len(AVE_CATEGORIES) * 100, 1)
        if AVE_CATEGORIES
        else 0,
        "uncovered_categories": sorted(set(AVE_CATEGORIES) - covered),
    }


@app.get("/v1/ave/gaps")
async def ave_gaps() -> dict[str, Any]:
    """Identify AVE categories with no active defence coverage."""
    covered: set[str] = set()
    for g in guardrails_store.values():
        if g.enabled:
            for trigger in g.ave_triggers:
                if trigger.category:
                    covered.add(trigger.category)
    for m in monitors_store.values():
        if m.enabled:
            for trigger in m.ave_triggers:
                if trigger.category:
                    covered.add(trigger.category)

    gaps = sorted(set(AVE_CATEGORIES) - covered)
    return {
        "gap_count": len(gaps),
        "gaps": gaps,
        "recommendation": "Deploy guardrails or monitors for uncovered categories.",
    }


# ---------------------------------------------------------------------------
# Health & audit
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "defence-orchestration-platform"}


@app.get("/v1/audit")
async def get_audit_log(limit: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
    return audit_log[-limit:]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]


def _severity_gte(actual: str, threshold: str) -> bool:
    """Check if actual severity >= threshold severity."""
    a = _SEVERITY_ORDER.index(actual) if actual in _SEVERITY_ORDER else -1
    t = _SEVERITY_ORDER.index(threshold) if threshold in _SEVERITY_ORDER else -1
    return a >= t


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8300)
