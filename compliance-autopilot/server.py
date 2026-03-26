"""
Regulatory Compliance Autopilot — Core compliance server.

Continuous regulatory monitoring and automated compliance management
for AI agent deployments across 8+ jurisdictions.  Ingests
regulations, parses AI-specific requirements, maps to AVE controls,
performs gap analysis, calculates impact scores, auto-generates
policy adjustments with a human approval gate, and maintains an
immutable audit trail.
"""

from __future__ import annotations

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
    title="NAIL Regulatory Compliance Autopilot",
    description=(
        "Continuous regulatory monitoring, AI requirement parsing, "
        "gap analysis, and policy auto-adjustment with human oversight."
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
# Constants
# ---------------------------------------------------------------------------

JURISDICTIONS = {
    "US": "United States",
    "EU": "European Union",
    "UK": "United Kingdom",
    "AU": "Australia",
    "CA": "Canada",
    "SG": "Singapore",
    "JP": "Japan",
    "BR": "Brazil",
}

FRAMEWORKS = [
    "NIST AI RMF 1.0",
    "EU AI Act",
    "ISO 42001",
    "OWASP Top 10 LLM",
    "ISO 27001:2022",
    "SOC 2 Type II",
    "NIST SP 800-53",
    "GDPR",
    "CCPA / CPRA",
    "BSI AI Security Guidelines",
]

AVE_CATEGORIES = [
    "prompt_injection", "tool_misuse", "memory_poisoning", "goal_hijacking",
    "identity_spoofing", "privilege_escalation", "data_exfiltration",
    "resource_exhaustion", "multi_agent_manipulation", "context_overflow",
    "guardrail_bypass", "output_manipulation", "supply_chain_compromise",
    "model_extraction", "reward_hacking", "capability_elicitation",
    "alignment_subversion", "delegation_abuse",
]

CONTROL_AREAS = [
    "input_validation", "output_filtering", "access_control", "audit_logging",
    "encryption", "key_management", "rate_limiting", "sandboxing",
    "monitoring", "incident_response", "supply_chain_integrity",
    "model_governance", "data_protection", "transparency", "human_oversight",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RegStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    UPCOMING = "upcoming"
    SUPERSEDED = "superseded"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    PROHIBITED = "prohibited"


class GapSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AdjustmentStatus(str, Enum):
    PROPOSED = "proposed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class Requirement(BaseModel):
    id: str = Field(default_factory=lambda: f"REQ-{uuid.uuid4().hex[:6].upper()}")
    text: str
    category: str = ""
    ave_controls: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM


class Regulation(BaseModel):
    id: str = Field(default_factory=lambda: f"REG-{uuid.uuid4().hex[:8].upper()}")
    name: str
    jurisdiction: str
    version: str = "1.0"
    status: RegStatus = RegStatus.ACTIVE
    description: str = ""
    effective_date: str = ""
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requirements: list[Requirement] = Field(default_factory=list)
    ai_risk_class: RiskLevel = RiskLevel.MEDIUM
    frameworks_mapped: list[str] = Field(default_factory=list)


class RegCreate(BaseModel):
    name: str
    jurisdiction: str
    version: str = "1.0"
    description: str = ""
    ai_risk_class: RiskLevel = RiskLevel.MEDIUM
    auto_parse: bool = True


class GapItem(BaseModel):
    id: str = Field(default_factory=lambda: f"GAP-{uuid.uuid4().hex[:8].upper()}")
    regulation_id: str
    requirement_id: str
    control_area: str
    severity: GapSeverity
    description: str
    remediation: str = ""
    effort_days: int = 1
    impact_score: float = Field(ge=0.0, le=10.0, default=5.0)
    status: str = "open"  # open | mitigated | accepted


class GapAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: f"GAPA-{uuid.uuid4().hex[:8].upper()}")
    jurisdiction: Optional[str] = None
    regulation_id: Optional[str] = None
    gaps: list[GapItem] = Field(default_factory=list)
    posture_score: float = 0.0  # 0-100
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AnalyseRequest(BaseModel):
    jurisdiction: Optional[str] = None
    regulation_id: Optional[str] = None
    control_areas: list[str] = Field(default_factory=lambda: CONTROL_AREAS[:])


class Adjustment(BaseModel):
    id: str = Field(default_factory=lambda: f"ADJ-{uuid.uuid4().hex[:8].upper()}")
    gap_id: str
    regulation_id: str
    control_area: str
    description: str
    policy_change: str
    impact: str = ""
    status: AdjustmentStatus = AdjustmentStatus.PROPOSED
    proposed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation: str
    entity_id: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → PostgreSQL + event log)
