"""Constitutional AI Monitor — Phase 26 Service 5 · Port 9909"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random

app = FastAPI(title="Constitutional AI Monitor", version="0.26.5")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class PrincipleCategory(str, Enum):
    fairness = "fairness"
    safety = "safety"
    transparency = "transparency"
    privacy = "privacy"
    accountability = "accountability"
    beneficence = "beneficence"
    non_maleficence = "non_maleficence"
    autonomy = "autonomy"

class EnforcementLevel(str, Enum):
    hard_constraint = "hard_constraint"
    soft_constraint = "soft_constraint"
    aspiration = "aspiration"

class SystemType(str, Enum):
    classifier = "classifier"
    generator = "generator"
    recommender = "recommender"
    agent = "agent"
    pipeline = "pipeline"

class RiskTier(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class ActionType(str, Enum):
    decision = "decision"
    output = "output"
    recommendation = "recommendation"
    denial = "denial"
    escalation = "escalation"

class ViolationType(str, Enum):
    direct_violation = "direct_violation"
    borderline = "borderline"
    spirit_violation = "spirit_violation"
    pattern_violation = "pattern_violation"

class SeverityTier(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"

class RemediationAction(str, Enum):
    retrain = "retrain"
    constrain = "constrain"
    audit = "audit"
    rollback = "rollback"
    decommission = "decommission"
    human_review = "human_review"

class AmendmentType(str, Enum):
    add = "add"
    modify = "modify"
    remove = "remove"
    reorder = "reorder"

# ── Models ───────────────────────────────────────────────────────────
class Principle(BaseModel):
    text: str
    category: PrincipleCategory
    weight: int = Field(5, ge=1, le=10)
    enforcement_level: EnforcementLevel = EnforcementLevel.soft_constraint

class ConstitutionCreate(BaseModel):
    name: str
    description: str = ""
    principles: list[Principle] = []

class SystemCreate(BaseModel):
    name: str
    system_type: SystemType
    deployment_env: str = "production"
    risk_tier: RiskTier = RiskTier.medium

class ObservationCreate(BaseModel):
    system_id: str
    action_type: ActionType
    input_summary: str = ""
    output_summary: str = ""
    affected_parties: list[str] = []
    context: dict = {}

class AmendmentCreate(BaseModel):
    amendment_type: AmendmentType
    principle_index: int = Field(0, ge=0)
    new_principle: Optional[Principle] = None
    rationale: str = ""

class RemediateRequest(BaseModel):
    action: RemediationAction
    notes: str = ""

# ── Stores ───────────────────────────────────────────────────────────
constitutions: dict[str, dict] = {}
systems: dict[str, dict] = {}
observations: dict[str, dict] = {}
violations: dict[str, dict] = {}
amendments: list[dict] = []

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Severity Scoring ─────────────────────────────────────────────────
ENFORCEMENT_MULTIPLIER = {"hard_constraint": 3.0, "soft_constraint": 2.0, "aspiration": 1.0}
RISK_MULTIPLIER = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5}

def _compute_severity_score(principle: dict, system: dict, recurrence: int) -> tuple[float, str]:
    base = principle["weight"] * 10
    enforced = base * ENFORCEMENT_MULTIPLIER.get(principle["enforcement_level"], 1.0)
    risk_adj = enforced * RISK_MULTIPLIER.get(system.get("risk_tier", "medium"), 1.0)
    recurrence_adj = risk_adj * (1 + 0.1 * min(recurrence, 10))
    score = min(100, round(recurrence_adj, 1))
    if score >= 90:
        tier = "critical"
    elif score >= 70:
        tier = "high"
    elif score >= 50:
        tier = "medium"
    elif score >= 30:
        tier = "low"
    else:
        tier = "info"
    return score, tier

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "constitutional-ai-monitor",
        "status": "healthy",
        "version": "0.26.5",
        "constitutions": len(constitutions),
        "systems": len(systems),
        "observations": len(observations),
        "violations": len(violations),
    }

# ── Constitution CRUD ────────────────────────────────────────────────
@app.post("/v1/constitutions", status_code=201)
def create_constitution(body: ConstitutionCreate):
    cid = str(uuid.uuid4())
    rec = {
        "id": cid,
        "name": body.name,
        "description": body.description,
        "principles": [p.model_dump() for p in body.principles],
        "version": 1,
        "created_at": _now(),
    }
    constitutions[cid] = rec
    return rec

@app.get("/v1/constitutions")
def list_constitutions():
    return list(constitutions.values())

@app.get("/v1/constitutions/{cid}")
def get_constitution(cid: str):
    if cid not in constitutions:
        raise HTTPException(404, "Constitution not found")
    return constitutions[cid]

@app.post("/v1/constitutions/{cid}/amend")
def amend_constitution(cid: str, body: AmendmentCreate):
    if cid not in constitutions:
        raise HTTPException(404, "Constitution not found")
    c = constitutions[cid]
    if body.amendment_type == "add" and body.new_principle:
        c["principles"].append(body.new_principle.model_dump())
    elif body.amendment_type == "modify" and body.new_principle:
        if body.principle_index < len(c["principles"]):
            c["principles"][body.principle_index] = body.new_principle.model_dump()
    elif body.amendment_type == "remove":
        if body.principle_index < len(c["principles"]):
            c["principles"].pop(body.principle_index)
    c["version"] += 1
    amendment = {"constitution_id": cid, **body.model_dump(), "version": c["version"], "amended_at": _now()}
    if body.new_principle:
        amendment["new_principle"] = body.new_principle.model_dump()
    amendments.append(amendment)
    return {"constitution_id": cid, "new_version": c["version"], "amendment": amendment}

# ── System Registry ──────────────────────────────────────────────────
@app.post("/v1/systems", status_code=201)
def create_system(body: SystemCreate):
    sid = str(uuid.uuid4())
    rec = {
        "id": sid,
        **body.model_dump(),
        "bound_constitution_id": None,
        "compliance_score": 100.0,
        "compliance_trend": "stable",
        "observation_count": 0,
        "violation_count": 0,
        "created_at": _now(),
    }
    systems[sid] = rec
    return rec

@app.get("/v1/systems")
def list_systems(system_type: Optional[SystemType] = None, risk_tier: Optional[RiskTier] = None):
    out = list(systems.values())
    if system_type:
        out = [s for s in out if s["system_type"] == system_type]
    if risk_tier:
        out = [s for s in out if s["risk_tier"] == risk_tier]
    return out

@app.post("/v1/systems/{sid}/bind")
def bind_constitution(sid: str, constitution_id: str = Query(...)):
    if sid not in systems:
        raise HTTPException(404, "System not found")
    if constitution_id not in constitutions:
        raise HTTPException(404, "Constitution not found")
    systems[sid]["bound_constitution_id"] = constitution_id
    return {"system_id": sid, "bound_constitution_id": constitution_id}

# ── Observations ─────────────────────────────────────────────────────
@app.post("/v1/observations", status_code=201)
def create_observation(body: ObservationCreate):
    if body.system_id not in systems:
        raise HTTPException(404, "System not found")
    oid = str(uuid.uuid4())
    rec = {"id": oid, **body.model_dump(), "evaluated": False, "created_at": _now()}
    observations[oid] = rec
    systems[body.system_id]["observation_count"] += 1
    return rec

# ── Evaluation ───────────────────────────────────────────────────────
@app.post("/v1/observations/{oid}/evaluate")
def evaluate_observation(oid: str):
    if oid not in observations:
        raise HTTPException(404, "Observation not found")
    obs = observations[oid]
    if obs["evaluated"]:
        return {"observation_id": oid, "status": "already_evaluated", "violations": []}

    sys = systems.get(obs["system_id"])
    if not sys or not sys.get("bound_constitution_id"):
        raise HTTPException(400, "System has no bound constitution")

    const = constitutions.get(sys["bound_constitution_id"])
    if not const:
        raise HTTPException(404, "Bound constitution not found")

    new_violations = []
    for i, principle in enumerate(const["principles"]):
        # Simulated evaluation — random chance of violation based on enforcement level
        violation_chance = {"hard_constraint": 0.1, "soft_constraint": 0.2, "aspiration": 0.3}.get(principle["enforcement_level"], 0.2)
        if random.random() < violation_chance:
            vid = str(uuid.uuid4())
            recurrence = sum(1 for v in violations.values() if v["system_id"] == obs["system_id"] and v["principle_index"] == i)
            score, tier = _compute_severity_score(principle, sys, recurrence)

            violation = {
                "id": vid,
                "observation_id": oid,
                "system_id": obs["system_id"],
                "constitution_id": sys["bound_constitution_id"],
                "principle_index": i,
                "principle_text": principle["text"],
                "principle_category": principle["category"],
                "violation_type": random.choice(list(ViolationType)).value,
                "confidence": round(random.uniform(0.6, 0.99), 3),
                "severity_score": score,
                "severity_tier": tier,
                "evidence": f"Observation output '{obs['output_summary'][:50]}' potentially conflicts with principle: '{principle['text'][:60]}'",
                "remediation_status": "open",
                "created_at": _now(),
            }
            violations[vid] = violation
            new_violations.append(violation)
            sys["violation_count"] += 1

    obs["evaluated"] = True

    # Update compliance score
    total_obs = sys["observation_count"]
    total_viol = sys["violation_count"]
    sys["compliance_score"] = round(max(0, 100 - (total_viol / max(total_obs, 1)) * 100), 1)
    prev_score = sys.get("_prev_compliance", 100)
    if sys["compliance_score"] < prev_score - 2:
        sys["compliance_trend"] = "declining"
    elif sys["compliance_score"] > prev_score + 2:
        sys["compliance_trend"] = "improving"
    else:
        sys["compliance_trend"] = "stable"
    sys["_prev_compliance"] = sys["compliance_score"]

    return {"observation_id": oid, "violations_found": len(new_violations), "violations": new_violations}

# ── Violations ───────────────────────────────────────────────────────
@app.get("/v1/violations")
def list_violations(
    severity: Optional[SeverityTier] = None,
    system_id: Optional[str] = None,
    category: Optional[PrincipleCategory] = None,
):
    out = list(violations.values())
    if severity:
        out = [v for v in out if v["severity_tier"] == severity]
    if system_id:
        out = [v for v in out if v["system_id"] == system_id]
    if category:
        out = [v for v in out if v["principle_category"] == category]
    return sorted(out, key=lambda x: x["severity_score"], reverse=True)

@app.post("/v1/violations/{vid}/remediate")
def remediate_violation(vid: str, body: RemediateRequest):
    if vid not in violations:
        raise HTTPException(404, "Violation not found")
    v = violations[vid]
    v["remediation_status"] = "remediated"
    v["remediation_action"] = body.action
    v["remediation_notes"] = body.notes
    v["remediated_at"] = _now()
    return v

# ── Compliance Score ─────────────────────────────────────────────────
@app.get("/v1/systems/{sid}/compliance")
def system_compliance(sid: str):
    if sid not in systems:
        raise HTTPException(404, "System not found")
    s = systems[sid]
    sys_violations = [v for v in violations.values() if v["system_id"] == sid]
    by_category = {}
    for v in sys_violations:
        by_category[v["principle_category"]] = by_category.get(v["principle_category"], 0) + 1
    open_violations = sum(1 for v in sys_violations if v["remediation_status"] == "open")
    return {
        "system_id": sid,
        "system_name": s["name"],
        "compliance_score": s["compliance_score"],
        "trend": s["compliance_trend"],
        "total_observations": s["observation_count"],
        "total_violations": s["violation_count"],
        "open_violations": open_violations,
        "violations_by_category": by_category,
    }

# ── Report Generation ────────────────────────────────────────────────
@app.post("/v1/reports/generate")
def generate_report(system_id: Optional[str] = None):
    target_systems = [systems[system_id]] if system_id and system_id in systems else list(systems.values())
    system_summaries = []
    for s in target_systems:
        sys_v = [v for v in violations.values() if v["system_id"] == s["id"]]
        by_sev = {}
        for v in sys_v:
            by_sev[v["severity_tier"]] = by_sev.get(v["severity_tier"], 0) + 1
        system_summaries.append({
            "system_id": s["id"],
            "name": s["name"],
            "compliance_score": s["compliance_score"],
            "trend": s["compliance_trend"],
            "violations_by_severity": by_sev,
            "total_violations": len(sys_v),
        })

    all_v = list(violations.values())
    risk_heat = {}
    for v in all_v:
        risk_heat[v["principle_category"]] = risk_heat.get(v["principle_category"], 0) + v["severity_score"]

    return {
        "report_type": "constitutional_compliance",
        "systems_analysed": len(target_systems),
        "system_summaries": system_summaries,
        "total_violations": len(all_v),
        "risk_heat_map": risk_heat,
        "amendments_applied": len(amendments),
        "generated_at": _now(),
    }

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    vl = list(violations.values())
    sl = list(systems.values())
    by_severity = {}
    for v in vl:
        by_severity[v["severity_tier"]] = by_severity.get(v["severity_tier"], 0) + 1
    by_category = {}
    for v in vl:
        by_category[v["principle_category"]] = by_category.get(v["principle_category"], 0) + 1
    by_system = {}
    for v in vl:
        by_system[v["system_id"]] = by_system.get(v["system_id"], 0) + 1
    avg_compliance = sum(s["compliance_score"] for s in sl) / max(len(sl), 1)
    remediated = sum(1 for v in vl if v["remediation_status"] == "remediated")
    return {
        "total_constitutions": len(constitutions),
        "total_systems": len(sl),
        "total_observations": len(observations),
        "total_violations": len(vl),
        "violations_by_severity": by_severity,
        "violations_by_category": by_category,
        "violations_by_system": by_system,
        "violations_remediated": remediated,
        "avg_compliance_score": round(avg_compliance, 1),
        "total_amendments": len(amendments),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9909)
