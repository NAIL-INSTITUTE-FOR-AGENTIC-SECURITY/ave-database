"""
AVE Vulnerability Marketplace — Core marketplace server.

Bounty platform for responsible disclosure of novel agentic AI
vulnerabilities with reward tiers, multi-stage verification pipeline,
researcher reputation tracking, and coordinated disclosure management.
"""

from __future__ import annotations

import hashlib
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
    title="NAIL AVE Vulnerability Marketplace",
    description=(
        "Bounty platform for responsible disclosure of novel agentic AI "
        "vulnerabilities with reward tiers and verification pipeline."
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
    "prompt_injection",
    "tool_misuse",
    "memory_poisoning",
    "goal_hijacking",
    "identity_spoofing",
    "privilege_escalation",
    "data_exfiltration",
    "resource_exhaustion",
    "multi_agent_manipulation",
    "context_overflow",
    "guardrail_bypass",
    "output_manipulation",
    "supply_chain_compromise",
    "model_extraction",
    "reward_hacking",
    "capability_elicitation",
    "alignment_subversion",
    "delegation_abuse",
]

EMBARGO_DAYS = 90

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SubmissionStatus(str, Enum):
    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    REPRODUCING = "reproducing"
    VALIDATED = "validated"
    SCORED = "scored"
    REWARDED = "rewarded"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    DISCLOSED = "disclosed"


class BountyTier(str, Enum):
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"


class ProgrammeScope(str, Enum):
    GENERAL = "general"
    FRAMEWORK_SPECIFIC = "framework_specific"
    CATEGORY_SPECIFIC = "category_specific"
    CTF = "ctf"
    RESEARCH = "research"


class VerificationStage(str, Enum):
    TRIAGE = "triage"
    REPRODUCE = "reproduce"
    VALIDATE = "validate"
    SCORE = "score"
    REWARD = "reward"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class VulnSubmission(BaseModel):
    id: str = Field(default_factory=lambda: f"MKTPL-{uuid.uuid4().hex[:8].upper()}")
    title: str
    description: str
    category: str
    researcher_id: str
    avss_score: Optional[float] = None
    severity: Optional[str] = None
    affected_frameworks: list[str] = Field(default_factory=list)
    proof_of_concept: Optional[str] = None
    defence_recommendation: Optional[str] = None
    real_world_evidence: bool = False
    status: SubmissionStatus = SubmissionStatus.SUBMITTED
    bounty_tier: Optional[BountyTier] = None
    bounty_amount_usd: Optional[float] = None
    verification_stage: VerificationStage = VerificationStage.TRIAGE
    verification_notes: list[dict[str, Any]] = Field(default_factory=list)
    embargo_start: Optional[str] = None
    embargo_end: Optional[str] = None
    disclosed: bool = False
    submitted_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    content_hash: str = ""


class SubmissionCreate(BaseModel):
    title: str
    description: str
    category: str
    researcher_id: str
    affected_frameworks: list[str] = Field(default_factory=list)
    proof_of_concept: Optional[str] = None
    defence_recommendation: Optional[str] = None
    real_world_evidence: bool = False


class StatusUpdate(BaseModel):
    status: SubmissionStatus
    note: Optional[str] = None


class Researcher(BaseModel):
    id: str = Field(default_factory=lambda: f"RES-{uuid.uuid4().hex[:8].upper()}")
    handle: str
    email: str = ""
    bio: str = ""
    joined_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    submissions_count: int = 0
    validated_count: int = 0
    total_earned_usd: float = 0.0
    accuracy_rating: float = 1.0  # validated / (validated + rejected)
    reputation_tier: str = "newcomer"  # newcomer → contributor → expert → elite
    specialties: list[str] = Field(default_factory=list)


class ResearcherCreate(BaseModel):
    handle: str
    email: str = ""
    bio: str = ""
    specialties: list[str] = Field(default_factory=list)


class BountyProgramme(BaseModel):
    id: str = Field(default_factory=lambda: f"PROG-{uuid.uuid4().hex[:8].upper()}")
    name: str
    scope: ProgrammeScope
    description: str
    categories_in_scope: list[str] = Field(default_factory=list)
    frameworks_in_scope: list[str] = Field(default_factory=list)
    max_reward_usd: float = 30000.0
    active: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_paid_usd: float = 0.0
    submissions_received: int = 0