# ---------------------------------------------------------------------------

REGULATIONS: dict[str, Regulation] = {}
GAP_ANALYSES: dict[str, GapAnalysis] = {}
ADJUSTMENTS: dict[str, Adjustment] = {}
AUDIT_LOG: list[AuditEntry] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


def _audit(operation: str, entity_id: str = "", **details):
    entry = AuditEntry(operation=operation, entity_id=entity_id, details=details)
    AUDIT_LOG.append(entry)
    return entry


def _auto_parse_requirements(regulation: Regulation) -> list[Requirement]:
    """Simulate AI requirement parsing from regulation text."""
    # Each jurisdiction triggers different focus areas
    focus: dict[str, list[str]] = {
        "EU": ["transparency", "human_oversight", "data_protection", "model_governance"],
        "US": ["audit_logging", "access_control", "incident_response", "monitoring"],
        "UK": ["transparency", "audit_logging", "data_protection", "sandboxing"],
        "AU": ["access_control", "data_protection", "monitoring", "human_oversight"],
        "CA": ["data_protection", "transparency", "audit_logging", "encryption"],
        "SG": ["monitoring", "access_control", "encryption", "incident_response"],
        "JP": ["model_governance", "transparency", "human_oversight", "output_filtering"],
        "BR": ["data_protection", "transparency", "audit_logging", "human_oversight"],
    }

    areas = focus.get(regulation.jurisdiction, CONTROL_AREAS[:4])
    risk_map = {
        RiskLevel.LOW: [RiskLevel.LOW, RiskLevel.LOW, RiskLevel.MEDIUM],
        RiskLevel.MEDIUM: [RiskLevel.MEDIUM, RiskLevel.MEDIUM, RiskLevel.HIGH],
        RiskLevel.HIGH: [RiskLevel.HIGH, RiskLevel.HIGH, RiskLevel.CRITICAL],
        RiskLevel.CRITICAL: [RiskLevel.CRITICAL, RiskLevel.CRITICAL, RiskLevel.CRITICAL],
        RiskLevel.PROHIBITED: [RiskLevel.PROHIBITED],
    }

    requirements: list[Requirement] = []
    for area in areas:
        # Map control area to AVE categories
        ave_mapping: dict[str, list[str]] = {
            "input_validation": ["prompt_injection", "context_overflow"],
            "output_filtering": ["output_manipulation", "data_exfiltration"],
            "access_control": ["privilege_escalation", "identity_spoofing"],
            "audit_logging": ["tool_misuse", "delegation_abuse"],
            "encryption": ["data_exfiltration", "model_extraction"],
            "key_management": ["identity_spoofing", "supply_chain_compromise"],
            "rate_limiting": ["resource_exhaustion", "context_overflow"],
            "sandboxing": ["tool_misuse", "privilege_escalation"],
            "monitoring": ["multi_agent_manipulation", "alignment_subversion"],
            "incident_response": ["goal_hijacking", "reward_hacking"],
            "supply_chain_integrity": ["supply_chain_compromise", "capability_elicitation"],
            "model_governance": ["model_extraction", "alignment_subversion"],
            "data_protection": ["data_exfiltration", "memory_poisoning"],
            "transparency": ["output_manipulation", "guardrail_bypass"],
            "human_oversight": ["delegation_abuse", "goal_hijacking"],
        }

        controls = ave_mapping.get(area, [])
        risk = random.choice(risk_map.get(regulation.ai_risk_class, [RiskLevel.MEDIUM]))

        # Determine relevant frameworks
        fw_mapping: dict[str, list[str]] = {
            "data_protection": ["GDPR", "CCPA / CPRA"],
            "transparency": ["EU AI Act", "NIST AI RMF 1.0"],
            "human_oversight": ["EU AI Act", "ISO 42001"],
            "access_control": ["ISO 27001:2022", "NIST SP 800-53"],
            "audit_logging": ["SOC 2 Type II", "ISO 27001:2022"],
            "monitoring": ["NIST AI RMF 1.0", "OWASP Top 10 LLM"],
        }
        frameworks = fw_mapping.get(area, ["NIST AI RMF 1.0"])

        req = Requirement(
            text=f"Requirement for {area.replace('_', ' ')} under {regulation.name}",
            category=area,
            ave_controls=controls,
            frameworks=frameworks,
            risk_level=risk,
        )
        requirements.append(req)

    return requirements


