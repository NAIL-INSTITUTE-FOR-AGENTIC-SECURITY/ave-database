"""Human Override Controller — Phase 25 Service 3 · Port 9902"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

app = FastAPI(title="Human Override Controller", version="0.25.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class AutonomyLevel(str, Enum):
    full_auto = "full_auto"
    supervised = "supervised"
    approval_required = "approval_required"
    human_only = "human_only"

class OverrideState(str, Enum):
    pending = "pending"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"

class Urgency(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class ReviewAction(str, Enum):
    approve_as_is = "approve_as_is"
    approve_with_modifications = "approve_with_modifications"
    reject = "reject"
    defer = "defer"

class EscalationTier(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"

ESCALATION_CONFIG = {
    "L1": {"role": "team_lead", "timeout_minutes": 30},
    "L2": {"role": "department_head", "timeout_minutes": 15},
    "L3": {"role": "executive", "timeout_minutes": 5},
}

# ── Models ───────────────────────────────────────────────────────────
class BoundaryCreate(BaseModel):
    system_id: str
    system_name: str = ""
    autonomy_level: AutonomyLevel = AutonomyLevel.supervised
    risk_threshold: float = Field(0.7, ge=0, le=1)
    auto_approve_below_confidence: float = Field(0.3, ge=0, le=1)

class OverrideCreate(BaseModel):
    system_id: str
    action_description: str
    risk_score: float = Field(0.5, ge=0, le=1)
    confidence: float = Field(0.5, ge=0, le=1)
    urgency: Urgency = Urgency.medium
    context: dict = {}

class ReviewCreate(BaseModel):
    reviewer_id: str
    action: ReviewAction
    justification: str
    modifications: dict = {}

# ── Stores ───────────────────────────────────────────────────────────
boundaries: dict[str, dict] = {}
overrides: dict[str, dict] = {}
interventions: list[dict] = []
emergency_halt_active: bool = False

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "human-override-controller",
        "status": "healthy",
        "version": "0.25.3",
        "boundaries": len(boundaries),
        "overrides": len(overrides),
        "emergency_halt": emergency_halt_active,
    }

# ── Boundaries ───────────────────────────────────────────────────────
@app.post("/v1/boundaries", status_code=201)
def create_boundary(body: BoundaryCreate):
    bid = str(uuid.uuid4())
    rec = {"id": bid, **body.model_dump(), "created_at": _now(), "autonomy_adjustments": []}
    boundaries[bid] = rec
    return rec

@app.get("/v1/boundaries")
def list_boundaries(system_id: Optional[str] = None):
    out = list(boundaries.values())
    if system_id:
        out = [b for b in out if b["system_id"] == system_id]
    return out

# ── Override Requests ────────────────────────────────────────────────
@app.post("/v1/overrides", status_code=201)
def create_override(body: OverrideCreate):
    if emergency_halt_active:
        raise HTTPException(423, "Emergency halt active — all AI actions frozen")

    oid = str(uuid.uuid4())
    rec = {
        "id": oid,
        **body.model_dump(),
        "state": "pending",
        "escalation_tier": "L1",
        "created_at": _now(),
        "reviewed_at": None,
        "reviewer_id": None,
        "review_action": None,
        "justification": None,
        "modifications": {},
        "original_action": body.action_description,
    }
    overrides[oid] = rec
    return rec

@app.get("/v1/overrides")
def list_overrides(
    state: Optional[OverrideState] = None,
    system_id: Optional[str] = None,
    urgency: Optional[Urgency] = None,
):
    out = list(overrides.values())
    if state:
        out = [o for o in out if o["state"] == state]
    if system_id:
        out = [o for o in out if o["system_id"] == system_id]
    if urgency:
        out = [o for o in out if o["urgency"] == urgency]
    return sorted(out, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["urgency"], 4))

@app.get("/v1/overrides/{oid}")
def get_override(oid: str):
    if oid not in overrides:
        raise HTTPException(404, "Override not found")
    return overrides[oid]

# ── Review ───────────────────────────────────────────────────────────
@app.post("/v1/overrides/{oid}/review")
def review_override(oid: str, body: ReviewCreate):
    if oid not in overrides:
        raise HTTPException(404, "Override not found")
    o = overrides[oid]
    if o["state"] not in ("pending", "under_review"):
        raise HTTPException(400, f"Override in state {o['state']}, cannot review")

    action_map = {
        "approve_as_is": "approved",
        "approve_with_modifications": "approved",
        "reject": "rejected",
        "defer": "under_review",
    }
    o["state"] = action_map[body.action]
    o["reviewed_at"] = _now()
    o["reviewer_id"] = body.reviewer_id
    o["review_action"] = body.action
    o["justification"] = body.justification
    o["modifications"] = body.modifications

    # Log intervention
    interventions.append({
        "override_id": oid,
        "system_id": o["system_id"],
        "reviewer_id": body.reviewer_id,
        "action": body.action,
        "justification": body.justification,
        "original_action": o["original_action"],
        "modified_action": body.modifications.get("new_action", o["original_action"]),
        "risk_score": o["risk_score"],
        "timestamp": _now(),
    })
    return o

# ── Escalation ───────────────────────────────────────────────────────
@app.post("/v1/overrides/{oid}/escalate")
def escalate_override(oid: str):
    if oid not in overrides:
        raise HTTPException(404, "Override not found")
    o = overrides[oid]
    tier_order = ["L1", "L2", "L3"]
    current_idx = tier_order.index(o.get("escalation_tier", "L1"))
    if current_idx >= len(tier_order) - 1:
        raise HTTPException(400, "Already at maximum escalation (L3)")
    new_tier = tier_order[current_idx + 1]
    o["escalation_tier"] = new_tier
    o["state"] = "under_review"
    return {"override_id": oid, "escalated_to": new_tier, "config": ESCALATION_CONFIG[new_tier]}

# ── Emergency Halt ───────────────────────────────────────────────────
@app.post("/v1/emergency-halt")
def emergency_halt():
    global emergency_halt_active
    emergency_halt_active = True
    # Move all pending overrides to under_review
    count = 0
    for o in overrides.values():
        if o["state"] == "pending":
            o["state"] = "under_review"
            count += 1
    return {"status": "halt_active", "pending_frozen": count}

@app.post("/v1/emergency-resume")
def emergency_resume():
    global emergency_halt_active
    emergency_halt_active = False
    return {"status": "resumed"}

# ── Intervention Log ─────────────────────────────────────────────────
@app.get("/v1/interventions")
def list_interventions(system_id: Optional[str] = None, limit: int = Query(100, ge=1)):
    out = interventions
    if system_id:
        out = [i for i in out if i["system_id"] == system_id]
    return out[-limit:]

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    ol = list(overrides.values())
    by_state = {}
    for o in ol:
        by_state[o["state"]] = by_state.get(o["state"], 0) + 1
    by_system = {}
    for o in ol:
        by_system[o["system_id"]] = by_system.get(o["system_id"], 0) + 1
    by_urgency = {}
    for o in ol:
        by_urgency[o["urgency"]] = by_urgency.get(o["urgency"], 0) + 1
    by_tier = {}
    for o in ol:
        by_tier[o.get("escalation_tier", "L1")] = by_tier.get(o.get("escalation_tier", "L1"), 0) + 1
    review_actions = {}
    for i in interventions:
        review_actions[i["action"]] = review_actions.get(i["action"], 0) + 1
    return {
        "total_overrides": len(ol),
        "by_state": by_state,
        "by_system": by_system,
        "by_urgency": by_urgency,
        "by_escalation_tier": by_tier,
        "total_interventions": len(interventions),
        "review_actions": review_actions,
        "emergency_halt_active": emergency_halt_active,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9902)
