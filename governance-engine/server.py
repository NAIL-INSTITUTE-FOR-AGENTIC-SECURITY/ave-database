"""
Autonomous Governance Engine — Core governance server.

AI-assisted policy engine that dynamically adjusts organisational AI
governance based on threat landscape, compliance requirements, and
risk tolerance.  Every policy change is auditable with justification,
trigger, and rollback path.
"""

from __future__ import annotations

import copy
import math
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
    title="NAIL Autonomous Governance Engine",
    description=(
        "AI-assisted policy engine for dynamic AI governance "
        "based on threats, compliance, and risk tolerance."
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

AVE_CATEGORIES = [
    "prompt_injection", "tool_misuse", "memory_poisoning", "goal_hijacking",
    "identity_spoofing", "privilege_escalation", "data_exfiltration",
    "resource_exhaustion", "multi_agent_manipulation", "context_overflow",
    "guardrail_bypass", "output_manipulation", "supply_chain_compromise",
    "model_extraction", "reward_hacking", "capability_elicitation",
    "alignment_subversion", "delegation_abuse",
]

REGULATORY_FRAMEWORKS = {
    "nist_ai_rmf": "NIST AI Risk Management Framework",
    "eu_ai_act": "EU AI Act",
    "iso_42001": "ISO/IEC 42001",
    "owasp_llm": "OWASP LLM Top 10",
}

GOVERNANCE_DOMAINS = [
    "data_privacy",
    "model_safety",
    "tool_security",
    "agent_autonomy",
    "human_oversight",
    "transparency",
    "accountability",
    "fairness",
    "robustness",
    "incident_response",
]

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class EnforcementLevel(str, Enum):
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"
    EMERGENCY = "emergency"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class AdjustmentAction(str, Enum):
    TIGHTEN = "tighten"
    RELAX = "relax"
    ESCALATE = "escalate"
    SUSPEND = "suspend"
    RESTORE = "restore"
    NO_CHANGE = "no_change"


class DecisionStatus(str, Enum):
    APPLIED = "applied"
    PENDING_REVIEW = "pending_review"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class PolicyCondition(BaseModel):
    """When this condition is true the policy action is triggered."""
    domain: str
    metric: str  # e.g. "threat_count", "compliance_score", "risk_score"
    operator: str  # gt, gte, lt, lte, eq
    threshold: float


class PolicyAction(BaseModel):
    action: AdjustmentAction
    target_domain: str
    parameter: str
    value: Any


class GovernancePolicy(BaseModel):
    id: str = Field(default_factory=lambda: f"GOV-{uuid.uuid4().hex[:8].upper()}")
    name: str
    description: str = ""
    domain: str
    enforcement: EnforcementLevel = EnforcementLevel.RECOMMENDED
    status: PolicyStatus = PolicyStatus.ACTIVE
    conditions: list[PolicyCondition] = Field(default_factory=list)
    actions: list[PolicyAction] = Field(default_factory=list)
    regulatory_refs: list[str] = Field(default_factory=list)  # e.g. ["nist_ai_rmf", "eu_ai_act"]
    ave_categories: list[str] = Field(default_factory=list)
    version: int = 1
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PolicyCreate(BaseModel):
    name: str
    description: str = ""
    domain: str
    enforcement: EnforcementLevel = EnforcementLevel.RECOMMENDED
    conditions: list[PolicyCondition] = Field(default_factory=list)
    actions: list[PolicyAction] = Field(default_factory=list)
    regulatory_refs: list[str] = Field(default_factory=list)
    ave_categories: list[str] = Field(default_factory=list)


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enforcement: Optional[EnforcementLevel] = None
    status: Optional[PolicyStatus] = None
    conditions: Optional[list[PolicyCondition]] = None
    actions: Optional[list[PolicyAction]] = None


class RiskAppetite(BaseModel):
    domain: str
    current_risk: RiskLevel = RiskLevel.MEDIUM
    max_acceptable: RiskLevel = RiskLevel.HIGH
    floor: float = 0.0  # minimum tolerance 0-1
    ceiling: float = 1.0  # maximum tolerance 0-1
    auto_adjust: bool = True


class RiskAppetiteProfile(BaseModel):
    id: str = Field(default_factory=lambda: f"RAP-{uuid.uuid4().hex[:8].upper()}")
    org_name: str = "Default Organisation"
    industry: str = "technology"
    jurisdiction: str = "global"
    appetites: list[RiskAppetite] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RiskAppetiteCreate(BaseModel):
    org_name: str = "Default Organisation"
    industry: str = "technology"
    jurisdiction: str = "global"
    appetites: list[RiskAppetite] = Field(default_factory=list)


class ThreatSignal(BaseModel):
    category: str
    severity: str  # critical, high, medium, low
    source: str = "external"
    description: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class GovernanceDecision(BaseModel):
    id: str = Field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:8].upper()}")
    policy_id: str
    policy_name: str
    action: AdjustmentAction
    domain: str
    trigger: str  # what caused this decision
    justification: str
    previous_state: dict[str, Any] = Field(default_factory=dict)
    new_state: dict[str, Any] = Field(default_factory=dict)
    status: DecisionStatus = DecisionStatus.APPLIED
    requires_review: bool = False
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EvaluationResult(BaseModel):
    overall_risk: RiskLevel
    domain_risks: dict[str, RiskLevel]
    compliance_gaps: list[dict[str, Any]]
    recommended_adjustments: list[dict[str, Any]]
    decisions_made: list[GovernanceDecision]
    threat_context: dict[str, Any]
    timestamp: str


