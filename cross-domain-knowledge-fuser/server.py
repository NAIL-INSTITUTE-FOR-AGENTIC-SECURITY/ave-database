"""Cross-Domain Knowledge Fuser — Phase 30 Service 5 · Port 9929"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random
from collections import Counter

app = FastAPI(title="Cross-Domain Knowledge Fuser", version="0.30.5")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class DomainType(str, Enum):
    network = "network"
    endpoint = "endpoint"
    identity = "identity"
    cloud = "cloud"
    application = "application"
    physical = "physical"

class FragmentType(str, Enum):
    indicator = "indicator"
    tactic = "tactic"
    vulnerability = "vulnerability"
    behaviour_pattern = "behaviour_pattern"
    policy_rule = "policy_rule"
    threat_actor = "threat_actor"
    attack_chain = "attack_chain"
    mitigation = "mitigation"

class LinkType(str, Enum):
    correlates_with = "correlates_with"
    enables = "enables"
    mitigates = "mitigates"
    contradicts = "contradicts"
    reinforces = "reinforces"

class FusionState(str, Enum):
    queued = "queued"
    linking = "linking"
    reasoning = "reasoning"
    synthesised = "synthesised"
    published = "published"

FUSION_TRANSITIONS = {
    "queued": ["linking"],
    "linking": ["reasoning"],
    "reasoning": ["synthesised"],
    "synthesised": ["published"],
}

class FusionStrategy(str, Enum):
    union = "union"
    intersection = "intersection"
    weighted_merge = "weighted_merge"
    conflict_resolution = "conflict_resolution"
    temporal_priority = "temporal_priority"

class ConflictResolution(str, Enum):
    domain_priority = "domain_priority"
    confidence_weighted = "confidence_weighted"
    temporal_latest = "temporal_latest"
    human_review = "human_review"

# ── Models ───────────────────────────────────────────────────────────
class DomainCreate(BaseModel):
    name: str
    domain_type: DomainType
    reliability: float = Field(0.8, ge=0, le=1)
    freshness_hours: int = Field(24, ge=1, le=720)
    description: str = ""

class FragmentCreate(BaseModel):
    domain_id: str
    fragment_type: FragmentType
    title: str
    content: str = ""
    confidence: float = Field(0.7, ge=0, le=1)
    attributes: dict = {}
    valid_hours: int = Field(48, ge=1, le=720)

class LinkCreate(BaseModel):
    target_fragment_id: str
    link_type: LinkType
    evidence: str = ""

class FusionCreate(BaseModel):
    name: str
    strategy: FusionStrategy = FusionStrategy.weighted_merge
    domain_ids: list[str] = []
    fragment_ids: list[str] = []
    description: str = ""

class ConflictResolve(BaseModel):
    resolution: ConflictResolution
    rationale: str = ""

# ── Stores ───────────────────────────────────────────────────────────
domains: dict[str, dict] = {}
fragments: dict[str, dict] = {}
fusions: dict[str, dict] = {}
conflicts: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Auto-Link Detection ─────────────────────────────────────────────
def _find_attribute_links(frag: dict) -> list[dict]:
    """Find fragments that share attributes with this fragment."""
    links = []
    frag_attrs = frag.get("attributes", {})
    if not frag_attrs:
        return links

    for other_id, other in fragments.items():
        if other_id == frag["id"]:
            continue
        if other.get("domain_id") == frag.get("domain_id"):
            continue  # Cross-domain only
        other_attrs = other.get("attributes", {})
        shared = set(frag_attrs.keys()) & set(other_attrs.keys())
        matching = {k for k in shared if frag_attrs[k] == other_attrs[k]}
        if matching:
            links.append({
                "target_id": other_id,
                "shared_attributes": list(matching),
                "link_type": "correlates_with",
                "auto_confidence": round(len(matching) / max(len(frag_attrs), 1), 2),
            })
    return links

# ── Confidence Propagation ───────────────────────────────────────────
def _propagated_confidence(frag: dict) -> float:
    """Calculate confidence considering domain reliability and links."""
    domain = domains.get(frag.get("domain_id", ""), {})
    base = frag["confidence"] * domain.get("reliability", 0.5)

    # Boost from corroborating links
    boost = 0
    for link in frag.get("links", []):
        linked_frag = fragments.get(link["target_fragment_id"])
        if linked_frag and link["link_type"] in ("correlates_with", "reinforces"):
            linked_domain = domains.get(linked_frag.get("domain_id", ""), {})
            boost += 0.05 * linked_frag["confidence"] * linked_domain.get("reliability", 0.5)
        elif linked_frag and link["link_type"] == "contradicts":
            boost -= 0.1

    return round(max(0, min(1, base + boost)), 3)

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "cross-domain-knowledge-fuser",
        "status": "healthy",
        "version": "0.30.5",
        "domains": len(domains),
        "fragments": len(fragments),
        "fusions": len(fusions),
        "conflicts": len(conflicts),
    }

# ── Domains ──────────────────────────────────────────────────────────
@app.post("/v1/domains", status_code=201)
def create_domain(body: DomainCreate):
    did = str(uuid.uuid4())
    rec = {"id": did, **body.model_dump(), "created_at": _now()}
    domains[did] = rec
    return rec

@app.get("/v1/domains")
def list_domains():
    enriched = []
    for d in domains.values():
        frag_count = sum(1 for f in fragments.values() if f["domain_id"] == d["id"])
        enriched.append({**d, "fragment_count": frag_count})
    return enriched

# ── Fragments ────────────────────────────────────────────────────────
@app.post("/v1/fragments", status_code=201)
def ingest_fragment(body: FragmentCreate):
    if body.domain_id not in domains:
        raise HTTPException(404, "Domain not found")
    fid = str(uuid.uuid4())
    rec = {
        "id": fid,
        **body.model_dump(),
        "domain_name": domains[body.domain_id]["name"],
        "domain_type": domains[body.domain_id]["domain_type"],
        "links": [],
        "propagated_confidence": 0,
        "stale": False,
        "ingested_at": _now(),
    }
    rec["propagated_confidence"] = _propagated_confidence(rec)

    # Auto-detect cross-domain links
    auto_links = _find_attribute_links(rec)
    for al in auto_links:
        link_rec = {
            "id": str(uuid.uuid4()),
            "target_fragment_id": al["target_id"],
            "link_type": al["link_type"],
            "evidence": f"Auto-linked via shared attributes: {', '.join(al['shared_attributes'])}",
            "auto_detected": True,
            "created_at": _now(),
        }
        rec["links"].append(link_rec)

        # Check for contradictions → create conflict
        target = fragments.get(al["target_id"])
        if target and rec["fragment_type"] == target["fragment_type"] and rec["content"] != target.get("content", "") and rec["confidence"] > 0.5 and target["confidence"] > 0.5:
            cid = str(uuid.uuid4())
            conflicts[cid] = {
                "id": cid,
                "fragment_a_id": fid,
                "fragment_b_id": al["target_id"],
                "fragment_a_domain": rec["domain_type"],
                "fragment_b_domain": target["domain_type"],
                "type": "cross_domain_contradiction",
                "resolved": False,
                "resolution": None,
                "created_at": _now(),
            }

    fragments[fid] = rec
    return rec

@app.get("/v1/fragments")
def list_fragments(domain_id: Optional[str] = None, fragment_type: Optional[FragmentType] = None, limit: int = Query(100, ge=1, le=1000)):
    out = list(fragments.values())
    if domain_id:
        out = [f for f in out if f["domain_id"] == domain_id]
    if fragment_type:
        out = [f for f in out if f["fragment_type"] == fragment_type]
    return [{k: v for k, v in f.items() if k != "links"} for f in out[-limit:]]

@app.get("/v1/fragments/{fid}")
def get_fragment(fid: str):
    if fid not in fragments:
        raise HTTPException(404, "Fragment not found")
    f = fragments[fid]
    f["propagated_confidence"] = _propagated_confidence(f)
    return f

# ── Manual Link ──────────────────────────────────────────────────────
@app.post("/v1/fragments/{fid}/link")
def create_link(fid: str, body: LinkCreate):
    if fid not in fragments:
        raise HTTPException(404, "Source fragment not found")
    if body.target_fragment_id not in fragments:
        raise HTTPException(404, "Target fragment not found")

    link_rec = {
        "id": str(uuid.uuid4()),
        **body.model_dump(),
        "auto_detected": False,
        "created_at": _now(),
    }
    fragments[fid]["links"].append(link_rec)

    # Recalculate confidence
    fragments[fid]["propagated_confidence"] = _propagated_confidence(fragments[fid])

    return link_rec

# ── Fusions ──────────────────────────────────────────────────────────
@app.post("/v1/fusions", status_code=201)
def create_fusion(body: FusionCreate):
    fid = str(uuid.uuid4())
    rec = {
        "id": fid,
        **body.model_dump(),
        "state": "queued",
        "intelligence_product": None,
        "created_at": _now(),
    }
    fusions[fid] = rec
    return rec

@app.get("/v1/fusions")
def list_fusions(state: Optional[FusionState] = None):
    out = list(fusions.values())
    if state:
        out = [f for f in out if f["state"] == state]
    return out

@app.get("/v1/fusions/{fid}")
def get_fusion(fid: str):
    if fid not in fusions:
        raise HTTPException(404, "Fusion not found")
    return fusions[fid]

@app.post("/v1/fusions/{fid}/execute")
def execute_fusion(fid: str):
    if fid not in fusions:
        raise HTTPException(404, "Fusion not found")
    f = fusions[fid]
    if f["state"] not in ("queued", "linking"):
        raise HTTPException(400, f"Fusion must be queued or linking, currently {f['state']}")

    # Gather fragments
    target_frags = []
    if f["fragment_ids"]:
        target_frags = [fragments[fid2] for fid2 in f["fragment_ids"] if fid2 in fragments]
    elif f["domain_ids"]:
        target_frags = [fr for fr in fragments.values() if fr["domain_id"] in f["domain_ids"]]
    else:
        target_frags = list(fragments.values())

    if not target_frags:
        raise HTTPException(400, "No fragments to fuse")

    # Count cross-domain links
    link_count = sum(len(fr.get("links", [])) for fr in target_frags)
    domains_covered = set(fr["domain_type"] for fr in target_frags)

    # Build evidence chains
    evidence_chains = []
    for fr in target_frags:
        for link in fr.get("links", []):
            target = fragments.get(link["target_fragment_id"])
            if target:
                evidence_chains.append({
                    "from_domain": fr["domain_type"],
                    "to_domain": target["domain_type"],
                    "link_type": link["link_type"],
                    "from_fragment": fr["title"],
                    "to_fragment": target["title"],
                })

    # Aggregate confidence per strategy
    confidences = [_propagated_confidence(fr) for fr in target_frags]
    if f["strategy"] == "weighted_merge":
        agg_confidence = round(sum(confidences) / max(len(confidences), 1), 3)
    elif f["strategy"] == "intersection":
        agg_confidence = round(min(confidences) if confidences else 0, 3)
    elif f["strategy"] == "union":
        agg_confidence = round(max(confidences) if confidences else 0, 3)
    else:
        agg_confidence = round(sum(confidences) / max(len(confidences), 1), 3)

    product = {
        "fragments_fused": len(target_frags),
        "domains_covered": list(domains_covered),
        "domain_count": len(domains_covered),
        "cross_domain_links": link_count,
        "evidence_chains": evidence_chains[:20],
        "aggregate_confidence": agg_confidence,
        "fragment_types": dict(Counter(fr["fragment_type"] for fr in target_frags)),
        "key_findings": [fr["title"] for fr in sorted(target_frags, key=lambda x: x["confidence"], reverse=True)[:5]],
        "strategy_used": f["strategy"],
        "fused_at": _now(),
    }

    f["intelligence_product"] = product
    f["state"] = "synthesised"
    return f

# ── Conflicts ────────────────────────────────────────────────────────
@app.get("/v1/conflicts")
def list_conflicts(resolved: Optional[bool] = None):
    out = list(conflicts.values())
    if resolved is not None:
        out = [c for c in out if c["resolved"] == resolved]
    return out

@app.post("/v1/conflicts/{cid}/resolve")
def resolve_conflict(cid: str, body: ConflictResolve):
    if cid not in conflicts:
        raise HTTPException(404, "Conflict not found")
    c = conflicts[cid]
    c["resolved"] = True
    c["resolution"] = body.resolution
    c["rationale"] = body.rationale
    c["resolved_at"] = _now()

    # Apply resolution
    frag_a = fragments.get(c["fragment_a_id"])
    frag_b = fragments.get(c["fragment_b_id"])
    if frag_a and frag_b:
        if body.resolution == "confidence_weighted":
            winner = frag_a if frag_a["confidence"] >= frag_b["confidence"] else frag_b
            c["winner_fragment_id"] = winner["id"]
        elif body.resolution == "temporal_latest":
            c["winner_fragment_id"] = frag_a["id"] if frag_a["ingested_at"] >= frag_b["ingested_at"] else frag_b["id"]
        elif body.resolution == "domain_priority":
            # Prefer the domain with higher reliability
            dom_a = domains.get(frag_a["domain_id"], {})
            dom_b = domains.get(frag_b["domain_id"], {})
            c["winner_fragment_id"] = frag_a["id"] if dom_a.get("reliability", 0) >= dom_b.get("reliability", 0) else frag_b["id"]

    return c

# ── Coverage ─────────────────────────────────────────────────────────
@app.get("/v1/coverage")
def coverage():
    domain_frags = {}
    for d in domains.values():
        frags = [f for f in fragments.values() if f["domain_id"] == d["id"]]
        types_covered = set(f["fragment_type"] for f in frags)
        cross_links = sum(1 for f in frags for l in f.get("links", []) if fragments.get(l["target_fragment_id"], {}).get("domain_id") != d["id"])

        domain_frags[d["name"]] = {
            "domain_type": d["domain_type"],
            "fragment_count": len(frags),
            "types_covered": list(types_covered),
            "type_coverage_pct": round(len(types_covered) / len(FragmentType) * 100, 1),
            "cross_domain_links": cross_links,
            "reliability": d["reliability"],
        }

    # Identify blind spots
    all_types = set(ft.value for ft in FragmentType)
    blind_spots = []
    for dname, info in domain_frags.items():
        missing = all_types - set(info["types_covered"])
        if missing:
            blind_spots.append({"domain": dname, "missing_types": list(missing), "recommendation": f"Enrich {dname} with {', '.join(missing)} fragments"})

    # Single-domain fragments (no cross-domain corroboration)
    single_domain = sum(1 for f in fragments.values() if not f.get("links"))
    total = len(fragments)

    return {
        "domains": domain_frags,
        "total_fragments": total,
        "single_domain_fragments": single_domain,
        "cross_domain_corroboration_pct": round((1 - single_domain / max(total, 1)) * 100, 1),
        "blind_spots": blind_spots,
    }

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    fl = list(fragments.values())
    by_domain = Counter(f["domain_type"] for f in fl)
    by_type = Counter(f["fragment_type"] for f in fl)
    total_links = sum(len(f.get("links", [])) for f in fl)
    auto_links = sum(1 for f in fl for l in f.get("links", []) if l.get("auto_detected"))
    manual_links = total_links - auto_links

    cl = list(conflicts.values())
    resolved = sum(1 for c in cl if c["resolved"])

    fu = list(fusions.values())
    by_state = Counter(f["state"] for f in fu)
    by_strategy = Counter(f["strategy"] for f in fu)

    return {
        "total_domains": len(domains),
        "total_fragments": len(fl),
        "by_domain_type": dict(by_domain),
        "by_fragment_type": dict(by_type),
        "total_links": total_links,
        "auto_detected_links": auto_links,
        "manual_links": manual_links,
        "link_density": round(total_links / max(len(fl), 1), 2),
        "total_conflicts": len(cl),
        "resolved_conflicts": resolved,
        "unresolved_conflicts": len(cl) - resolved,
        "total_fusions": len(fu),
        "by_fusion_state": dict(by_state),
        "by_fusion_strategy": dict(by_strategy),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9929)
