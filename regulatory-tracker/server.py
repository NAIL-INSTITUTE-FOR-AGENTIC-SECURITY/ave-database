"""
Regulatory Change Tracker — Phase 23 Service 5 of 5
Port: 9704

Automated monitoring of AI regulatory changes across jurisdictions with
impact assessment, compliance gap detection, and action-item generation.
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

class ChangeType(str, Enum):
    new_legislation = "new_legislation"
    amendment = "amendment"
    guidance = "guidance"
    enforcement_action = "enforcement_action"
    court_ruling = "court_ruling"


class ChangeSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ActionStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    verified = "verified"


class ActionPriority(str, Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"


# ---------------------------------------------------------------------------
# Seed Jurisdictions
# ---------------------------------------------------------------------------

JURISDICTIONS: Dict[str, Dict[str, Any]] = {
    "EU": {
        "name": "European Union",
        "key_legislation": ["EU AI Act 2024/1689", "GDPR 2016/679"],
        "regulator": "European Commission / AI Office",
        "notes": "Risk-based framework, prohibits unacceptable-risk AI",
    },
    "US": {
        "name": "United States",
        "key_legislation": ["Executive Order 14110", "NIST AI RMF 1.0", "State-level laws"],
        "regulator": "NIST / FTC / State AGs",
        "notes": "Sectoral approach, voluntary frameworks + state laws",
    },
    "UK": {
        "name": "United Kingdom",
        "key_legislation": ["AI Regulation White Paper 2023", "Online Safety Act"],
        "regulator": "DSIT / Sector regulators",
        "notes": "Pro-innovation, principles-based",
    },
    "CN": {
        "name": "China",
        "key_legislation": ["Interim Measures for GenAI 2023", "Algorithm Recommendation Rules"],
        "regulator": "CAC / MIIT",
        "notes": "Pre-market approval for GenAI services",
    },
    "JP": {
        "name": "Japan",
        "key_legislation": ["AI Strategy 2022", "AI Guidelines for Business"],
        "regulator": "MIC / METI",
        "notes": "Social principles-based, human-centric",
    },
    "AU": {
        "name": "Australia",
        "key_legislation": ["AI Ethics Framework", "Privacy Act 1988"],
        "regulator": "DTA / OAIC",
        "notes": "Voluntary AI Ethics Principles, mandatory guardrails proposed",
    },
    "BR": {
        "name": "Brazil",
        "key_legislation": ["AI Bill PL 2338/2023", "LGPD"],
        "regulator": "ANPD",
        "notes": "Risk-based bill under consideration",
    },
    "IN": {
        "name": "India",
        "key_legislation": ["DPDP Act 2023", "AI Advisory 2024"],
        "regulator": "MeitY",
        "notes": "Digital Personal Data Protection + AI advisories",
    },
    "CA": {
        "name": "Canada",
        "key_legislation": ["AIDA (C-27)", "Voluntary Code of Conduct"],
        "regulator": "ISED / AI Commissioner (proposed)",
        "notes": "AIDA under parliamentary review",
    },
    "SG": {
        "name": "Singapore",
        "key_legislation": ["Model AI Governance Framework", "AI Verify"],
        "regulator": "IMDA / PDPC",
        "notes": "Governance framework + testing toolkit",
    },
}

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class ChangeCreate(BaseModel):
    jurisdiction: str
    title: str
    description: str = ""
    change_type: ChangeType
    severity: ChangeSeverity = ChangeSeverity.medium
    effective_date: Optional[str] = None
    published_date: Optional[str] = None
    affected_domains: List[str] = Field(default_factory=list)
    source_url: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChangeRecord(ChangeCreate):
    change_id: str
    assessment: Optional[Dict[str, Any]] = None
    action_items: List[str] = Field(default_factory=list)  # action_item_ids
    created_at: str
    updated_at: str


class AssessmentCreate(BaseModel):
    compliance_gap: str
    required_actions: List[str] = Field(default_factory=list)
    effort_estimate_hours: float = Field(default=0, ge=0)
    deadline: Optional[str] = None
    risk_if_non_compliant: str = ""
    assessor: str = ""


class ActionItemCreate(BaseModel):
    title: str
    change_id: Optional[str] = None
    owner: str = ""
    priority: ActionPriority = ActionPriority.medium
    description: str = ""
    due_date: Optional[str] = None


class ActionItemRecord(ActionItemCreate):
    action_id: str
    status: ActionStatus = ActionStatus.open
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

changes: Dict[str, ChangeRecord] = {}
action_items: Dict[str, ActionItemRecord] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Regulatory Change Tracker",
    description="Phase 23 — Automated AI regulatory change monitoring with impact assessment and action items",
    version="23.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    open_actions = sum(1 for a in action_items.values() if a.status in (ActionStatus.open, ActionStatus.in_progress))
    return {
        "service": "regulatory-change-tracker",
        "status": "healthy",
        "phase": 23,
        "port": 9704,
        "stats": {
            "jurisdictions": len(JURISDICTIONS),
            "changes": len(changes),
            "action_items": len(action_items),
            "open_actions": open_actions,
        },
        "timestamp": _now(),
    }


# -- Jurisdictions -----------------------------------------------------------

@app.get("/v1/jurisdictions")
def list_jurisdictions():
    return {
        "jurisdictions": [
            {"code": code, **info}
            for code, info in JURISDICTIONS.items()
        ],
        "total": len(JURISDICTIONS),
    }


# -- Changes -----------------------------------------------------------------

@app.post("/v1/changes", status_code=201)
def register_change(body: ChangeCreate):
    if body.jurisdiction not in JURISDICTIONS:
        raise HTTPException(422, f"Unknown jurisdiction '{body.jurisdiction}'. Known: {list(JURISDICTIONS.keys())}")
    cid = f"CHG-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = ChangeRecord(**body.dict(), change_id=cid, created_at=now, updated_at=now)
    changes[cid] = record
    return record.dict()


@app.get("/v1/changes")
def list_changes(
    jurisdiction: Optional[str] = None,
    change_type: Optional[ChangeType] = None,
    severity: Optional[ChangeSeverity] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(changes.values())
    if jurisdiction:
        results = [c for c in results if c.jurisdiction == jurisdiction]
    if change_type:
        results = [c for c in results if c.change_type == change_type]
    if severity:
        results = [c for c in results if c.severity == severity]
    results.sort(key=lambda c: c.created_at, reverse=True)
    return {"changes": [c.dict() for c in results[:limit]], "total": len(results)}


@app.get("/v1/changes/{change_id}")
def get_change(change_id: str):
    if change_id not in changes:
        raise HTTPException(404, "Change not found")
    return changes[change_id].dict()


# -- Impact Assessment -------------------------------------------------------

@app.post("/v1/changes/{change_id}/assess")
def assess_change(change_id: str, body: AssessmentCreate):
    if change_id not in changes:
        raise HTTPException(404, "Change not found")
    change = changes[change_id]
    change.assessment = {
        "compliance_gap": body.compliance_gap,
        "required_actions": body.required_actions,
        "effort_estimate_hours": body.effort_estimate_hours,
        "deadline": body.deadline,
        "risk_if_non_compliant": body.risk_if_non_compliant,
        "assessor": body.assessor,
        "assessed_at": _now(),
    }
    change.updated_at = _now()

    # Auto-generate action items from required_actions
    generated = []
    priority_map = {"critical": ActionPriority.urgent, "high": ActionPriority.high,
                    "medium": ActionPriority.medium, "low": ActionPriority.low}
    priority = priority_map.get(change.severity.value, ActionPriority.medium)
    for action_desc in body.required_actions:
        aid = f"ACT-{uuid.uuid4().hex[:12]}"
        item = ActionItemRecord(
            action_id=aid, title=action_desc, change_id=change_id,
            owner=body.assessor, priority=priority,
            description=f"Generated from assessment of {change.title}",
            due_date=body.deadline,
            created_at=_now(), updated_at=_now(),
        )
        action_items[aid] = item
        change.action_items.append(aid)
        generated.append(aid)

    return {
        "change_id": change_id,
        "assessment": change.assessment,
        "action_items_generated": generated,
    }


@app.get("/v1/changes/{change_id}/assessment")
def get_assessment(change_id: str):
    if change_id not in changes:
        raise HTTPException(404, "Change not found")
    change = changes[change_id]
    if not change.assessment:
        raise HTTPException(404, "No assessment for this change")
    items = [action_items[aid].dict() for aid in change.action_items if aid in action_items]
    return {"change_id": change_id, "assessment": change.assessment, "action_items": items}


# -- Action Items ------------------------------------------------------------

@app.post("/v1/action-items", status_code=201)
def create_action_item(body: ActionItemCreate):
    aid = f"ACT-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = ActionItemRecord(**body.dict(), action_id=aid, created_at=now, updated_at=now)
    action_items[aid] = record
    # Link to change if provided
    if body.change_id and body.change_id in changes:
        changes[body.change_id].action_items.append(aid)
    return record.dict()


@app.get("/v1/action-items")
def list_action_items(
    status: Optional[ActionStatus] = None,
    priority: Optional[ActionPriority] = None,
    owner: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(action_items.values())
    if status:
        results = [a for a in results if a.status == status]
    if priority:
        results = [a for a in results if a.priority == priority]
    if owner:
        results = [a for a in results if a.owner == owner]
    results.sort(key=lambda a: a.created_at, reverse=True)
    return {"action_items": [a.dict() for a in results[:limit]], "total": len(results)}


STATUS_ORDER = list(ActionStatus)


@app.patch("/v1/action-items/{action_id}/advance")
def advance_action_item(action_id: str):
    if action_id not in action_items:
        raise HTTPException(404, "Action item not found")
    item = action_items[action_id]
    idx = STATUS_ORDER.index(item.status)
    if idx >= len(STATUS_ORDER) - 1:
        raise HTTPException(409, "Action item already at final status")
    item.status = STATUS_ORDER[idx + 1]
    item.updated_at = _now()
    return {"action_id": action_id, "status": item.status.value}


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    juris_dist: Dict[str, int] = defaultdict(int)
    type_dist: Dict[str, int] = defaultdict(int)
    severity_dist: Dict[str, int] = defaultdict(int)
    for c in changes.values():
        juris_dist[c.jurisdiction] += 1
        type_dist[c.change_type.value] += 1
        severity_dist[c.severity.value] += 1

    status_dist: Dict[str, int] = defaultdict(int)
    priority_dist: Dict[str, int] = defaultdict(int)
    for a in action_items.values():
        status_dist[a.status.value] += 1
        priority_dist[a.priority.value] += 1

    assessed = sum(1 for c in changes.values() if c.assessment)
    total_effort = sum(
        c.assessment.get("effort_estimate_hours", 0)
        for c in changes.values() if c.assessment
    )

    return {
        "changes": {
            "total": len(changes),
            "jurisdiction_distribution": dict(juris_dist),
            "type_distribution": dict(type_dist),
            "severity_distribution": dict(severity_dist),
            "assessed": assessed,
            "unassessed": len(changes) - assessed,
        },
        "action_items": {
            "total": len(action_items),
            "status_distribution": dict(status_dist),
            "priority_distribution": dict(priority_dist),
        },
        "effort": {
            "total_estimated_hours": total_effort,
        },
        "jurisdictions_monitored": len(JURISDICTIONS),
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9704)