class SimulationResult(BaseModel):
    scenario: str
    current_state: dict[str, Any]
    projected_state: dict[str, Any]
    risk_delta: dict[str, float]
    compliance_impact: dict[str, Any]
    recommendation: str


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → PostgreSQL + Redis)
# ---------------------------------------------------------------------------

POLICIES: dict[str, GovernancePolicy] = {}
RISK_PROFILE: Optional[RiskAppetiteProfile] = None
DECISIONS: dict[str, GovernanceDecision] = {}
THREAT_SIGNALS: list[ThreatSignal] = []
DOMAIN_METRICS: dict[str, dict[str, float]] = defaultdict(
    lambda: {"threat_count": 0, "compliance_score": 0.8, "risk_score": 0.3}
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731

RISK_NUMERIC: dict[str, float] = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
    "minimal": 0.1,
}

RISK_FROM_SCORE: list[tuple[float, RiskLevel]] = [
    (0.8, RiskLevel.CRITICAL),
    (0.6, RiskLevel.HIGH),
    (0.4, RiskLevel.MEDIUM),
    (0.2, RiskLevel.LOW),
    (0.0, RiskLevel.MINIMAL),
]


def _score_to_risk(score: float) -> RiskLevel:
    for threshold, level in RISK_FROM_SCORE:
        if score >= threshold:
            return level
    return RiskLevel.MINIMAL


def _evaluate_condition(cond: PolicyCondition, metrics: dict[str, float]) -> bool:
    val = metrics.get(cond.metric, 0.0)
    ops = {
        "gt": val > cond.threshold,
        "gte": val >= cond.threshold,
        "lt": val < cond.threshold,
        "lte": val <= cond.threshold,
        "eq": abs(val - cond.threshold) < 0.001,
    }
    return ops.get(cond.operator, False)