def _perform_gap_analysis(
    regulations: list[Regulation],
    control_areas: list[str],
) -> GapAnalysis:
    """Perform gap analysis across selected regulations and controls."""
    gaps: list[GapItem] = []
    rng = random.Random(42)  # Deterministic for demo

    for reg in regulations:
        for req in reg.requirements:
            if req.category not in control_areas:
                continue

            # Simulate coverage gaps — probability based on risk level
            gap_prob = {
                RiskLevel.LOW: 0.2,
                RiskLevel.MEDIUM: 0.35,
                RiskLevel.HIGH: 0.5,
                RiskLevel.CRITICAL: 0.65,
                RiskLevel.PROHIBITED: 0.8,
            }

            if rng.random() < gap_prob.get(req.risk_level, 0.3):
                sev_map = {
                    RiskLevel.LOW: GapSeverity.LOW,
                    RiskLevel.MEDIUM: GapSeverity.MEDIUM,
                    RiskLevel.HIGH: GapSeverity.HIGH,
                    RiskLevel.CRITICAL: GapSeverity.CRITICAL,
                    RiskLevel.PROHIBITED: GapSeverity.CRITICAL,
                }
                severity = sev_map.get(req.risk_level, GapSeverity.MEDIUM)
                impact = round(rng.uniform(3.0, 9.5), 1)
                effort = rng.randint(1, 30)

                gap = GapItem(
                    regulation_id=reg.id,
                    requirement_id=req.id,
                    control_area=req.category,
                    severity=severity,
                    description=f"Incomplete {req.category.replace('_', ' ')} for {reg.name}: {req.text}",
                    remediation=f"Implement {req.category.replace('_', ' ')} controls mapped to AVE categories: {', '.join(req.ave_controls)}",
                    effort_days=effort,
                    impact_score=impact,
                )
                gaps.append(gap)

    # Posture score: 100 - penalty from gaps
    total_possible = sum(len(r.requirements) for r in regulations)
    gap_penalty = sum(g.impact_score for g in gaps)
    posture = max(0.0, 100.0 - (gap_penalty / max(total_possible, 1)) * 10)

    analysis = GapAnalysis(
        gaps=gaps,
        posture_score=round(posture, 2),
    )
    return analysis


def _generate_adjustments(analysis: GapAnalysis) -> list[Adjustment]:
    """Auto-generate policy adjustments for identified gaps."""
    adjustments: list[Adjustment] = []

    policy_templates: dict[str, str] = {
        "input_validation": "Enable strict input schema validation with deny-by-default policy",
        "output_filtering": "Activate output content scanning with PII/credential redaction",
        "access_control": "Enforce RBAC with least-privilege and just-in-time access",
        "audit_logging": "Enable immutable audit trail with 90-day retention minimum",
        "encryption": "Upgrade to PQ-safe encryption (ML-KEM-768) for data at rest and in transit",
        "key_management": "Implement automated key rotation with 90-day maximum lifecycle",
        "rate_limiting": "Configure adaptive rate limiting with circuit breaker patterns",
        "sandboxing": "Deploy tool execution sandbox with network isolation",
        "monitoring": "Enable real-time anomaly detection with < 5 min alerting SLA",
        "incident_response": "Activate automated containment playbook for high-severity events",
        "supply_chain_integrity": "Require SBOM + provenance attestation for all agent dependencies",
        "model_governance": "Implement model card registry with mandatory bias/safety testing",
        "data_protection": "Apply differential privacy and data minimisation policies",
        "transparency": "Publish decision audit trail and model explanation endpoints",
        "human_oversight": "Configure human-in-the-loop gates for high-risk classifications",
    }

    for gap in analysis.gaps:
        policy = policy_templates.get(
            gap.control_area,
            f"Review and strengthen {gap.control_area.replace('_', ' ')} controls",
        )

        adj = Adjustment(
            gap_id=gap.id,
            regulation_id=gap.regulation_id,
            control_area=gap.control_area,
            description=f"Auto-adjustment for {gap.severity.value} gap in {gap.control_area.replace('_', ' ')}",
            policy_change=policy,
            impact=f"Estimated {gap.effort_days} days implementation, impact score: {gap.impact_score}",
        )
        adjustments.append(adj)

    return adjustments


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    seed_regs = [
        ("EU AI Act", "EU", "Final", "Comprehensive regulation for AI systems in the EU", RiskLevel.HIGH),
        ("NIST AI RMF 1.0", "US", "1.0", "AI Risk Management Framework", RiskLevel.MEDIUM),
        ("UK AI Safety Framework", "UK", "1.0", "UK approach to AI safety and regulation", RiskLevel.MEDIUM),
        ("Australia AI Ethics Framework", "AU", "2.1", "Voluntary AI ethics principles", RiskLevel.LOW),
        ("Canada AIDA", "CA", "Draft", "Artificial Intelligence and Data Act", RiskLevel.MEDIUM),
        ("Singapore AI Governance", "SG", "2.0", "Model AI Governance Framework", RiskLevel.MEDIUM),
        ("Japan AI Guidelines", "JP", "1.2", "Social Principles of Human-Centric AI", RiskLevel.LOW),
        ("Brazil AI Framework", "BR", "1.0", "Legal framework for AI — Bill 2338/2023", RiskLevel.MEDIUM),
    ]

    for name, jurisdiction, version, desc, risk_class in seed_regs:
        reg = Regulation(
            name=name,
            jurisdiction=jurisdiction,
            version=version,
            description=desc,
            effective_date=(_now() - timedelta(days=random.randint(30, 365))).isoformat(),
            ai_risk_class=risk_class,
            frameworks_mapped=[fw for fw in FRAMEWORKS if random.random() > 0.5],
        )

        # Auto-parse requirements
        reg.requirements = _auto_parse_requirements(reg)
        REGULATIONS[reg.id] = reg
        _audit("regulation_ingested", reg.id, name=name, jurisdiction=jurisdiction)

    # Perform initial gap analysis
    all_regs = list(REGULATIONS.values())
    analysis = _perform_gap_analysis(all_regs, CONTROL_AREAS)
    analysis.jurisdiction = "ALL"
    GAP_ANALYSES[analysis.id] = analysis

    # Generate adjustments
    adjustments = _generate_adjustments(analysis)
    for adj in adjustments:
        ADJUSTMENTS[adj.id] = adj

    _audit("initial_gap_analysis", analysis.id, gaps=len(analysis.gaps), posture=analysis.posture_score)


