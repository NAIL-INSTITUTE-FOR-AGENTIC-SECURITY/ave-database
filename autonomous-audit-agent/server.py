"""Autonomous Audit Agent — Phase 26 Service 2 · Port 9906"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random, hashlib

app = FastAPI(title="Autonomous Audit Agent", version="0.26.2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class TargetType(str, Enum):
    api_service = "api_service"
    database = "database"
    ai_model = "ai_model"
    pipeline = "pipeline"
    infrastructure = "infrastructure"

class CampaignType(str, Enum):
    scheduled = "scheduled"
    continuous = "continuous"
    triggered = "triggered"
    spot_check = "spot_check"
    deep_dive = "deep_dive"
    post_incident = "post_incident"

class CampaignState(str, Enum):
    planned = "planned"
    running = "running"
    analysing = "analysing"
    reporting = "reporting"
    closed = "closed"

CAMPAIGN_TRANSITIONS = {
    "planned": ["running"],
    "running": ["analysing"],
    "analysing": ["reporting"],
    "reporting": ["closed"],
}

class ProbeType(str, Enum):
    health_check = "health_check"
    log_analysis = "log_analysis"
    config_drift = "config_drift"
    permission_scan = "permission_scan"
    data_flow_trace = "data_flow_trace"
    model_drift = "model_drift"
    latency_profile = "latency_profile"

class FindingSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"

class FindingType(str, Enum):
    violation = "violation"
    anomaly = "anomaly"
    warning = "warning"
    observation = "observation"
    recommendation = "recommendation"

class RemediationType(str, Enum):
    auto_fix = "auto_fix"
    escalate = "escalate"
    quarantine = "quarantine"
    notify = "notify"
    log_only = "log_only"

class AnomalyCategory(str, Enum):
    spike = "spike"
    drift = "drift"
    pattern_break = "pattern_break"
    missing_data = "missing_data"
    threshold_breach = "threshold_breach"

# ── Models ───────────────────────────────────────────────────────────
class TargetCreate(BaseModel):
    name: str
    target_type: TargetType
    audit_domains: list[str] = ["security"]
    endpoint_url: str = ""
    monitoring_interval_minutes: int = Field(60, ge=5)

class CampaignCreate(BaseModel):
    name: str
    campaign_type: CampaignType
    target_ids: list[str] = []
    description: str = ""

class ProbeRequest(BaseModel):
    target_id: str
    probe_type: ProbeType
    parameters: dict = {}

class RemediateRequest(BaseModel):
    remediation_type: RemediationType
    notes: str = ""

# ── Stores ───────────────────────────────────────────────────────────
targets: dict[str, dict] = {}
campaigns: dict[str, dict] = {}
findings: dict[str, dict] = {}
reports: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Simulated Probe Execution ────────────────────────────────────────
def _run_probe(target: dict, probe_type: ProbeType) -> dict:
    """Simulate running a probe and generating findings."""
    passed = random.random() > 0.3
    baseline = random.uniform(50, 100)
    current = baseline + random.uniform(-20, 20)
    z_score = round((current - baseline) / max(random.uniform(1, 10), 0.1), 3)
    anomaly = abs(z_score) > 2.0

    result = {
        "probe_type": probe_type,
        "target_id": target["id"],
        "target_name": target["name"],
        "passed": passed and not anomaly,
        "baseline_value": round(baseline, 2),
        "current_value": round(current, 2),
        "z_score": z_score,
        "anomaly_detected": anomaly,
        "anomaly_category": random.choice(list(AnomalyCategory)).value if anomaly else None,
        "detail": f"Probe {probe_type} {'passed' if passed else 'failed'} for {target['name']}",
        "executed_at": _now(),
    }
    return result

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "autonomous-audit-agent",
        "status": "healthy",
        "version": "0.26.2",
        "targets": len(targets),
        "campaigns": len(campaigns),
        "findings": len(findings),
    }

# ── Target CRUD ──────────────────────────────────────────────────────
@app.post("/v1/targets", status_code=201)
def create_target(body: TargetCreate):
    tid = str(uuid.uuid4())
    rec = {"id": tid, **body.model_dump(), "created_at": _now(), "last_audited_at": None}
    targets[tid] = rec
    return rec

@app.get("/v1/targets")
def list_targets(target_type: Optional[TargetType] = None):
    out = list(targets.values())
    if target_type:
        out = [t for t in out if t["target_type"] == target_type]
    return out

# ── Campaign CRUD ────────────────────────────────────────────────────
@app.post("/v1/campaigns", status_code=201)
def create_campaign(body: CampaignCreate):
    for tid in body.target_ids:
        if tid not in targets:
            raise HTTPException(404, f"Target {tid} not found")
    cid = str(uuid.uuid4())
    rec = {
        "id": cid,
        **body.model_dump(),
        "state": "planned",
        "probe_results": [],
        "finding_ids": [],
        "created_at": _now(),
        "started_at": None,
        "closed_at": None,
    }
    campaigns[cid] = rec
    return rec

@app.get("/v1/campaigns")
def list_campaigns(state: Optional[CampaignState] = None, campaign_type: Optional[CampaignType] = None):
    out = list(campaigns.values())
    if state:
        out = [c for c in out if c["state"] == state]
    if campaign_type:
        out = [c for c in out if c["campaign_type"] == campaign_type]
    return out

@app.get("/v1/campaigns/{cid}")
def get_campaign(cid: str):
    if cid not in campaigns:
        raise HTTPException(404, "Campaign not found")
    return campaigns[cid]

@app.patch("/v1/campaigns/{cid}/advance")
def advance_campaign(cid: str, target_state: CampaignState = Query(...)):
    if cid not in campaigns:
        raise HTTPException(404, "Campaign not found")
    c = campaigns[cid]
    allowed = CAMPAIGN_TRANSITIONS.get(c["state"], [])
    if target_state not in allowed:
        raise HTTPException(400, f"Cannot transition from {c['state']} to {target_state}")
    c["state"] = target_state
    if target_state == "running":
        c["started_at"] = _now()
    if target_state == "closed":
        c["closed_at"] = _now()
    return c

# ── Probes ───────────────────────────────────────────────────────────
@app.post("/v1/campaigns/{cid}/probe")
def run_probe(cid: str, body: ProbeRequest):
    if cid not in campaigns:
        raise HTTPException(404, "Campaign not found")
    if body.target_id not in targets:
        raise HTTPException(404, "Target not found")
    c = campaigns[cid]
    if c["state"] != "running":
        raise HTTPException(400, "Campaign must be running to probe")

    result = _run_probe(targets[body.target_id], body.probe_type)
    c["probe_results"].append(result)

    # Auto-generate finding if probe failed or anomaly
    if not result["passed"] or result["anomaly_detected"]:
        fid = str(uuid.uuid4())
        severity = "critical" if result.get("anomaly_category") == "threshold_breach" else random.choice(["high", "medium", "low"])
        finding = {
            "id": fid,
            "campaign_id": cid,
            "target_id": body.target_id,
            "finding_type": "anomaly" if result["anomaly_detected"] else "violation",
            "severity": severity,
            "description": result["detail"],
            "evidence": {"probe_result": result},
            "remediation_status": "open",
            "created_at": _now(),
        }
        findings[fid] = finding
        c["finding_ids"].append(fid)
        result["finding_id"] = fid

    targets[body.target_id]["last_audited_at"] = _now()
    return result

# ── Findings ─────────────────────────────────────────────────────────
@app.get("/v1/findings")
def list_findings(
    severity: Optional[FindingSeverity] = None,
    finding_type: Optional[FindingType] = None,
    target_id: Optional[str] = None,
):
    out = list(findings.values())
    if severity:
        out = [f for f in out if f["severity"] == severity]
    if finding_type:
        out = [f for f in out if f["finding_type"] == finding_type]
    if target_id:
        out = [f for f in out if f["target_id"] == target_id]
    return sorted(out, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(x["severity"], 5))

@app.post("/v1/findings/{fid}/remediate")
def remediate_finding(fid: str, body: RemediateRequest):
    if fid not in findings:
        raise HTTPException(404, "Finding not found")
    f = findings[fid]
    f["remediation_status"] = "remediated"
    f["remediation_type"] = body.remediation_type
    f["remediation_notes"] = body.notes
    f["remediated_at"] = _now()
    return f

# ── Report Generation ────────────────────────────────────────────────
@app.post("/v1/campaigns/{cid}/report")
def generate_report(cid: str):
    if cid not in campaigns:
        raise HTTPException(404, "Campaign not found")
    c = campaigns[cid]
    camp_findings = [findings[fid] for fid in c["finding_ids"] if fid in findings]
    sev_counts = {}
    for f in camp_findings:
        sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1

    total_probes = len(c["probe_results"])
    failed_probes = sum(1 for p in c["probe_results"] if not p["passed"])
    risk_score = min(100, round((sev_counts.get("critical", 0) * 30 + sev_counts.get("high", 0) * 20 + sev_counts.get("medium", 0) * 10 + sev_counts.get("low", 0) * 5) / max(total_probes, 1) * 10, 1))

    report = {
        "campaign_id": cid,
        "campaign_name": c["name"],
        "executive_summary": f"Audit campaign '{c['name']}' executed {total_probes} probes across {len(c['target_ids'])} targets. {failed_probes} probes flagged issues. Risk score: {risk_score}/100.",
        "risk_score": risk_score,
        "probes_executed": total_probes,
        "probes_failed": failed_probes,
        "findings_by_severity": sev_counts,
        "total_findings": len(camp_findings),
        "recommendations": [
            f"Address {sev_counts.get('critical', 0)} critical findings immediately" if sev_counts.get("critical") else None,
            f"Review {sev_counts.get('high', 0)} high-severity findings within 48h" if sev_counts.get("high") else None,
            "Schedule follow-up audit in 30 days" if risk_score > 50 else "No urgent follow-up needed",
        ],
        "generated_at": _now(),
    }
    report["recommendations"] = [r for r in report["recommendations"] if r]
    reports[cid] = report
    return report

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    cl = list(campaigns.values())
    fl = list(findings.values())
    by_state = {}
    for c in cl:
        by_state[c["state"]] = by_state.get(c["state"], 0) + 1
    by_type = {}
    for c in cl:
        by_type[c["campaign_type"]] = by_type.get(c["campaign_type"], 0) + 1
    by_severity = {}
    for f in fl:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
    by_finding_type = {}
    for f in fl:
        by_finding_type[f["finding_type"]] = by_finding_type.get(f["finding_type"], 0) + 1
    remediated = sum(1 for f in fl if f["remediation_status"] == "remediated")
    return {
        "total_targets": len(targets),
        "total_campaigns": len(cl),
        "campaigns_by_state": by_state,
        "campaigns_by_type": by_type,
        "total_findings": len(fl),
        "findings_by_severity": by_severity,
        "findings_by_type": by_finding_type,
        "findings_remediated": remediated,
        "reports_generated": len(reports),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9906)