class ProgrammeCreate(BaseModel):
    name: str
    scope: ProgrammeScope
    description: str
    categories_in_scope: list[str] = Field(default_factory=list)
    frameworks_in_scope: list[str] = Field(default_factory=list)
    max_reward_usd: float = 30000.0


class BountyCalculation(BaseModel):
    avss_score: float
    tier: BountyTier
    base_reward_usd: float
    multipliers: dict[str, float]
    total_multiplier: float
    final_reward_usd: float


class DiscloseTimeline(BaseModel):
    submission_id: str
    events: list[dict[str, Any]]
    embargo_start: Optional[str]
    embargo_end: Optional[str]
    days_remaining: Optional[int]
    disclosed: bool


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → PostgreSQL)
# ---------------------------------------------------------------------------

SUBMISSIONS: dict[str, VulnSubmission] = {}
RESEARCHERS: dict[str, Researcher] = {}
PROGRAMMES: dict[str, BountyProgramme] = {}
BOUNTY_PAYOUTS: list[dict[str, Any]] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


def _content_hash(title: str, description: str) -> str:
    raw = f"{title.strip().lower()}|{description.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _classify_severity(avss: float) -> tuple[str, BountyTier]:
    if avss >= 9.0:
        return "critical", BountyTier.PLATINUM
    elif avss >= 7.0:
        return "high", BountyTier.GOLD
    elif avss >= 4.0:
        return "medium", BountyTier.SILVER
    else:
        return "low", BountyTier.BRONZE


BASE_REWARDS: dict[BountyTier, float] = {
    BountyTier.PLATINUM: 10_000.0,
    BountyTier.GOLD: 5_000.0,
    BountyTier.SILVER: 2_000.0,
    BountyTier.BRONZE: 500.0,
}

MAX_MULTIPLIERS: dict[BountyTier, float] = {
    BountyTier.PLATINUM: 3.0,
    BountyTier.GOLD: 2.0,
    BountyTier.SILVER: 1.5,
    BountyTier.BRONZE: 1.0,
}


def _calculate_bounty(
    avss_score: float,
    is_novel_category: bool = False,
    has_poc: bool = False,
    has_defence: bool = False,
    multi_framework: bool = False,
    real_world: bool = False,
) -> BountyCalculation:
    severity, tier = _classify_severity(avss_score)
    base = BASE_REWARDS[tier]
    multipliers: dict[str, float] = {}
    total = 1.0

    if is_novel_category:
        multipliers["novel_category"] = 2.0
        total *= 2.0
    if has_poc:
        multipliers["proof_of_concept"] = 1.5
        total *= 1.5
    if has_defence:
        multipliers["defence_recommendation"] = 1.25
        total *= 1.25
    if multi_framework:
        multipliers["multi_framework"] = 1.5
        total *= 1.5
    if real_world:
        multipliers["real_world_evidence"] = 1.75
        total *= 1.75

    # Cap multiplier
    total = min(total, MAX_MULTIPLIERS[tier])
    final = round(base * total, 2)

    return BountyCalculation(
        avss_score=avss_score,
        tier=tier,
        base_reward_usd=base,
        multipliers=multipliers,
        total_multiplier=round(total, 4),
        final_reward_usd=final,
    )


def _auto_score(sub: VulnSubmission) -> float:
    """Heuristic AVSS scoring based on category, frameworks, and evidence."""
    base = 5.0
    # Category weight
    high_sev = {"prompt_injection", "tool_misuse", "privilege_escalation",
                "data_exfiltration", "guardrail_bypass", "alignment_subversion"}
    if sub.category in high_sev:
        base += 2.0
    # Multi-framework
    if len(sub.affected_frameworks) >= 2:
        base += 1.0
    elif len(sub.affected_frameworks) >= 4:
        base += 2.0
    # Evidence
    if sub.proof_of_concept:
        base += 0.5
    if sub.real_world_evidence:
        base += 1.0
    if sub.defence_recommendation:
        base += 0.3
    return min(round(base + random.uniform(-0.5, 0.5), 1), 10.0)