_seed()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "regulatory-compliance-autopilot",
        "version": "1.0.0",
        "regulations": len(REGULATIONS),
        "jurisdictions": len(set(r.jurisdiction for r in REGULATIONS.values())),
        "gaps": sum(len(a.gaps) for a in GAP_ANALYSES.values()),
        "pending_adjustments": sum(1 for a in ADJUSTMENTS.values() if a.status == AdjustmentStatus.PROPOSED),
    }


# ---- Regulations ----------------------------------------------------------

@app.post("/v1/regulations", status_code=status.HTTP_201_CREATED)
async def ingest_regulation(data: RegCreate):
    if data.jurisdiction not in JURISDICTIONS:
        raise HTTPException(400, f"Unknown jurisdiction. Known: {list(JURISDICTIONS.keys())}")

    reg = Regulation(
        name=data.name,
        jurisdiction=data.jurisdiction,
        version=data.version,
        description=data.description,
        effective_date=_now().isoformat(),
        ai_risk_class=data.ai_risk_class,
    )

    if data.auto_parse:
        reg.requirements = _auto_parse_requirements(reg)
        reg.frameworks_mapped = list({fw for r in reg.requirements for fw in r.frameworks})

    REGULATIONS[reg.id] = reg
    _audit("regulation_ingested", reg.id, name=data.name, jurisdiction=data.jurisdiction)

    return {
        "id": reg.id,
        "name": reg.name,
        "jurisdiction": reg.jurisdiction,
        "requirements_parsed": len(reg.requirements),
        "frameworks_mapped": reg.frameworks_mapped,
    }


@app.get("/v1/regulations")
async def list_regulations(
    jurisdiction: Optional[str] = None,
    reg_status: Optional[RegStatus] = Query(None, alias="status"),
):
    regs = list(REGULATIONS.values())
    if jurisdiction:
        regs = [r for r in regs if r.jurisdiction == jurisdiction]
    if reg_status:
        regs = [r for r in regs if r.status == reg_status]
    return {
        "count": len(regs),
        "regulations": [
            {
                "id": r.id,
                "name": r.name,
                "jurisdiction": r.jurisdiction,
                "version": r.version,
                "status": r.status.value,
                "ai_risk_class": r.ai_risk_class.value,
                "requirements": len(r.requirements),
                "frameworks": r.frameworks_mapped,
            }
            for r in regs
        ],
    }