def _apply_adjustment(
    policy: GovernancePolicy,
    action: PolicyAction,
    trigger: str,
) -> GovernanceDecision:
    """Apply a policy action and return a decision record."""
    prev = copy.deepcopy(dict(DOMAIN_METRICS[action.target_domain]))

    # Simulate the adjustment
    if action.action == AdjustmentAction.TIGHTEN:
        DOMAIN_METRICS[action.target_domain]["risk_score"] = max(
            0.0,
            DOMAIN_METRICS[action.target_domain].get("risk_score", 0.5) - 0.1,
        )
    elif action.action == AdjustmentAction.RELAX:
        DOMAIN_METRICS[action.target_domain]["risk_score"] = min(
            1.0,
            DOMAIN_METRICS[action.target_domain].get("risk_score", 0.5) + 0.05,
        )
    elif action.action == AdjustmentAction.ESCALATE:
        pass  # Escalation is a workflow trigger, not a metric change
    elif action.action == AdjustmentAction.SUSPEND:
        DOMAIN_METRICS[action.target_domain]["risk_score"] = 0.0

    new = dict(DOMAIN_METRICS[action.target_domain])

    # Check if risk appetite exceeded → require human review
    requires_review = False
    if RISK_PROFILE:
        for appetite in RISK_PROFILE.appetites:
            if appetite.domain == action.target_domain:
                max_val = RISK_NUMERIC.get(appetite.max_acceptable.value, 0.75)
                if new.get("risk_score", 0) > max_val:
                    requires_review = True

    decision = GovernanceDecision(
        policy_id=policy.id,
        policy_name=policy.name,
        action=action.action,
        domain=action.target_domain,
        trigger=trigger,
        justification=f"Policy '{policy.name}' condition met: {trigger}. Action: {action.action.value} on {action.target_domain}.",
        previous_state=prev,
        new_state=new,
        status=DecisionStatus.PENDING_REVIEW if requires_review else DecisionStatus.APPLIED,
        requires_review=requires_review,
    )
    DECISIONS[decision.id] = decision
    return decision


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    global RISK_PROFILE

    # Default risk appetite
    appetites = [
        RiskAppetite(domain=d, current_risk=RiskLevel.MEDIUM, max_acceptable=RiskLevel.HIGH, floor=0.1, ceiling=0.8)
        for d in GOVERNANCE_DOMAINS
    ]
    RISK_PROFILE = RiskAppetiteProfile(
        org_name="NAIL Institute",
        industry="ai_security",
        jurisdiction="global",
        appetites=appetites,
    )

    # Domain metrics (simulated)
    for domain in GOVERNANCE_DOMAINS:
        DOMAIN_METRICS[domain] = {
            "threat_count": random.randint(0, 15),
            "compliance_score": round(random.uniform(0.5, 1.0), 2),
            "risk_score": round(random.uniform(0.1, 0.7), 2),
        }

    # Seed policies
    policies_data = [
        (
            "Prompt Injection Defence Mandate",
            "Requires active prompt injection defences when threat count exceeds threshold.",
            "model_safety",
            EnforcementLevel.MANDATORY,
            [PolicyCondition(domain="model_safety", metric="threat_count", operator="gte", threshold=5)],
            [PolicyAction(action=AdjustmentAction.TIGHTEN, target_domain="model_safety", parameter="defence_level", value="high")],
            ["nist_ai_rmf", "owasp_llm"],
            ["prompt_injection", "guardrail_bypass"],
        ),
        (
            "Data Exfiltration Prevention",
            "Enforces DLP when data privacy risk score exceeds ceiling.",
            "data_privacy",
            EnforcementLevel.MANDATORY,
            [PolicyCondition(domain="data_privacy", metric="risk_score", operator="gt", threshold=0.6)],
            [PolicyAction(action=AdjustmentAction.TIGHTEN, target_domain="data_privacy", parameter="dlp_level", value="strict")],
            ["eu_ai_act", "iso_42001"],
            ["data_exfiltration"],
        ),
        (
            "Tool Access Governance",
            "Restricts agent tool access when tool_security compliance drops.",
            "tool_security",
            EnforcementLevel.RECOMMENDED,
            [PolicyCondition(domain="tool_security", metric="compliance_score", operator="lt", threshold=0.7)],
            [PolicyAction(action=AdjustmentAction.TIGHTEN, target_domain="tool_security", parameter="tool_whitelist", value="restricted")],
            ["nist_ai_rmf"],
            ["tool_misuse", "privilege_escalation"],
        ),
        (
            "Human Oversight Escalation",
            "Escalates to human review when agent autonomy risk is high.",
            "human_oversight",
            EnforcementLevel.MANDATORY,
            [PolicyCondition(domain="agent_autonomy", metric="risk_score", operator="gte", threshold=0.7)],
            [PolicyAction(action=AdjustmentAction.ESCALATE, target_domain="agent_autonomy", parameter="approval_required", value=True)],
            ["eu_ai_act", "iso_42001"],
            ["goal_hijacking", "delegation_abuse"],
        ),
        (
            "Transparency Requirement",
            "Increases logging and explainability when transparency score is low.",
            "transparency",
            EnforcementLevel.RECOMMENDED,
            [PolicyCondition(domain="transparency", metric="compliance_score", operator="lt", threshold=0.6)],
            [PolicyAction(action=AdjustmentAction.TIGHTEN, target_domain="transparency", parameter="logging_level", value="verbose")],
            ["eu_ai_act", "nist_ai_rmf", "iso_42001"],
            [],
        ),
        (
            "Incident Response Readiness",
            "Activates emergency protocol when active threats spike.",
            "incident_response",
            EnforcementLevel.EMERGENCY,
            [PolicyCondition(domain="incident_response", metric="threat_count", operator="gte", threshold=10)],
            [
                PolicyAction(action=AdjustmentAction.TIGHTEN, target_domain="incident_response", parameter="alert_level", value="red"),
                PolicyAction(action=AdjustmentAction.ESCALATE, target_domain="incident_response", parameter="soc_notify", value=True),
            ],
            ["nist_ai_rmf"],
            ["multi_agent_manipulation", "alignment_subversion"],
        ),
        (
            "Fairness & Bias Monitoring",
            "Flags potential bias when fairness compliance dips.",
            "fairness",
            EnforcementLevel.RECOMMENDED,
            [PolicyCondition(domain="fairness", metric="compliance_score", operator="lt", threshold=0.75)],
            [PolicyAction(action=AdjustmentAction.TIGHTEN, target_domain="fairness", parameter="bias_scan", value="enabled")],
            ["eu_ai_act", "iso_42001"],
            [],
        ),
        (
            "Robustness Assurance",
            "Strengthens input validation when robustness risk is elevated.",
            "robustness",
            EnforcementLevel.RECOMMENDED,
            [PolicyCondition(domain="robustness", metric="risk_score", operator="gt", threshold=0.5)],
            [PolicyAction(action=AdjustmentAction.TIGHTEN, target_domain="robustness", parameter="validation_mode", value="strict")],
            ["nist_ai_rmf", "owasp_llm"],
            ["context_overflow", "resource_exhaustion"],
        ),
    ]

    for name, desc, domain, enforce, conds, actions, regs, cats in policies_data:
        p = GovernancePolicy(
            name=name,
            description=desc,
            domain=domain,
            enforcement=enforce,
            conditions=conds,
            actions=actions,
            regulatory_refs=regs,
            ave_categories=cats,
        )
        POLICIES[p.id] = p

    # Seed some threat signals
    for cat in random.sample(AVE_CATEGORIES, 8):
        sig = ThreatSignal(
            category=cat,
            severity=random.choice(["critical", "high", "medium", "low"]),
            source="live_feed",
            description=f"Observed {cat} activity",
            timestamp=(_now() - timedelta(hours=random.randint(0, 48))).isoformat(),
        )
        THREAT_SIGNALS.append(sig)


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "autonomous-governance-engine",
        "version": "1.0.0",
        "policies": len(POLICIES),
        "decisions": len(DECISIONS),
        "domains": len(GOVERNANCE_DOMAINS),
    }


