"""Emergent Strategy Detector — Phase 30 Service 4 · Port 9928"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random
from collections import Counter

app = FastAPI(title="Emergent Strategy Detector", version="0.30.4")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class InteractionType(str, Enum):
    coordination = "coordination"
    delegation = "delegation"
    information_sharing = "information_sharing"
    conflict = "conflict"
    negotiation = "negotiation"
    resource_competition = "resource_competition"
    alliance_formation = "alliance_formation"

class InteractionOutcome(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

class PatternType(str, Enum):
    clustering = "clustering"
    specialisation = "specialisation"
    hierarchy_formation = "hierarchy_formation"
    free_riding = "free_riding"
    collusion = "collusion"
    load_balancing = "load_balancing"
    emergent_leadership = "emergent_leadership"

class StrategyClassification(str, Enum):
    beneficial = "beneficial"
    neutral = "neutral"
    adversarial = "adversarial"
    unknown = "unknown"

class StrategyLifecycle(str, Enum):
    emerging = "emerging"
    active = "active"
    stable = "stable"
    dissolving = "dissolving"
    extinct = "extinct"

# Pattern classification mappings
PATTERN_CLASSIFICATION = {
    "clustering": "neutral",
    "specialisation": "beneficial",
    "hierarchy_formation": "neutral",
    "free_riding": "adversarial",
    "collusion": "adversarial",
    "load_balancing": "beneficial",
    "emergent_leadership": "beneficial",
}

# ── Models ───────────────────────────────────────────────────────────
class InteractionCreate(BaseModel):
    agent_a_id: str
    agent_b_id: str
    interaction_type: InteractionType
    outcome: InteractionOutcome = InteractionOutcome.neutral
    strength: float = Field(0.5, ge=0, le=1)
    context: str = ""

# ── Stores ───────────────────────────────────────────────────────────
interactions: list[dict] = []
strategies: dict[str, dict] = {}
coalitions: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Pattern Detection Engine ─────────────────────────────────────────
def _build_graph() -> dict[str, dict[str, list[dict]]]:
    """Build adjacency with interaction lists."""
    graph: dict[str, dict[str, list[dict]]] = {}
    for ix in interactions:
        a, b = ix["agent_a_id"], ix["agent_b_id"]
        if a not in graph:
            graph[a] = {}
        if b not in graph:
            graph[b] = {}
        graph[a].setdefault(b, []).append(ix)
        graph[b].setdefault(a, []).append(ix)
    return graph

def _detect_patterns() -> list[dict]:
    graph = _build_graph()
    if not graph:
        return []

    detected = []
    agent_ids = list(graph.keys())

    # 1. Clustering: groups with dense internal connections
    for aid in agent_ids:
        neighbours = list(graph.get(aid, {}).keys())
        if len(neighbours) >= 3:
            # Check density among neighbours
            internal = 0
            for i, n1 in enumerate(neighbours):
                for n2 in neighbours[i + 1:]:
                    if n2 in graph.get(n1, {}):
                        internal += 1
            possible = len(neighbours) * (len(neighbours) - 1) / 2
            density = internal / max(possible, 1)
            if density > 0.5:
                detected.append({"pattern": "clustering", "agents": [aid] + neighbours[:5], "density": round(density, 2), "evidence_count": internal})

    # 2. Specialisation: agents mostly do one interaction type
    agent_type_counts: dict[str, Counter] = {}
    for ix in interactions:
        for ag in [ix["agent_a_id"], ix["agent_b_id"]]:
            if ag not in agent_type_counts:
                agent_type_counts[ag] = Counter()
            agent_type_counts[ag][ix["interaction_type"]] += 1

    specialists = []
    for ag, counts in agent_type_counts.items():
        total = sum(counts.values())
        if total >= 3:
            top_type, top_count = counts.most_common(1)[0]
            if top_count / total > 0.7:
                specialists.append(ag)
    if len(specialists) >= 2:
        detected.append({"pattern": "specialisation", "agents": specialists[:10], "specialist_count": len(specialists), "evidence_count": len(specialists)})

    # 3. Hierarchy: some agents delegate much more than others
    delegation_out = Counter()
    delegation_in = Counter()
    for ix in interactions:
        if ix["interaction_type"] == "delegation":
            delegation_out[ix["agent_a_id"]] += 1
            delegation_in[ix["agent_b_id"]] += 1
    leaders = [a for a, c in delegation_out.items() if c >= 3 and delegation_in.get(a, 0) < c]
    if leaders:
        detected.append({"pattern": "hierarchy_formation", "agents": leaders, "leader_count": len(leaders), "evidence_count": sum(delegation_out[l] for l in leaders)})
        detected.append({"pattern": "emergent_leadership", "agents": leaders[:3], "leader_count": len(leaders), "evidence_count": sum(delegation_out[l] for l in leaders)})

    # 4. Free-riding: agents that receive info but rarely share
    info_given = Counter()
    info_received = Counter()
    for ix in interactions:
        if ix["interaction_type"] == "information_sharing":
            info_given[ix["agent_a_id"]] += 1
            info_received[ix["agent_b_id"]] += 1
    free_riders = [a for a in info_received if info_received[a] >= 3 and info_given.get(a, 0) <= 1]
    if free_riders:
        detected.append({"pattern": "free_riding", "agents": free_riders, "free_rider_count": len(free_riders), "evidence_count": sum(info_received[f] for f in free_riders)})

    # 5. Load balancing: even distribution of coordination
    coord_counts = Counter()
    for ix in interactions:
        if ix["interaction_type"] == "coordination":
            coord_counts[ix["agent_a_id"]] += 1
            coord_counts[ix["agent_b_id"]] += 1
    if len(coord_counts) >= 3:
        vals = list(coord_counts.values())
        mean_c = sum(vals) / len(vals)
        std_c = (sum((v - mean_c) ** 2 for v in vals) / len(vals)) ** 0.5
        cv = std_c / max(mean_c, 1)
        if cv < 0.3:
            detected.append({"pattern": "load_balancing", "agents": list(coord_counts.keys())[:10], "coefficient_of_variation": round(cv, 3), "evidence_count": sum(vals)})

    return detected

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "emergent-strategy-detector",
        "status": "healthy",
        "version": "0.30.4",
        "interactions": len(interactions),
        "strategies": len(strategies),
        "coalitions": len(coalitions),
    }

# ── Interactions ─────────────────────────────────────────────────────
@app.post("/v1/interactions", status_code=201)
def record_interaction(body: InteractionCreate):
    rec = {"id": str(uuid.uuid4()), **body.model_dump(), "recorded_at": _now()}
    interactions.append(rec)
    return rec

@app.get("/v1/interactions")
def list_interactions(interaction_type: Optional[InteractionType] = None, agent_id: Optional[str] = None, limit: int = Query(100, ge=1, le=1000)):
    out = interactions
    if interaction_type:
        out = [i for i in out if i["interaction_type"] == interaction_type]
    if agent_id:
        out = [i for i in out if i["agent_a_id"] == agent_id or i["agent_b_id"] == agent_id]
    return out[-limit:]

# ── Detect Patterns ──────────────────────────────────────────────────
@app.post("/v1/detect-patterns")
def detect_patterns():
    patterns = _detect_patterns()
    new_strategies = []

    for p in patterns:
        # Create or update strategy
        existing = next((s for s in strategies.values() if s["pattern"] == p["pattern"] and set(s["agents"][:3]) & set(p["agents"][:3])), None)
        if existing:
            existing["evidence_count"] = max(existing["evidence_count"], p["evidence_count"])
            existing["last_seen"] = _now()
            # Lifecycle progression
            if existing["lifecycle"] == "emerging" and p["evidence_count"] >= 5:
                existing["lifecycle"] = "active"
            elif existing["lifecycle"] == "active" and p["evidence_count"] >= 10:
                existing["lifecycle"] = "stable"
        else:
            sid = str(uuid.uuid4())
            strat = {
                "id": sid,
                "pattern": p["pattern"],
                "classification": PATTERN_CLASSIFICATION.get(p["pattern"], "unknown"),
                "lifecycle": "emerging",
                "agents": p["agents"],
                "evidence_count": p["evidence_count"],
                "confidence": round(min(0.95, p["evidence_count"] * 0.1), 2),
                "first_detected": _now(),
                "last_seen": _now(),
            }
            strategies[sid] = strat
            new_strategies.append(strat)

    return {"patterns_found": len(patterns), "new_strategies": len(new_strategies), "total_strategies": len(strategies), "details": patterns}

# ── Strategies ───────────────────────────────────────────────────────
@app.get("/v1/strategies")
def list_strategies(classification: Optional[StrategyClassification] = None, lifecycle: Optional[StrategyLifecycle] = None):
    out = list(strategies.values())
    if classification:
        out = [s for s in out if s["classification"] == classification]
    if lifecycle:
        out = [s for s in out if s["lifecycle"] == lifecycle]
    return out

@app.get("/v1/strategies/{sid}")
def get_strategy(sid: str):
    if sid not in strategies:
        raise HTTPException(404, "Strategy not found")
    return strategies[sid]

@app.get("/v1/strategies/{sid}/impact")
def strategy_impact(sid: str):
    if sid not in strategies:
        raise HTTPException(404, "Strategy not found")
    s = strategies[sid]
    # Measure impact from related interactions
    agent_set = set(s["agents"])
    related = [ix for ix in interactions if ix["agent_a_id"] in agent_set or ix["agent_b_id"] in agent_set]

    positive = sum(1 for ix in related if ix["outcome"] == "positive")
    negative = sum(1 for ix in related if ix["outcome"] == "negative")
    total = len(related)
    avg_strength = round(sum(ix["strength"] for ix in related) / max(total, 1), 3)

    impact_score = round((positive - negative) / max(total, 1) * 100, 1)

    return {
        "strategy_id": sid,
        "pattern": s["pattern"],
        "classification": s["classification"],
        "total_related_interactions": total,
        "positive_outcomes": positive,
        "negative_outcomes": negative,
        "impact_score": impact_score,
        "avg_interaction_strength": avg_strength,
        "assessment": "beneficial" if impact_score > 20 else "harmful" if impact_score < -20 else "neutral",
    }

# ── Coalitions ───────────────────────────────────────────────────────
@app.get("/v1/coalitions")
def detect_coalitions():
    graph = _build_graph()
    found = []

    # Simple dense subgraph detection
    for agent in graph:
        neighbours = set(graph[agent].keys())
        if len(neighbours) < 2:
            continue
        # Check if neighbours form a clique-like structure
        coalition_members = {agent}
        for n in neighbours:
            n_neighbours = set(graph.get(n, {}).keys())
            overlap = neighbours & n_neighbours
            if len(overlap) >= len(neighbours) * 0.5:
                coalition_members.add(n)

        if len(coalition_members) >= 3:
            key = frozenset(coalition_members)
            # Deduplicate
            existing = any(frozenset(c["members"]) == key for c in coalitions.values())
            if not existing:
                cid = str(uuid.uuid4())
                internal_ix = [ix for ix in interactions if ix["agent_a_id"] in coalition_members and ix["agent_b_id"] in coalition_members]
                external_ix = [ix for ix in interactions if (ix["agent_a_id"] in coalition_members) != (ix["agent_b_id"] in coalition_members)]
                stability = round(len(internal_ix) / max(len(internal_ix) + len(external_ix), 1), 3)
                exclusivity = round(1 - len(external_ix) / max(len(internal_ix) + len(external_ix), 1), 3)

                coal = {
                    "id": cid,
                    "members": list(coalition_members),
                    "size": len(coalition_members),
                    "internal_interactions": len(internal_ix),
                    "external_interactions": len(external_ix),
                    "stability": stability,
                    "exclusivity": exclusivity,
                    "detected_at": _now(),
                }
                coalitions[cid] = coal
                found.append(coal)

    return {"coalitions_detected": len(found), "total_coalitions": len(coalitions), "coalitions": list(coalitions.values())}

# ── Free-Riders ──────────────────────────────────────────────────────
@app.get("/v1/free-riders")
def free_riders():
    give = Counter()
    receive = Counter()
    for ix in interactions:
        give[ix["agent_a_id"]] += 1
        receive[ix["agent_b_id"]] += 1

    all_agents = set(give.keys()) | set(receive.keys())
    riders = []
    for ag in all_agents:
        given = give.get(ag, 0)
        received = receive.get(ag, 0)
        total = given + received
        if total >= 3 and received > 0:
            ratio = given / max(received, 1)
            if ratio < 0.3:
                riders.append({
                    "agent_id": ag,
                    "interactions_initiated": given,
                    "interactions_received": received,
                    "contribution_ratio": round(ratio, 3),
                    "free_riding_severity": "high" if ratio < 0.1 else "medium",
                })

    return {"total_agents_analysed": len(all_agents), "free_riders_detected": len(riders), "free_riders": sorted(riders, key=lambda r: r["contribution_ratio"])}

# ── Collusion Scan ───────────────────────────────────────────────────
@app.get("/v1/collusion-scan")
def collusion_scan():
    # Find pairs that always align (same interaction types, outcomes)
    pair_align: dict[tuple, list] = {}
    for ix in interactions:
        pair = tuple(sorted([ix["agent_a_id"], ix["agent_b_id"]]))
        pair_align.setdefault(pair, []).append(ix)

    suspects = []
    for pair, ixs in pair_align.items():
        if len(ixs) < 3:
            continue
        # Check outcome alignment
        outcomes = [ix["outcome"] for ix in ixs]
        diversity = len(set(outcomes)) / len(outcomes)
        # Check if mostly alliance/coordination
        types = [ix["interaction_type"] for ix in ixs]
        alliance_ratio = sum(1 for t in types if t in ("alliance_formation", "coordination")) / len(types)

        if diversity < 0.4 and alliance_ratio > 0.6:
            suspects.append({
                "agents": list(pair),
                "interaction_count": len(ixs),
                "outcome_diversity": round(diversity, 3),
                "alliance_ratio": round(alliance_ratio, 3),
                "collusion_score": round((1 - diversity) * alliance_ratio * 100, 1),
            })

    return {"pairs_analysed": len(pair_align), "collusion_suspects": len(suspects), "suspects": sorted(suspects, key=lambda s: s["collusion_score"], reverse=True)}

# ── Interventions ────────────────────────────────────────────────────
@app.get("/v1/interventions")
def interventions():
    recs = []
    for s in strategies.values():
        if s["classification"] == "adversarial":
            if s["pattern"] == "free_riding":
                recs.append({"strategy_id": s["id"], "pattern": s["pattern"], "action": "incentive_adjustment", "description": "Introduce contribution requirements for resource access", "priority": "medium", "agents_affected": s["agents"]})
            elif s["pattern"] == "collusion":
                recs.append({"strategy_id": s["id"], "pattern": s["pattern"], "action": "coalition_break", "description": "Redistribute colluding agents across different task groups", "priority": "high", "agents_affected": s["agents"]})
                recs.append({"strategy_id": s["id"], "pattern": s["pattern"], "action": "isolation", "description": "Temporarily isolate suspected colluders for independent verification", "priority": "high", "agents_affected": s["agents"]})
        elif s["classification"] == "beneficial" and s["lifecycle"] in ("emerging", "active"):
            recs.append({"strategy_id": s["id"], "pattern": s["pattern"], "action": "role_reassignment", "description": f"Reinforce {s['pattern']} by assigning complementary tasks", "priority": "low", "agents_affected": s["agents"]})

    return {"total_recommendations": len(recs), "interventions": recs}

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    sl = list(strategies.values())
    by_class = Counter(s["classification"] for s in sl)
    by_pattern = Counter(s["pattern"] for s in sl)
    by_lifecycle = Counter(s["lifecycle"] for s in sl)
    by_ix_type = Counter(ix["interaction_type"] for ix in interactions)

    unique_agents = set()
    for ix in interactions:
        unique_agents.add(ix["agent_a_id"])
        unique_agents.add(ix["agent_b_id"])

    return {
        "total_interactions": len(interactions),
        "unique_agents": len(unique_agents),
        "by_interaction_type": dict(by_ix_type),
        "total_strategies": len(sl),
        "by_classification": dict(by_class),
        "by_pattern": dict(by_pattern),
        "by_lifecycle": dict(by_lifecycle),
        "total_coalitions": len(coalitions),
        "adversarial_strategies": by_class.get("adversarial", 0),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9928)
