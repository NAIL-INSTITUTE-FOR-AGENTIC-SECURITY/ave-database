"""
Agent Capability Marketplace — Phase 22 Service 3 of 5
Port: 9602

Curated registry of vetted agent capabilities with trust scoring,
dependency analysis, supply-chain attestation, and secure distribution.
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

class CapabilityState(str, Enum):
    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    approved = "approved"
    published = "published"
    deprecated = "deprecated"
    revoked = "revoked"


STATE_ORDER = list(CapabilityState)


class CapabilityCategory(str, Enum):
    tool_use = "tool_use"
    reasoning = "reasoning"
    integration = "integration"
    security_control = "security_control"
    data_processing = "data_processing"
    communication = "communication"
    monitoring = "monitoring"
    orchestration = "orchestration"


class SignatureMethod(str, Enum):
    sha256_rsa = "sha256_rsa"
    ed25519 = "ed25519"
    sigstore = "sigstore"


AVE_CATEGORIES: list[str] = [
    "prompt_injection", "tool_misuse", "memory_poisoning",
    "goal_hijacking", "identity_spoofing", "privilege_escalation",
    "data_exfiltration", "resource_exhaustion", "multi_agent_manipulation",
    "context_overflow", "guardrail_bypass", "output_manipulation",
    "supply_chain_compromise", "model_extraction", "reward_hacking",
    "capability_elicitation", "alignment_subversion", "delegation_abuse",
]

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class AttestationCreate(BaseModel):
    signer: str
    signature_method: SignatureMethod = SignatureMethod.sha256_rsa
    build_provenance: Dict[str, Any] = Field(default_factory=dict)
    sbom: List[str] = Field(default_factory=list)


class AttestationRecord(AttestationCreate):
    attestation_id: str
    verified: bool = False
    signature_hash: str = ""
    attested_at: str


class ReviewCreate(BaseModel):
    reviewer: str
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    security_concerns: List[str] = Field(default_factory=list)


class ReviewRecord(ReviewCreate):
    review_id: str
    reviewed_at: str


class CapabilityCreate(BaseModel):
    name: str
    category: CapabilityCategory
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    source_repo: str = ""
    dependencies: List[str] = Field(default_factory=list)  # list of capability_ids
    api_surface: List[str] = Field(default_factory=list)  # list of offered endpoints/methods
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TrustScore(BaseModel):
    attestation_score: float = 0.0
    review_score: float = 0.0
    vulnerability_score: float = 100.0  # starts at 100, decreases with issues
    usage_score: float = 0.0
    total: float = 0.0


class CapabilityRecord(CapabilityCreate):
    capability_id: str
    state: CapabilityState = CapabilityState.draft
    trust: TrustScore = Field(default_factory=TrustScore)
    attestations: List[AttestationRecord] = Field(default_factory=list)
    reviews: List[ReviewRecord] = Field(default_factory=list)
    download_count: int = 0
    known_vulnerabilities: int = 0
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

capabilities: Dict[str, CapabilityRecord] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _recalculate_trust(cap: CapabilityRecord) -> None:
    """Recalculate trust score from all signals."""
    # Attestation (0-100)
    if cap.attestations:
        verified = sum(1 for a in cap.attestations if a.verified)
        cap.trust.attestation_score = round((verified / len(cap.attestations)) * 100, 2)
    else:
        cap.trust.attestation_score = 0.0

    # Reviews (0-100)
    if cap.reviews:
        avg_rating = sum(r.rating for r in cap.reviews) / len(cap.reviews)
        cap.trust.review_score = round((avg_rating / 5.0) * 100, 2)
    else:
        cap.trust.review_score = 0.0

    # Vulnerability (100 - penalty)
    cap.trust.vulnerability_score = round(max(0, 100 - cap.known_vulnerabilities * 15), 2)

    # Usage (0-100, log scale)
    import math
    cap.trust.usage_score = round(min(100, math.log2(max(cap.download_count, 1)) * 10), 2)

    # Weighted total
    cap.trust.total = round(
        0.30 * cap.trust.attestation_score
        + 0.25 * cap.trust.review_score
        + 0.25 * cap.trust.vulnerability_score
        + 0.20 * cap.trust.usage_score,
        2,
    )

    # Transitive trust: cannot exceed lowest-trust dependency
    if cap.dependencies:
        dep_trusts = []
        for dep_id in cap.dependencies:
            if dep_id in capabilities:
                dep_trusts.append(capabilities[dep_id].trust.total)
        if dep_trusts:
            cap.trust.total = min(cap.trust.total, min(dep_trusts))


def _detect_cycles(cap_id: str, deps: List[str]) -> bool:
    """Check if adding deps to cap_id would create a cycle."""
    visited: set = set()
    stack = list(deps)
    while stack:
        current = stack.pop()
        if current == cap_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        if current in capabilities:
            stack.extend(capabilities[current].dependencies)
    return False


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Agent Capability Marketplace",
    description="Phase 22 — Curated agent capability registry with trust scoring and supply-chain attestation",
    version="22.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    published = sum(1 for c in capabilities.values() if c.state == CapabilityState.published)
    return {
        "service": "agent-capability-marketplace",
        "status": "healthy",
        "phase": 22,
        "port": 9602,
        "stats": {
            "total_capabilities": len(capabilities),
            "published": published,
        },
        "timestamp": _now(),
    }


# -- Capabilities ------------------------------------------------------------

@app.post("/v1/capabilities", status_code=201)
def register_capability(body: CapabilityCreate):
    cid = f"CAP-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = CapabilityRecord(**body.dict(), capability_id=cid, created_at=now, updated_at=now)

    # Validate dependencies exist and no cycles
    for dep_id in body.dependencies:
        if dep_id not in capabilities:
            raise HTTPException(422, f"Dependency {dep_id} not found")
    if _detect_cycles(cid, body.dependencies):
        raise HTTPException(422, "Dependency cycle detected")

    _recalculate_trust(record)
    capabilities[cid] = record
    return record.dict()


@app.get("/v1/capabilities")
def list_capabilities(
    category: Optional[CapabilityCategory] = None,
    state: Optional[CapabilityState] = None,
    tag: Optional[str] = None,
    min_trust: Optional[float] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    results = list(capabilities.values())
    if category:
        results = [c for c in results if c.category == category]
    if state:
        results = [c for c in results if c.state == state]
    if tag:
        results = [c for c in results if tag in c.tags]
    if min_trust is not None:
        results = [c for c in results if c.trust.total >= min_trust]
    if q:
        q_lower = q.lower()
        results = [c for c in results if q_lower in c.name.lower() or q_lower in c.description.lower()]
    results.sort(key=lambda c: c.trust.total, reverse=True)
    return {"capabilities": [c.dict() for c in results[:limit]], "total": len(results)}


@app.get("/v1/capabilities/{cap_id}")
def get_capability(cap_id: str):
    if cap_id not in capabilities:
        raise HTTPException(404, "Capability not found")
    cap = capabilities[cap_id]
    cap.download_count += 1
    _recalculate_trust(cap)
    return cap.dict()


@app.patch("/v1/capabilities/{cap_id}/publish")
def publish_capability(cap_id: str):
    if cap_id not in capabilities:
        raise HTTPException(404, "Capability not found")
    cap = capabilities[cap_id]
    idx = STATE_ORDER.index(cap.state)
    target_idx = STATE_ORDER.index(CapabilityState.published)
    if idx >= target_idx:
        raise HTTPException(409, f"Capability already at {cap.state.value}")
    # Must have at least one attestation to publish
    if not cap.attestations:
        raise HTTPException(422, "At least one attestation required before publishing")
    cap.state = CapabilityState.published
    cap.updated_at = _now()
    return {"capability_id": cap_id, "state": cap.state.value}


@app.post("/v1/capabilities/{cap_id}/review", status_code=201)
def submit_review(cap_id: str, body: ReviewCreate):
    if cap_id not in capabilities:
        raise HTTPException(404, "Capability not found")
    cap = capabilities[cap_id]
    rid = f"REV-{uuid.uuid4().hex[:8]}"
    review = ReviewRecord(**body.dict(), review_id=rid, reviewed_at=_now())
    cap.reviews.append(review)
    if body.security_concerns:
        cap.known_vulnerabilities += len(body.security_concerns)
    _recalculate_trust(cap)
    cap.updated_at = _now()
    return review.dict()


@app.post("/v1/capabilities/{cap_id}/attest", status_code=201)
def add_attestation(cap_id: str, body: AttestationCreate):
    if cap_id not in capabilities:
        raise HTTPException(404, "Capability not found")
    cap = capabilities[cap_id]
    aid = f"ATT-{uuid.uuid4().hex[:8]}"
    sig_data = f"{body.signer}:{cap_id}:{body.signature_method.value}:{_now()}"
    sig_hash = hashlib.sha256(sig_data.encode()).hexdigest()
    attestation = AttestationRecord(
        **body.dict(),
        attestation_id=aid,
        verified=True,  # In production: actual cryptographic verification
        signature_hash=sig_hash,
        attested_at=_now(),
    )
    cap.attestations.append(attestation)
    _recalculate_trust(cap)
    cap.updated_at = _now()
    return attestation.dict()


@app.get("/v1/capabilities/{cap_id}/dependencies")
def get_dependencies(cap_id: str):
    if cap_id not in capabilities:
        raise HTTPException(404, "Capability not found")
    cap = capabilities[cap_id]

    tree: List[Dict[str, Any]] = []
    visited: set = set()

    def _walk(cid: str, depth: int = 0):
        if cid in visited:
            return
        visited.add(cid)
        if cid in capabilities:
            c = capabilities[cid]
            tree.append({
                "capability_id": cid,
                "name": c.name,
                "trust_score": c.trust.total,
                "state": c.state.value,
                "depth": depth,
            })
            for dep in c.dependencies:
                _walk(dep, depth + 1)

    for dep in cap.dependencies:
        _walk(dep)

    return {"capability_id": cap_id, "dependency_tree": tree, "total_transitive": len(tree)}


@app.get("/v1/capabilities/{cap_id}/dependents")
def get_dependents(cap_id: str):
    if cap_id not in capabilities:
        raise HTTPException(404, "Capability not found")
    dependents = [
        {"capability_id": c.capability_id, "name": c.name, "trust_score": c.trust.total}
        for c in capabilities.values()
        if cap_id in c.dependencies
    ]
    return {"capability_id": cap_id, "dependents": dependents, "total": len(dependents)}


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    state_dist: Dict[str, int] = defaultdict(int)
    cat_dist: Dict[str, int] = defaultdict(int)
    for c in capabilities.values():
        state_dist[c.state.value] += 1
        cat_dist[c.category.value] += 1

    trust_scores = [c.trust.total for c in capabilities.values()]
    total_reviews = sum(len(c.reviews) for c in capabilities.values())
    total_attestations = sum(len(c.attestations) for c in capabilities.values())

    return {
        "capabilities": {
            "total": len(capabilities),
            "state_distribution": dict(state_dist),
            "category_distribution": dict(cat_dist),
        },
        "trust": {
            "avg_score": round(sum(trust_scores) / max(len(trust_scores), 1), 2) if trust_scores else None,
            "max_score": round(max(trust_scores), 2) if trust_scores else None,
            "min_score": round(min(trust_scores), 2) if trust_scores else None,
        },
        "reviews": total_reviews,
        "attestations": total_attestations,
        "total_vulnerabilities": sum(c.known_vulnerabilities for c in capabilities.values()),
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9602)