# ---- Policies ------------------------------------------------------------

@app.post("/v1/policies", status_code=status.HTTP_201_CREATED)
async def create_policy(data: PolicyCreate):
    if data.domain not in GOVERNANCE_DOMAINS:
        raise HTTPException(400, f"Invalid domain. Must be one of: {GOVERNANCE_DOMAINS}")
    for ref in data.regulatory_refs:
        if ref not in REGULATORY_FRAMEWORKS:
            raise HTTPException(400, f"Unknown regulatory framework: {ref}")
    for cat in data.ave_categories:
        if cat not in AVE_CATEGORIES:
            raise HTTPException(400, f"Unknown AVE category: {cat}")

    policy = GovernancePolicy(
        name=data.name,
        description=data.description,
        domain=data.domain,
        enforcement=data.enforcement,
        conditions=data.conditions,
        actions=data.actions,
        regulatory_refs=data.regulatory_refs,
        ave_categories=data.ave_categories,
    )
    POLICIES[policy.id] = policy
    return {"id": policy.id, "name": policy.name, "status": policy.status.value}


@app.get("/v1/policies")
async def list_policies(
    domain: Optional[str] = None,
    status_filter: Optional[PolicyStatus] = Query(None, alias="status"),
    enforcement: Optional[EnforcementLevel] = None,
):
    policies = list(POLICIES.values())
    if domain:
        policies = [p for p in policies if p.domain == domain]
    if status_filter:
        policies = [p for p in policies if p.status == status_filter]
    if enforcement:
        policies = [p for p in policies if p.enforcement == enforcement]
    return {"count": len(policies), "policies": [p.dict() for p in policies]}