@app.get("/v1/regulations/{reg_id}")
async def get_regulation(reg_id: str):
    if reg_id not in REGULATIONS:
        raise HTTPException(404, "Regulation not found")
    return REGULATIONS[reg_id].dict()


# ---- Jurisdictions --------------------------------------------------------

@app.get("/v1/jurisdictions")
async def list_jurisdictions():
    juris_info: list[dict[str, Any]] = []
    for code, name in JURISDICTIONS.items():
        regs = [r for r in REGULATIONS.values() if r.jurisdiction == code]
        total_reqs = sum(len(r.requirements) for r in regs)
        juris_info.append({
            "code": code,
            "name": name,
            "regulations": len(regs),
            "total_requirements": total_reqs,
        })
    return {"count": len(JURISDICTIONS), "jurisdictions": juris_info}


# ---- Gap Analysis ---------------------------------------------------------

@app.post("/v1/analyse", status_code=status.HTTP_201_CREATED)
async def run_gap_analysis(req: AnalyseRequest):
    regs = list(REGULATIONS.values())
    if req.jurisdiction:
        if req.jurisdiction not in JURISDICTIONS:
            raise HTTPException(400, f"Unknown jurisdiction: {req.jurisdiction}")
        regs = [r for r in regs if r.jurisdiction == req.jurisdiction]
    if req.regulation_id:
        if req.regulation_id not in REGULATIONS:
            raise HTTPException(404, "Regulation not found")
        regs = [REGULATIONS[req.regulation_id]]

    if not regs:
        raise HTTPException(400, "No regulations match the filter")

    analysis = _perform_gap_analysis(regs, req.control_areas)
    analysis.jurisdiction = req.jurisdiction
    analysis.regulation_id = req.regulation_id
    GAP_ANALYSES[analysis.id] = analysis

    # Auto-generate adjustments
    adjustments = _generate_adjustments(analysis)
    for adj in adjustments:
        ADJUSTMENTS[adj.id] = adj

    _audit("gap_analysis_run", analysis.id, gaps=len(analysis.gaps), posture=analysis.posture_score)

    return {
        "id": analysis.id,
        "gaps_found": len(analysis.gaps),
        "posture_score": analysis.posture_score,
        "adjustments_proposed": len(adjustments),
        "by_severity": dict(Counter(g.severity.value for g in analysis.gaps)),
    }


@app.get("/v1/gaps")
async def list_gaps(
    severity: Optional[GapSeverity] = None,
    control_area: Optional[str] = None,
    gap_status: Optional[str] = Query(None, alias="status"),
):
    all_gaps: list[GapItem] = []
    for analysis in GAP_ANALYSES.values():
        all_gaps.extend(analysis.gaps)

    if severity:
        all_gaps = [g for g in all_gaps if g.severity == severity]
    if control_area:
        all_gaps = [g for g in all_gaps if g.control_area == control_area]
    if gap_status:
        all_gaps = [g for g in all_gaps if g.status == gap_status]

    all_gaps.sort(key=lambda g: g.impact_score, reverse=True)

    return {
        "count": len(all_gaps),
        "gaps": [g.dict() for g in all_gaps[:100]],
    }


# ---- Adjustments ----------------------------------------------------------

@app.get("/v1/adjustments")
async def list_adjustments(
    adj_status: Optional[AdjustmentStatus] = Query(None, alias="status"),
    control_area: Optional[str] = None,
):
    adjs = list(ADJUSTMENTS.values())
    if adj_status:
        adjs = [a for a in adjs if a.status == adj_status]
    if control_area:
        adjs = [a for a in adjs if a.control_area == control_area]
    return {
        "count": len(adjs),
        "adjustments": [a.dict() for a in adjs],
    }


@app.post("/v1/adjustments/{adj_id}/approve")
async def approve_adjustment(adj_id: str, reviewer: str = Query("compliance-officer")):
    if adj_id not in ADJUSTMENTS:
        raise HTTPException(404, "Adjustment not found")
    adj = ADJUSTMENTS[adj_id]
    if adj.status not in (AdjustmentStatus.PROPOSED, AdjustmentStatus.PENDING_REVIEW):
        raise HTTPException(409, f"Cannot approve adjustment in status '{adj.status.value}'")

    adj.status = AdjustmentStatus.APPROVED
    adj.reviewed_by = reviewer
    adj.reviewed_at = _now().isoformat()

    _audit("adjustment_approved", adj.id, reviewer=reviewer, control=adj.control_area)

    return {
        "id": adj.id,
        "status": adj.status.value,
        "reviewed_by": reviewer,
        "policy_change": adj.policy_change,
    }


