"""Regulation Simulator — Phase 26 Service 4 · Port 9908"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random

app = FastAPI(title="Regulation Simulator", version="0.26.4")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class RegDomain(str, Enum):
    ai_governance = "ai_governance"
    data_privacy = "data_privacy"
    security = "security"
    financial = "financial"
    healthcare = "healthcare"
    environmental = "environmental"

class RegStatus(str, Enum):
    proposed = "proposed"
    adopted = "adopted"
    enforced = "enforced"
    repealed = "repealed"

class SandboxType(str, Enum):
    full_clone = "full_clone"
    lightweight = "lightweight"
    config_only = "config_only"

class SandboxState(str, Enum):
    provisioning = "provisioning"
    ready = "ready"
    running = "running"
    analysing = "analysing"
    terminated = "terminated"

SANDBOX_TRANSITIONS = {
    "provisioning": ["ready"],
    "ready": ["running"],
    "running": ["analysing"],
    "analysing": ["terminated", "running"],
}

class WorkloadType(str, Enum):
    api_traffic = "api_traffic"
    data_processing = "data_processing"
    model_inference = "model_inference"
    batch_job = "batch_job"
    user_interaction = "user_interaction"

class RiskLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"

# ── Models ───────────────────────────────────────────────────────────
class RegulationCreate(BaseModel):
    name: str
    jurisdiction: str
    domain: RegDomain
    description: str = ""
    effective_date: str = ""
    requirements: list[str] = []
    status: RegStatus = RegStatus.proposed

class SandboxCreate(BaseModel):
    name: str
    sandbox_type: SandboxType = SandboxType.lightweight
    regulation_ids: list[str] = []
    ttl_hours: int = Field(24, ge=1)

class SimulationRequest(BaseModel):
    workload_type: WorkloadType
    volume_rps: int = Field(100, ge=1)
    duration_minutes: int = Field(10, ge=1)

class CompareRequest(BaseModel):
    regulation_id_a: str
    regulation_id_b: str

# ── Stores ───────────────────────────────────────────────────────────
regulations: dict[str, dict] = {}
sandboxes: dict[str, dict] = {}
simulations: list[dict] = []
impact_reports: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Simulated Metrics ────────────────────────────────────────────────
def _generate_metrics(with_regulation: bool) -> dict:
    base_latency_p50 = random.uniform(10, 50)
    penalty = random.uniform(1.05, 1.3) if with_regulation else 1.0
    return {
        "latency_p50_ms": round(base_latency_p50 * penalty, 1),
        "latency_p95_ms": round(base_latency_p50 * 2.5 * penalty, 1),
        "latency_p99_ms": round(base_latency_p50 * 5 * penalty, 1),
        "error_rate": round(random.uniform(0.001, 0.05) * (penalty if with_regulation else 1), 4),
        "throughput_rps": round(random.uniform(80, 200) / penalty, 1),
        "compliance_violations": random.randint(0, 3) if with_regulation else 0,
    }

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "regulation-simulator",
        "status": "healthy",
        "version": "0.26.4",
        "regulations": len(regulations),
        "sandboxes": len(sandboxes),
        "simulations": len(simulations),
    }

# ── Regulation CRUD ──────────────────────────────────────────────────
@app.post("/v1/regulations", status_code=201)
def create_regulation(body: RegulationCreate):
    rid = str(uuid.uuid4())
    rec = {"id": rid, **body.model_dump(), "created_at": _now()}
    regulations[rid] = rec
    return rec

@app.get("/v1/regulations")
def list_regulations(domain: Optional[RegDomain] = None, status: Optional[RegStatus] = None):
    out = list(regulations.values())
    if domain:
        out = [r for r in out if r["domain"] == domain]
    if status:
        out = [r for r in out if r["status"] == status]
    return out

# ── Sandbox CRUD ─────────────────────────────────────────────────────
@app.post("/v1/sandboxes", status_code=201)
def create_sandbox(body: SandboxCreate):
    for rid in body.regulation_ids:
        if rid not in regulations:
            raise HTTPException(404, f"Regulation {rid} not found")
    sid = str(uuid.uuid4())
    rec = {
        "id": sid,
        **body.model_dump(),
        "state": "provisioning",
        "simulations": [],
        "created_at": _now(),
        "rollback_point": None,
    }
    sandboxes[sid] = rec
    return rec

@app.get("/v1/sandboxes")
def list_sandboxes(state: Optional[SandboxState] = None):
    out = list(sandboxes.values())
    if state:
        out = [s for s in out if s["state"] == state]
    return out

@app.get("/v1/sandboxes/{sid}")
def get_sandbox(sid: str):
    if sid not in sandboxes:
        raise HTTPException(404, "Sandbox not found")
    return sandboxes[sid]

@app.patch("/v1/sandboxes/{sid}/advance")
def advance_sandbox(sid: str, target_state: SandboxState = Query(...)):
    if sid not in sandboxes:
        raise HTTPException(404, "Sandbox not found")
    s = sandboxes[sid]
    allowed = SANDBOX_TRANSITIONS.get(s["state"], [])
    if target_state not in allowed:
        raise HTTPException(400, f"Cannot transition from {s['state']} to {target_state}")
    s["state"] = target_state
    return s

# ── Simulation ───────────────────────────────────────────────────────
@app.post("/v1/sandboxes/{sid}/simulate")
def run_simulation(sid: str, body: SimulationRequest):
    if sid not in sandboxes:
        raise HTTPException(404, "Sandbox not found")
    s = sandboxes[sid]
    if s["state"] != "running":
        raise HTTPException(400, "Sandbox must be running")

    baseline = _generate_metrics(with_regulation=False)
    regulated = _generate_metrics(with_regulation=True)

    sim = {
        "simulation_id": str(uuid.uuid4()),
        "sandbox_id": sid,
        "workload_type": body.workload_type,
        "volume_rps": body.volume_rps,
        "duration_minutes": body.duration_minutes,
        "baseline_metrics": baseline,
        "regulated_metrics": regulated,
        "delta": {
            "latency_p50_delta_pct": round((regulated["latency_p50_ms"] - baseline["latency_p50_ms"]) / baseline["latency_p50_ms"] * 100, 1),
            "error_rate_delta": round(regulated["error_rate"] - baseline["error_rate"], 4),
            "throughput_delta_pct": round((regulated["throughput_rps"] - baseline["throughput_rps"]) / baseline["throughput_rps"] * 100, 1),
        },
        "executed_at": _now(),
    }
    s["simulations"].append(sim["simulation_id"])
    s["rollback_point"] = sim["simulation_id"]
    simulations.append(sim)
    return sim

# ── Impact Prediction ────────────────────────────────────────────────
@app.post("/v1/sandboxes/{sid}/impact")
def predict_impact(sid: str):
    if sid not in sandboxes:
        raise HTTPException(404, "Sandbox not found")
    s = sandboxes[sid]
    reg_count = len(s["regulation_ids"])
    reqs = sum(len(regulations.get(rid, {}).get("requirements", [])) for rid in s["regulation_ids"])

    affected = random.randint(1, 10)
    gaps = random.randint(0, reqs)
    hours = gaps * random.uniform(4, 20)
    risk = "critical" if gaps > 5 else "high" if gaps > 3 else "medium" if gaps > 1 else "low" if gaps > 0 else "none"

    report = {
        "sandbox_id": sid,
        "regulations_tested": reg_count,
        "total_requirements": reqs,
        "affected_systems": affected,
        "compliance_gaps": gaps,
        "estimated_remediation_hours": round(hours, 1),
        "risk_level": risk,
        "cost_impact_estimate": round(hours * 150, 2),
        "generated_at": _now(),
    }
    impact_reports[sid] = report
    return report

# ── Compatibility Check ──────────────────────────────────────────────
@app.post("/v1/sandboxes/{sid}/compatibility")
def check_compatibility(sid: str):
    if sid not in sandboxes:
        raise HTTPException(404, "Sandbox not found")
    checks = [
        {"check_type": "technical_feasibility", "passed": random.random() > 0.2, "detail": "System supports required encryption standards" if random.random() > 0.3 else "Missing required audit logging capability"},
        {"check_type": "policy_conflict", "passed": random.random() > 0.3, "detail": "No conflicting policies detected" if random.random() > 0.4 else "Conflict with existing data retention policy"},
        {"check_type": "resource_requirement", "passed": random.random() > 0.15, "detail": "Sufficient compute resources available"},
        {"check_type": "timeline_feasibility", "passed": random.random() > 0.25, "detail": "Implementation timeline within effective date"},
    ]
    return {"sandbox_id": sid, "checks": checks, "all_passed": all(c["passed"] for c in checks)}

# ── A/B Comparison ───────────────────────────────────────────────────
@app.post("/v1/sandboxes/{sid}/compare")
def compare_regulations(sid: str, body: CompareRequest):
    if body.regulation_id_a not in regulations or body.regulation_id_b not in regulations:
        raise HTTPException(404, "One or both regulations not found")
    metrics_a = _generate_metrics(with_regulation=True)
    metrics_b = _generate_metrics(with_regulation=True)

    a_score = metrics_a["throughput_rps"] / (metrics_a["latency_p50_ms"] * (1 + metrics_a["error_rate"]))
    b_score = metrics_b["throughput_rps"] / (metrics_b["latency_p50_ms"] * (1 + metrics_b["error_rate"]))
    recommendation = "adopt_a" if a_score > b_score else "adopt_b" if b_score > a_score else "equivalent"

    return {
        "sandbox_id": sid,
        "regulation_a": {"id": body.regulation_id_a, "name": regulations[body.regulation_id_a]["name"], "metrics": metrics_a, "composite_score": round(a_score, 4)},
        "regulation_b": {"id": body.regulation_id_b, "name": regulations[body.regulation_id_b]["name"], "metrics": metrics_b, "composite_score": round(b_score, 4)},
        "recommendation": recommendation,
    }

# ── Rollback ─────────────────────────────────────────────────────────
@app.post("/v1/sandboxes/{sid}/rollback")
def rollback_sandbox(sid: str, reason: str = ""):
    if sid not in sandboxes:
        raise HTTPException(404, "Sandbox not found")
    s = sandboxes[sid]
    rollback_point = s.get("rollback_point")
    s["state"] = "ready"
    s["simulations"] = []
    s["rollback_point"] = None
    return {"sandbox_id": sid, "rolled_back_to": rollback_point, "reason": reason, "new_state": "ready"}

# ── Report ───────────────────────────────────────────────────────────
@app.post("/v1/sandboxes/{sid}/report")
def generate_report(sid: str):
    if sid not in sandboxes:
        raise HTTPException(404, "Sandbox not found")
    s = sandboxes[sid]
    sims = [sim for sim in simulations if sim["sandbox_id"] == sid]
    impact = impact_reports.get(sid, {})

    avg_latency_delta = sum(sim["delta"]["latency_p50_delta_pct"] for sim in sims) / max(len(sims), 1) if sims else 0
    avg_throughput_delta = sum(sim["delta"]["throughput_delta_pct"] for sim in sims) / max(len(sims), 1) if sims else 0

    return {
        "sandbox_id": sid,
        "executive_summary": f"Sandbox '{s['name']}' tested {len(s['regulation_ids'])} regulations across {len(sims)} simulations. Avg latency impact: {avg_latency_delta:+.1f}%, avg throughput impact: {avg_throughput_delta:+.1f}%.",
        "simulations_run": len(sims),
        "avg_latency_delta_pct": round(avg_latency_delta, 1),
        "avg_throughput_delta_pct": round(avg_throughput_delta, 1),
        "impact_assessment": impact,
        "recommendation": "proceed" if avg_latency_delta < 20 and avg_throughput_delta > -20 else "review_needed",
        "generated_at": _now(),
    }

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    rl = list(regulations.values())
    sl = list(sandboxes.values())
    by_domain = {}
    for r in rl:
        by_domain[r["domain"]] = by_domain.get(r["domain"], 0) + 1
    by_state = {}
    for s in sl:
        by_state[s["state"]] = by_state.get(s["state"], 0) + 1
    by_jurisdiction = {}
    for r in rl:
        by_jurisdiction[r["jurisdiction"]] = by_jurisdiction.get(r["jurisdiction"], 0) + 1
    return {
        "total_regulations": len(rl),
        "regulations_by_domain": by_domain,
        "regulations_by_jurisdiction": by_jurisdiction,
        "total_sandboxes": len(sl),
        "sandboxes_by_state": by_state,
        "total_simulations": len(simulations),
        "impact_reports": len(impact_reports),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9908)