@app.get("/v1/policies/{policy_id}")
async def get_policy(policy_id: str):
    if policy_id not in POLICIES:
        raise HTTPException(404, "Policy not found")
    return POLICIES[policy_id].dict()


@app.patch("/v1/policies/{policy_id}")
async def update_policy(policy_id: str, data: PolicyUpdate):
    if policy_id not in POLICIES:
        raise HTTPException(404, "Policy not found")
    policy = POLICIES[policy_id]

    if data.name is not None:
        policy.name = data.name
    if data.description is not None:
        policy.description = data.description
    if data.enforcement is not None:
        policy.enforcement = data.enforcement
    if data.status is not None:
        policy.status = data.status
    if data.conditions is not None:
        policy.conditions = data.conditions
    if data.actions is not None:
        policy.actions = data.actions

    policy.version += 1
    policy.updated_at = _now().isoformat()
    return {"id": policy_id, "version": policy.version, "status": policy.status.value}


@app.delete("/v1/policies/{policy_id}")
async def archive_policy(policy_id: str):
    if policy_id not in POLICIES:
        raise HTTPException(404, "Policy not found")
    POLICIES[policy_id].status = PolicyStatus.ARCHIVED
    POLICIES[policy_id].updated_at = _now().isoformat()
    return {"archived": policy_id}


# ---- Risk Appetite -------------------------------------------------------

@app.post("/v1/risk-appetite", status_code=status.HTTP_201_CREATED)
async def set_risk_appetite(data: RiskAppetiteCreate):
    global RISK_PROFILE
    for a in data.appetites:
        if a.domain not in GOVERNANCE_DOMAINS:
            raise HTTPException(400, f"Invalid domain: {a.domain}")

    RISK_PROFILE = RiskAppetiteProfile(
        org_name=data.org_name,
        industry=data.industry,
        jurisdiction=data.jurisdiction,
        appetites=data.appetites,
    )
    return {"id": RISK_PROFILE.id, "domains": len(RISK_PROFILE.appetites)}


@app.get("/v1/risk-appetite")
async def get_risk_appetite():
    if not RISK_PROFILE:
        raise HTTPException(404, "No risk appetite profile configured")
    return RISK_PROFILE.dict()


# ---- Evaluate (core governance loop) ------------------------------------

@app.post("/v1/evaluate")
async def evaluate_governance():
    """Run the governance evaluation loop across all active policies."""
    decisions_made: list[GovernanceDecision] = []

    # Update domain threat counts from recent signals
    for domain in GOVERNANCE_DOMAINS:
        category_threats = sum(
            1 for s in THREAT_SIGNALS
            if s.timestamp >= (_now() - timedelta(hours=24)).isoformat()
        )
        DOMAIN_METRICS[domain]["threat_count"] = category_threats

    # Evaluate each active policy
    for policy in POLICIES.values():
        if policy.status != PolicyStatus.ACTIVE:
            continue

        metrics = dict(DOMAIN_METRICS.get(policy.domain, {}))
        conditions_met = all(
            _evaluate_condition(c, metrics) for c in policy.conditions
        ) if policy.conditions else False

        if conditions_met:
            for action in policy.actions:
                trigger = f"conditions_met: {[f'{c.metric} {c.operator} {c.threshold}' for c in policy.conditions]}"
                dec = _apply_adjustment(policy, action, trigger)
                decisions_made.append(dec)

    # Compute domain risk levels
    domain_risks: dict[str, RiskLevel] = {}
    for domain in GOVERNANCE_DOMAINS:
        score = DOMAIN_METRICS[domain].get("risk_score", 0.5)
        domain_risks[domain] = _score_to_risk(score)

    # Overall risk: worst domain
    risk_scores = [
        DOMAIN_METRICS[d].get("risk_score", 0.5) for d in GOVERNANCE_DOMAINS
    ]
    overall_risk = _score_to_risk(max(risk_scores) if risk_scores else 0.5)

    # Compliance gaps
    compliance_gaps: list[dict[str, Any]] = []
    for domain in GOVERNANCE_DOMAINS:
        cscore = DOMAIN_METRICS[domain].get("compliance_score", 1.0)
        if cscore < 0.7:
            compliance_gaps.append({
                "domain": domain,
                "compliance_score": cscore,
                "gap": round(0.7 - cscore, 2),
                "recommendation": f"Increase compliance investment in {domain}",
            })

    # Recommended adjustments
    recommended: list[dict[str, Any]] = []
    for domain in GOVERNANCE_DOMAINS:
        rscore = DOMAIN_METRICS[domain].get("risk_score", 0.5)
        if RISK_PROFILE:
            appetite = next(
                (a for a in RISK_PROFILE.appetites if a.domain == domain), None
            )
            if appetite:
                max_val = RISK_NUMERIC.get(appetite.max_acceptable.value, 0.75)
                if rscore > max_val:
                    recommended.append({
                        "domain": domain,
                        "current_risk": rscore,
                        "max_acceptable": max_val,
                        "action": "tighten",
                        "urgency": "high" if rscore > 0.8 else "medium",
                    })

    # Threat context
    sev_counts = Counter(s.severity for s in THREAT_SIGNALS)
    cat_counts = Counter(s.category for s in THREAT_SIGNALS)

    result = EvaluationResult(
        overall_risk=overall_risk,
        domain_risks={d: r.value for d, r in domain_risks.items()},
        compliance_gaps=compliance_gaps,
        recommended_adjustments=recommended,
        decisions_made=decisions_made,
        threat_context={
            "total_signals": len(THREAT_SIGNALS),
            "by_severity": dict(sev_counts),
            "by_category": dict(cat_counts.most_common(5)),
        },
        timestamp=_now().isoformat(),
    )
    return result