def _update_researcher_stats(researcher_id: str) -> None:
    if researcher_id not in RESEARCHERS:
        return
    r = RESEARCHERS[researcher_id]
    subs = [s for s in SUBMISSIONS.values() if s.researcher_id == researcher_id]
    r.submissions_count = len(subs)
    r.validated_count = sum(
        1 for s in subs
        if s.status in (SubmissionStatus.VALIDATED, SubmissionStatus.SCORED,
                        SubmissionStatus.REWARDED, SubmissionStatus.DISCLOSED)
    )
    rejected = sum(1 for s in subs if s.status == SubmissionStatus.REJECTED)
    total_decided = r.validated_count + rejected
    r.accuracy_rating = round(r.validated_count / total_decided, 4) if total_decided else 1.0
    r.total_earned_usd = sum(
        s.bounty_amount_usd for s in subs if s.bounty_amount_usd
    )
    # Tier
    if r.validated_count >= 20 and r.accuracy_rating >= 0.9:
        r.reputation_tier = "elite"
    elif r.validated_count >= 10 and r.accuracy_rating >= 0.8:
        r.reputation_tier = "expert"
    elif r.validated_count >= 3:
        r.reputation_tier = "contributor"
    else:
        r.reputation_tier = "newcomer"


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    # Researchers
    researchers_data = [
        ("agent_hunter", "agent.hunter@example.com", "Specialises in prompt injection", ["prompt_injection", "guardrail_bypass"]),
        ("tool_breaker", "tool.breaker@example.com", "Framework security researcher", ["tool_misuse", "privilege_escalation"]),
        ("memory_ghost", "memory.ghost@example.com", "Memory and context attacks", ["memory_poisoning", "context_overflow"]),
    ]
    for handle, email, bio, specs in researchers_data:
        r = Researcher(handle=handle, email=email, bio=bio, specialties=specs)
        RESEARCHERS[r.id] = r

    # Default programme
    prog = BountyProgramme(
        name="NAIL General Bounty",
        scope=ProgrammeScope.GENERAL,
        description="Open bounty programme covering all AVE categories and frameworks.",
        categories_in_scope=AVE_CATEGORIES[:],
        max_reward_usd=30_000.0,
    )
    PROGRAMMES[prog.id] = prog

    fw_prog = BountyProgramme(
        name="LangChain Security Challenge",
        scope=ProgrammeScope.FRAMEWORK_SPECIFIC,
        description="Focused bounty for LangChain-specific agent vulnerabilities.",
        frameworks_in_scope=["LangChain"],
        categories_in_scope=["prompt_injection", "tool_misuse", "memory_poisoning"],
        max_reward_usd=15_000.0,
    )
    PROGRAMMES[fw_prog.id] = fw_prog

    # Sample submissions
    rids = list(RESEARCHERS.keys())
    sample_subs = [
        ("Cross-Agent Prompt Relay Attack", "Demonstrates chained prompt injection across LangChain multi-agent system.", "prompt_injection", rids[0], ["LangChain"], True, True, True, 8.7),
        ("Tool Schema Confusion in CrewAI", "Tool parameter injection via schema ambiguity.", "tool_misuse", rids[1], ["CrewAI"], True, False, False, 6.5),
        ("Persistent Memory Backdoor", "Shows memory poisoning surviving context window resets.", "memory_poisoning", rids[2], ["LangChain", "AutoGen"], True, True, False, 9.2),
    ]
    for title, desc, cat, rid, fw, poc, defence, rwe, avss in sample_subs:
        sub = VulnSubmission(
            title=title,
            description=desc,
            category=cat,
            researcher_id=rid,
            avss_score=avss,
            affected_frameworks=fw,
            proof_of_concept="PoC attached" if poc else None,
            defence_recommendation="Defence provided" if defence else None,
            real_world_evidence=rwe,
            content_hash=_content_hash(title, desc),
        )
        sev, tier = _classify_severity(avss)
        sub.severity = sev
        sub.bounty_tier = tier
        sub.status = SubmissionStatus.VALIDATED
        sub.verification_stage = VerificationStage.SCORE
        sub.embargo_start = _now().isoformat()
        sub.embargo_end = (_now() + timedelta(days=EMBARGO_DAYS)).isoformat()
        SUBMISSIONS[sub.id] = sub

    for rid in rids:
        _update_researcher_stats(rid)


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ave-vulnerability-marketplace",
        "version": "1.0.0",
        "submissions": len(SUBMISSIONS),
        "researchers": len(RESEARCHERS),
        "programmes": len(PROGRAMMES),
    }


# ---- Submissions ---------------------------------------------------------