@app.post("/v1/adjustments/{adj_id}/reject")
async def reject_adjustment(adj_id: str, reviewer: str = Query("compliance-officer"), reason: str = ""):
    if adj_id not in ADJUSTMENTS:
        raise HTTPException(404, "Adjustment not found")
    adj = ADJUSTMENTS[adj_id]

    adj.status = AdjustmentStatus.REJECTED
    adj.reviewed_by = reviewer
    adj.reviewed_at = _now().isoformat()

    _audit("adjustment_rejected", adj.id, reviewer=reviewer, reason=reason)

    return {"id": adj.id, "status": adj.status.value, "reviewed_by": reviewer}


# ---- Posture Dashboard ----------------------------------------------------

@app.get("/v1/posture")
async def compliance_posture():
    """Overall compliance posture across all jurisdictions."""
    posture_by_jurisdiction: dict[str, dict[str, Any]] = {}

    for code in JURISDICTIONS:
        regs = [r for r in REGULATIONS.values() if r.jurisdiction == code]
        if not regs:
            continue

        total_reqs = sum(len(r.requirements) for r in regs)
        # Find relevant gap analyses
        gaps = []
        for analysis in GAP_ANALYSES.values():
            if analysis.jurisdiction == code or analysis.jurisdiction == "ALL":
                for g in analysis.gaps:
                    if REGULATIONS.get(g.regulation_id, Regulation(name="", jurisdiction="")).jurisdiction == code:
                        gaps.append(g)

        open_gaps = [g for g in gaps if g.status == "open"]
        avg_impact = round(statistics.mean(g.impact_score for g in open_gaps), 2) if open_gaps else 0.0

        posture_by_jurisdiction[code] = {
            "jurisdiction": JURISDICTIONS[code],
            "regulations": len(regs),
            "total_requirements": total_reqs,
            "open_gaps": len(open_gaps),
            "avg_gap_impact": avg_impact,
            "posture_score": round(max(0, 100 - len(open_gaps) * avg_impact), 2),
        }

    # Overall
    all_scores = [v["posture_score"] for v in posture_by_jurisdiction.values()]
    overall = round(statistics.mean(all_scores), 2) if all_scores else 0.0

    return {
        "overall_posture": overall,
        "jurisdictions": posture_by_jurisdiction,
        "total_open_gaps": sum(v["open_gaps"] for v in posture_by_jurisdiction.values()),
        "pending_adjustments": sum(1 for a in ADJUSTMENTS.values() if a.status == AdjustmentStatus.PROPOSED),
    }


# ---- Audit ----------------------------------------------------------------

@app.get("/v1/audit")
async def audit_trail(
    operation: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    entries = AUDIT_LOG[:]
    if operation:
        entries = [e for e in entries if e.operation == operation]
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return {"count": len(entries[:limit]), "entries": [e.dict() for e in entries[:limit]]}


# ---- Analytics ------------------------------------------------------------

@app.get("/v1/analytics")
async def compliance_analytics():
    regs = list(REGULATIONS.values())
    all_gaps: list[GapItem] = []
    for analysis in GAP_ANALYSES.values():
        all_gaps.extend(analysis.gaps)

    by_jurisdiction = Counter(r.jurisdiction for r in regs)
    by_risk_class = Counter(r.ai_risk_class.value for r in regs)
    by_gap_severity = Counter(g.severity.value for g in all_gaps)
    by_control_area = Counter(g.control_area for g in all_gaps)
    by_adj_status = Counter(a.status.value for a in ADJUSTMENTS.values())

    total_reqs = sum(len(r.requirements) for r in regs)
    avg_req_per_reg = round(total_reqs / len(regs), 1) if regs else 0

    fw_coverage = Counter()
    for r in regs:
        for fw in r.frameworks_mapped:
            fw_coverage[fw] += 1

    return {
        "total_regulations": len(regs),
        "total_jurisdictions": len(by_jurisdiction),
        "by_jurisdiction": dict(by_jurisdiction),
        "by_risk_class": dict(by_risk_class),
        "total_requirements": total_reqs,
        "avg_requirements_per_regulation": avg_req_per_reg,
        "framework_coverage": dict(fw_coverage),
        "total_gaps": len(all_gaps),
        "by_gap_severity": dict(by_gap_severity),
        "by_control_area": dict(by_control_area),
        "total_adjustments": len(ADJUSTMENTS),
        "by_adjustment_status": dict(by_adj_status),
        "audit_entries": len(AUDIT_LOG),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8903)