# ---- Simulate ------------------------------------------------------------

@app.post("/v1/simulate")
async def simulate_change(
    domain: str = Query(...),
    action: AdjustmentAction = Query(...),
    magnitude: float = Query(0.1, ge=0.01, le=0.5),
):
    if domain not in GOVERNANCE_DOMAINS:
        raise HTTPException(400, f"Invalid domain. Must be one of: {GOVERNANCE_DOMAINS}")

    current = dict(DOMAIN_METRICS.get(domain, {"risk_score": 0.5, "compliance_score": 0.8, "threat_count": 0}))
    projected = copy.deepcopy(current)

    if action == AdjustmentAction.TIGHTEN:
        projected["risk_score"] = max(0.0, current.get("risk_score", 0.5) - magnitude)
        projected["compliance_score"] = min(1.0, current.get("compliance_score", 0.8) + magnitude * 0.5)
    elif action == AdjustmentAction.RELAX:
        projected["risk_score"] = min(1.0, current.get("risk_score", 0.5) + magnitude)
        projected["compliance_score"] = max(0.0, current.get("compliance_score", 0.8) - magnitude * 0.3)
    elif action == AdjustmentAction.SUSPEND:
        projected["risk_score"] = 0.0
        projected["compliance_score"] = current.get("compliance_score", 0.8)

    risk_delta = {
        k: round(projected.get(k, 0) - current.get(k, 0), 4)
        for k in ["risk_score", "compliance_score", "threat_count"]
    }

    # Compliance impact
    compliance_impact: dict[str, Any] = {}
    for ref, name in REGULATORY_FRAMEWORKS.items():
        relevant = [
            p for p in POLICIES.values()
            if ref in p.regulatory_refs and p.domain == domain
        ]
        compliance_impact[ref] = {
            "name": name,
            "affected_policies": len(relevant),
            "projected_compliance": round(projected.get("compliance_score", 0.8), 2),
        }

    recommendation = "proceed" if projected.get("risk_score", 0.5) < 0.7 else "review_required"

    return SimulationResult(
        scenario=f"{action.value} {domain} by {magnitude}",
        current_state=current,
        projected_state=projected,
        risk_delta=risk_delta,
        compliance_impact=compliance_impact,
        recommendation=recommendation,
    )


# ---- Threat Ingestion ----------------------------------------------------