@app.post("/v1/submissions", status_code=status.HTTP_201_CREATED)
async def create_submission(data: SubmissionCreate):
    if data.category not in AVE_CATEGORIES:
        raise HTTPException(400, f"Invalid category. Must be one of: {AVE_CATEGORIES}")
    if data.researcher_id not in RESEARCHERS:
        raise HTTPException(404, "Researcher not found — register first")

    ch = _content_hash(data.title, data.description)
    # Duplicate check
    for existing in SUBMISSIONS.values():
        if existing.content_hash == ch:
            raise HTTPException(
                409,
                f"Duplicate submission detected (matches {existing.id})",
            )

    sub = VulnSubmission(
        title=data.title,
        description=data.description,
        category=data.category,
        researcher_id=data.researcher_id,
        affected_frameworks=data.affected_frameworks,
        proof_of_concept=data.proof_of_concept,
        defence_recommendation=data.defence_recommendation,
        real_world_evidence=data.real_world_evidence,
        content_hash=ch,
        embargo_start=_now().isoformat(),
        embargo_end=(_now() + timedelta(days=EMBARGO_DAYS)).isoformat(),
    )
    SUBMISSIONS[sub.id] = sub
    _update_researcher_stats(data.researcher_id)

    prog_match = [
        p
        for p in PROGRAMMES.values()
        if p.active
        and (not p.categories_in_scope or data.category in p.categories_in_scope)
    ]
    for pm in prog_match:
        pm.submissions_received += 1

    return {"id": sub.id, "status": sub.status.value, "embargo_end": sub.embargo_end}


@app.get("/v1/submissions")
async def list_submissions(
    status_filter: Optional[SubmissionStatus] = Query(None, alias="status"),
    category: Optional[str] = None,
    researcher_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    subs = list(SUBMISSIONS.values())
    if status_filter:
        subs = [s for s in subs if s.status == status_filter]
    if category:
        subs = [s for s in subs if s.category == category]
    if researcher_id:
        subs = [s for s in subs if s.researcher_id == researcher_id]
    subs.sort(key=lambda s: s.submitted_at, reverse=True)
    return {"count": len(subs[:limit]), "submissions": [s.dict() for s in subs[:limit]]}


@app.get("/v1/submissions/{sub_id}")
async def get_submission(sub_id: str):
    if sub_id not in SUBMISSIONS:
        raise HTTPException(404, "Submission not found")
    return SUBMISSIONS[sub_id].dict()


@app.patch("/v1/submissions/{sub_id}/status")
async def update_status(sub_id: str, update: StatusUpdate):
    if sub_id not in SUBMISSIONS:
        raise HTTPException(404, "Submission not found")
    sub = SUBMISSIONS[sub_id]
    old_status = sub.status
    sub.status = update.status
    sub.updated_at = _now().isoformat()
    if update.note:
        sub.verification_notes.append({
            "from": old_status.value,
            "to": update.status.value,
            "note": update.note,
            "timestamp": _now().isoformat(),
        })
    _update_researcher_stats(sub.researcher_id)
    return {"id": sub_id, "old_status": old_status.value, "new_status": sub.status.value}


# ---- Verification --------------------------------------------------------

STAGE_ORDER = [
    VerificationStage.TRIAGE,
    VerificationStage.REPRODUCE,
    VerificationStage.VALIDATE,
    VerificationStage.SCORE,
    VerificationStage.REWARD,
]

STATUS_FOR_STAGE = {
    VerificationStage.TRIAGE: SubmissionStatus.TRIAGED,
    VerificationStage.REPRODUCE: SubmissionStatus.REPRODUCING,
    VerificationStage.VALIDATE: SubmissionStatus.VALIDATED,
    VerificationStage.SCORE: SubmissionStatus.SCORED,
    VerificationStage.REWARD: SubmissionStatus.REWARDED,
}


@app.post("/v1/submissions/{sub_id}/verify")
async def advance_verification(sub_id: str, passed: bool = True, note: str = ""):
    if sub_id not in SUBMISSIONS:
        raise HTTPException(404, "Submission not found")
    sub = SUBMISSIONS[sub_id]

    if sub.status in (SubmissionStatus.REJECTED, SubmissionStatus.DISCLOSED):
        raise HTTPException(409, f"Submission is {sub.status.value} — cannot advance")

    cur_idx = STAGE_ORDER.index(sub.verification_stage)

    if not passed:
        sub.status = SubmissionStatus.REJECTED
        sub.verification_notes.append({
            "stage": sub.verification_stage.value,
            "passed": False,
            "note": note,
            "timestamp": _now().isoformat(),
        })
        sub.updated_at = _now().isoformat()
        _update_researcher_stats(sub.researcher_id)
        return {"id": sub_id, "status": "rejected", "stage": sub.verification_stage.value}

    sub.verification_notes.append({
        "stage": sub.verification_stage.value,
        "passed": True,
        "note": note,
        "timestamp": _now().isoformat(),
    })

    if cur_idx < len(STAGE_ORDER) - 1:
        sub.verification_stage = STAGE_ORDER[cur_idx + 1]
        sub.status = STATUS_FOR_STAGE[sub.verification_stage]
    else:
        sub.status = SubmissionStatus.REWARDED

    # Auto-score when reaching SCORE stage
    if sub.verification_stage == VerificationStage.SCORE and sub.avss_score is None:
        sub.avss_score = _auto_score(sub)
        sev, tier = _classify_severity(sub.avss_score)
        sub.severity = sev
        sub.bounty_tier = tier

    # Auto-calculate bounty when reaching REWARD stage
    if sub.status == SubmissionStatus.REWARDED and sub.bounty_amount_usd is None:
        if sub.avss_score is None:
            sub.avss_score = _auto_score(sub)
            sev, tier = _classify_severity(sub.avss_score)
            sub.severity = sev
            sub.bounty_tier = tier
        calc = _calculate_bounty(
            avss_score=sub.avss_score,
            is_novel_category=False,
            has_poc=bool(sub.proof_of_concept),
            has_defence=bool(sub.defence_recommendation),
            multi_framework=len(sub.affected_frameworks) >= 2,
            real_world=sub.real_world_evidence,
        )
        sub.bounty_amount_usd = calc.final_reward_usd
        BOUNTY_PAYOUTS.append({
            "submission_id": sub.id,
            "researcher_id": sub.researcher_id,
            "amount_usd": calc.final_reward_usd,
            "tier": calc.tier.value,
            "timestamp": _now().isoformat(),
        })

    sub.updated_at = _now().isoformat()
    _update_researcher_stats(sub.researcher_id)

    return {
        "id": sub_id,
        "status": sub.status.value,
        "verification_stage": sub.verification_stage.value,
        "avss_score": sub.avss_score,
        "bounty_amount_usd": sub.bounty_amount_usd,
    }


# ---- Bounties ------------------------------------------------------------

@app.get("/v1/bounties")
async def list_bounties(limit: int = Query(50, ge=1, le=500)):
    payouts = sorted(BOUNTY_PAYOUTS, key=lambda p: p["timestamp"], reverse=True)
    return {"count": len(payouts[:limit]), "payouts": payouts[:limit]}


@app.get("/v1/bounties/calculate")
async def calculate_bounty_endpoint(
    avss_score: float = Query(..., ge=0, le=10),
    novel_category: bool = False,
    has_poc: bool = False,
    has_defence: bool = False,
    multi_framework: bool = False,
    real_world: bool = False,
):
    calc = _calculate_bounty(
        avss_score=avss_score,
        is_novel_category=novel_category,
        has_poc=has_poc,
        has_defence=has_defence,
        multi_framework=multi_framework,
        real_world=real_world,
    )
    return calc


@app.post("/v1/bounties/{sub_id}/approve")
async def approve_bounty(sub_id: str):
    if sub_id not in SUBMISSIONS:
        raise HTTPException(404, "Submission not found")
    sub = SUBMISSIONS[sub_id]
    if sub.status != SubmissionStatus.REWARDED:
        raise HTTPException(409, "Submission must be in REWARDED status to approve payout")

    payout = next(
        (p for p in BOUNTY_PAYOUTS if p["submission_id"] == sub_id), None
    )
    if not payout:
        raise HTTPException(404, "No payout record found")

    payout["approved"] = True
    payout["approved_at"] = _now().isoformat()
    _update_researcher_stats(sub.researcher_id)

    return {"approved": True, "submission_id": sub_id, "amount_usd": payout["amount_usd"]}


# ---- Researchers ---------------------------------------------------------

@app.get("/v1/researchers")
async def leaderboard(
    sort_by: str = Query("total_earned_usd", regex="^(total_earned_usd|validated_count|accuracy_rating)$"),
    limit: int = Query(50, ge=1, le=200),
):
    researchers = sorted(
        RESEARCHERS.values(),
        key=lambda r: getattr(r, sort_by),
        reverse=True,
    )
    return {
        "count": len(researchers[:limit]),
        "researchers": [r.dict() for r in researchers[:limit]],
    }


@app.get("/v1/researchers/{res_id}")
async def get_researcher(res_id: str):
    if res_id not in RESEARCHERS:
        raise HTTPException(404, "Researcher not found")
    _update_researcher_stats(res_id)
    return RESEARCHERS[res_id].dict()


@app.post("/v1/researchers", status_code=status.HTTP_201_CREATED)
async def register_researcher(data: ResearcherCreate):
    # Check handle uniqueness
    if any(r.handle == data.handle for r in RESEARCHERS.values()):
        raise HTTPException(409, "Handle already taken")
    r = Researcher(
        handle=data.handle,
        email=data.email,
        bio=data.bio,
        specialties=data.specialties,
    )
    RESEARCHERS[r.id] = r
    return {"id": r.id, "handle": r.handle}


# ---- Programmes ----------------------------------------------------------

@app.get("/v1/programmes")
async def list_programmes(active_only: bool = True):
    progs = list(PROGRAMMES.values())
    if active_only:
        progs = [p for p in progs if p.active]
    return {"count": len(progs), "programmes": [p.dict() for p in progs]}


@app.post("/v1/programmes", status_code=status.HTTP_201_CREATED)
async def create_programme(data: ProgrammeCreate):
    prog = BountyProgramme(
        name=data.name,
        scope=data.scope,
        description=data.description,
        categories_in_scope=data.categories_in_scope,
        frameworks_in_scope=data.frameworks_in_scope,
        max_reward_usd=data.max_reward_usd,
    )
    PROGRAMMES[prog.id] = prog
    return {"id": prog.id, "name": prog.name}


# ---- Disclosure Timeline -------------------------------------------------

@app.get("/v1/disclosure-timeline/{sub_id}")
async def disclosure_timeline(sub_id: str):
    if sub_id not in SUBMISSIONS:
        raise HTTPException(404, "Submission not found")
    sub = SUBMISSIONS[sub_id]

    events: list[dict[str, Any]] = [
        {"event": "submitted", "timestamp": sub.submitted_at},
    ]
    for vn in sub.verification_notes:
        events.append({
            "event": f"verification_{vn.get('stage', 'unknown')}",
            "passed": vn.get("passed"),
            "timestamp": vn.get("timestamp"),
        })
    if sub.embargo_start:
        events.append({"event": "embargo_started", "timestamp": sub.embargo_start})
    if sub.disclosed:
        events.append({"event": "public_disclosure", "timestamp": sub.updated_at})

    days_remaining = None
    if sub.embargo_end and not sub.disclosed:
        end = datetime.fromisoformat(sub.embargo_end)
        days_remaining = max(0, (end - _now()).days)

    return DiscloseTimeline(
        submission_id=sub_id,
        events=events,
        embargo_start=sub.embargo_start,
        embargo_end=sub.embargo_end,
        days_remaining=days_remaining,
        disclosed=sub.disclosed,
    )


# ---- Stats ---------------------------------------------------------------

@app.get("/v1/stats")
async def marketplace_stats():
    subs = list(SUBMISSIONS.values())
    by_status = Counter(s.status.value for s in subs)
    by_category = Counter(s.category for s in subs)
    by_tier = Counter(s.bounty_tier.value for s in subs if s.bounty_tier)

    total_paid = sum(p["amount_usd"] for p in BOUNTY_PAYOUTS)
    avg_bounty = statistics.mean(
        [p["amount_usd"] for p in BOUNTY_PAYOUTS]
    ) if BOUNTY_PAYOUTS else 0.0

    scores = [s.avss_score for s in subs if s.avss_score is not None]
    avg_avss = statistics.mean(scores) if scores else 0.0

    return {
        "total_submissions": len(subs),
        "by_status": dict(by_status),
        "by_category": dict(by_category),
        "by_bounty_tier": dict(by_tier),
        "total_researchers": len(RESEARCHERS),
        "active_programmes": sum(1 for p in PROGRAMMES.values() if p.active),
        "total_paid_usd": round(total_paid, 2),
        "avg_bounty_usd": round(avg_bounty, 2),
        "avg_avss_score": round(avg_avss, 2),
        "embargo_days": EMBARGO_DAYS,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8701)