@app.post("/v1/threats/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_threat_signal(signal: ThreatSignal):
    if signal.category not in AVE_CATEGORIES:
        raise HTTPException(400, f"Invalid category: {signal.category}")
    THREAT_SIGNALS.append(signal)

    # Update relevant domain metrics
    sev_weight = {"critical": 2, "high": 1.5, "medium": 1, "low": 0.5}.get(signal.severity, 0.5)
    for domain in GOVERNANCE_DOMAINS:
        DOMAIN_METRICS[domain]["threat_count"] = DOMAIN_METRICS[domain].get("threat_count", 0) + 1
        DOMAIN_METRICS[domain]["risk_score"] = min(
            1.0,
            DOMAIN_METRICS[domain].get("risk_score", 0.5) + sev_weight * 0.02,
        )

    return {"ingested": True, "total_signals": len(THREAT_SIGNALS)}


# ---- Decisions -----------------------------------------------------------

@app.get("/v1/decisions")
async def list_decisions(
    status_filter: Optional[DecisionStatus] = Query(None, alias="status"),
    domain: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    decs = list(DECISIONS.values())
    if status_filter:
        decs = [d for d in decs if d.status == status_filter]
    if domain:
        decs = [d for d in decs if d.domain == domain]
    decs.sort(key=lambda d: d.timestamp, reverse=True)
    return {"count": len(decs[:limit]), "decisions": [d.dict() for d in decs[:limit]]}


@app.get("/v1/decisions/{dec_id}")
async def get_decision(dec_id: str):
    if dec_id not in DECISIONS:
        raise HTTPException(404, "Decision not found")
    return DECISIONS[dec_id].dict()


@app.post("/v1/decisions/{dec_id}/rollback")
async def rollback_decision(dec_id: str):
    if dec_id not in DECISIONS:
        raise HTTPException(404, "Decision not found")
    dec = DECISIONS[dec_id]
    if dec.status == DecisionStatus.ROLLED_BACK:
        return {"message": "Already rolled back", "decision_id": dec_id}

    # Restore previous state
    if dec.previous_state:
        DOMAIN_METRICS[dec.domain] = defaultdict(float, dec.previous_state)

    dec.status = DecisionStatus.ROLLED_BACK
    return {
        "rolled_back": True,
        "decision_id": dec_id,
        "domain": dec.domain,
        "restored_state": dec.previous_state,
    }


# ---- Compliance Map ------------------------------------------------------

@app.get("/v1/compliance-map")
async def compliance_map():
    mapping: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ref, name in REGULATORY_FRAMEWORKS.items():
        relevant = [
            p for p in POLICIES.values()
            if ref in p.regulatory_refs and p.status == PolicyStatus.ACTIVE
        ]
        for p in relevant:
            mapping[ref].append({
                "policy_id": p.id,
                "policy_name": p.name,
                "domain": p.domain,
                "enforcement": p.enforcement.value,
                "ave_categories": p.ave_categories,
            })

    return {
        "frameworks": {
            ref: {
                "name": name,
                "policy_count": len(mapping.get(ref, [])),
                "policies": mapping.get(ref, []),
            }
            for ref, name in REGULATORY_FRAMEWORKS.items()
        }
    }


# ---- Analytics -----------------------------------------------------------

@app.get("/v1/analytics")
async def governance_analytics():
    policies = list(POLICIES.values())
    by_domain = Counter(p.domain for p in policies)
    by_enforcement = Counter(p.enforcement.value for p in policies)
    by_status = Counter(p.status.value for p in policies)

    decisions = list(DECISIONS.values())
    by_action = Counter(d.action.value for d in decisions)
    by_dec_status = Counter(d.status.value for d in decisions)

    # Domain risk summary
    domain_summary: dict[str, dict[str, Any]] = {}
    for domain in GOVERNANCE_DOMAINS:
        m = DOMAIN_METRICS.get(domain, {})
        domain_summary[domain] = {
            "risk_score": round(m.get("risk_score", 0.5), 4),
            "compliance_score": round(m.get("compliance_score", 0.8), 4),
            "threat_count": m.get("threat_count", 0),
            "risk_level": _score_to_risk(m.get("risk_score", 0.5)).value,
        }

    return {
        "total_policies": len(policies),
        "active_policies": sum(1 for p in policies if p.status == PolicyStatus.ACTIVE),
        "by_domain": dict(by_domain),
        "by_enforcement": dict(by_enforcement),
        "by_status": dict(by_status),
        "total_decisions": len(decisions),
        "by_action": dict(by_action),
        "by_decision_status": dict(by_dec_status),
        "pending_review": sum(1 for d in decisions if d.status == DecisionStatus.PENDING_REVIEW),
        "domain_summary": domain_summary,
        "total_threat_signals": len(THREAT_SIGNALS),
        "risk_appetite_configured": RISK_PROFILE is not None,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8704)
