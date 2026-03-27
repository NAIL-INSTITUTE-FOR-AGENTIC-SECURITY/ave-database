"""Swarm Consensus Engine — Phase 30 Service 1 · Port 9925"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random

app = FastAPI(title="Swarm Consensus Engine", version="0.30.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class AgentType(str, Enum):
    threat_detector = "threat_detector"
    anomaly_analyser = "anomaly_analyser"
    policy_enforcer = "policy_enforcer"
    response_coordinator = "response_coordinator"
    intel_gatherer = "intel_gatherer"
    vulnerability_scanner = "vulnerability_scanner"
    access_monitor = "access_monitor"
    forensic_investigator = "forensic_investigator"

class VotingProtocol(str, Enum):
    simple_majority = "simple_majority"
    supermajority_66 = "supermajority_66"
    supermajority_75 = "supermajority_75"
    unanimous = "unanimous"
    weighted_majority = "weighted_majority"
    ranked_choice = "ranked_choice"

class ProposalState(str, Enum):
    submitted = "submitted"
    voting = "voting"
    tallying = "tallying"
    decided = "decided"
    archived = "archived"

PROP_TRANSITIONS = {
    "submitted": ["voting"],
    "voting": ["tallying"],
    "tallying": ["decided"],
    "decided": ["archived"],
}

class VoteChoice(str, Enum):
    approve = "approve"
    reject = "reject"
    abstain = "abstain"

# ── Models ───────────────────────────────────────────────────────────
class AgentCreate(BaseModel):
    name: str
    agent_type: AgentType
    weight: float = Field(1.0, ge=0.1, le=10)
    reliability: float = Field(0.8, ge=0, le=1)
    domain: str = "general"

class ProposalCreate(BaseModel):
    title: str
    description: str = ""
    protocol: VotingProtocol = VotingProtocol.simple_majority
    quorum_pct: float = Field(60, ge=10, le=100)
    eligible_agent_ids: list[str] = []

class VoteCast(BaseModel):
    agent_id: str
    choice: VoteChoice
    confidence: float = Field(0.8, ge=0, le=1)
    rationale: str = ""

# ── Stores ───────────────────────────────────────────────────────────
agents: dict[str, dict] = {}
proposals: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Tally Logic ──────────────────────────────────────────────────────
def _effective_power(vote: dict) -> float:
    ag = agents.get(vote["agent_id"], {})
    return vote["confidence"] * ag.get("weight", 1.0) * ag.get("reliability", 0.5)

def _compute_tally(prop: dict) -> dict:
    votes = prop["votes"]
    eligible = prop["eligible_agent_ids"] or list(agents.keys())
    participation = len(votes) / max(len(eligible), 1) * 100
    quorum_met = participation >= prop["quorum_pct"]

    approve_power = sum(_effective_power(v) for v in votes if v["choice"] == "approve")
    reject_power = sum(_effective_power(v) for v in votes if v["choice"] == "reject")
    abstain_count = sum(1 for v in votes if v["choice"] == "abstain")
    total_power = approve_power + reject_power
    approve_pct = (approve_power / max(total_power, 0.001)) * 100 if total_power > 0 else 0

    protocol = prop["protocol"]
    threshold_map = {
        "simple_majority": 50,
        "supermajority_66": 66,
        "supermajority_75": 75,
        "unanimous": 100,
        "weighted_majority": 50,
        "ranked_choice": 50,
    }
    threshold = threshold_map.get(protocol, 50)
    approved = quorum_met and approve_pct >= threshold

    return {
        "participation_pct": round(participation, 1),
        "quorum_met": quorum_met,
        "approve_power": round(approve_power, 3),
        "reject_power": round(reject_power, 3),
        "abstain_count": abstain_count,
        "approve_pct": round(approve_pct, 1),
        "threshold": threshold,
        "decision": "approved" if approved else "rejected",
        "tallied_at": _now(),
    }

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "swarm-consensus-engine",
        "status": "healthy",
        "version": "0.30.1",
        "agents": len(agents),
        "proposals": len(proposals),
    }

# ── Agents ───────────────────────────────────────────────────────────
@app.post("/v1/agents", status_code=201)
def create_agent(body: AgentCreate):
    aid = str(uuid.uuid4())
    rec = {"id": aid, **body.model_dump(), "voting_history": [], "created_at": _now()}
    agents[aid] = rec
    return rec

@app.get("/v1/agents")
def list_agents(agent_type: Optional[AgentType] = None):
    out = list(agents.values())
    if agent_type:
        out = [a for a in out if a["agent_type"] == agent_type]
    return [{k: v for k, v in a.items() if k != "voting_history"} for a in out]

@app.get("/v1/agents/{aid}")
def get_agent(aid: str):
    if aid not in agents:
        raise HTTPException(404, "Agent not found")
    a = agents[aid]
    consistency = 0
    if a["voting_history"]:
        choices = [v["choice"] for v in a["voting_history"]]
        most_common = max(set(choices), key=choices.count)
        consistency = round(choices.count(most_common) / len(choices), 3)
    return {**a, "total_votes": len(a["voting_history"]), "consistency_score": consistency}

# ── Proposals ────────────────────────────────────────────────────────
@app.post("/v1/proposals", status_code=201)
def create_proposal(body: ProposalCreate):
    pid = str(uuid.uuid4())
    rec = {
        "id": pid,
        **body.model_dump(),
        "state": "submitted",
        "votes": [],
        "tally": None,
        "created_at": _now(),
    }
    proposals[pid] = rec
    return rec

@app.get("/v1/proposals")
def list_proposals(state: Optional[ProposalState] = None):
    out = list(proposals.values())
    if state:
        out = [p for p in out if p["state"] == state]
    return [{k: v for k, v in p.items() if k != "votes"} for p in out]

@app.get("/v1/proposals/{pid}")
def get_proposal(pid: str):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    return proposals[pid]

# ── Advance ──────────────────────────────────────────────────────────
@app.patch("/v1/proposals/{pid}/advance")
def advance_proposal(pid: str, target_state: ProposalState = Query(...)):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    p = proposals[pid]
    allowed = PROP_TRANSITIONS.get(p["state"], [])
    if target_state not in allowed:
        raise HTTPException(400, f"Cannot transition from {p['state']} to {target_state}")
    p["state"] = target_state
    return p

# ── Vote ─────────────────────────────────────────────────────────────
@app.post("/v1/proposals/{pid}/vote")
def cast_vote(pid: str, body: VoteCast):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    p = proposals[pid]
    if p["state"] not in ("submitted", "voting"):
        raise HTTPException(400, "Proposal is not accepting votes")
    if body.agent_id not in agents:
        raise HTTPException(404, "Agent not found")
    # Check duplicate
    if any(v["agent_id"] == body.agent_id for v in p["votes"]):
        raise HTTPException(409, "Agent has already voted on this proposal")
    # Check eligibility
    if p["eligible_agent_ids"] and body.agent_id not in p["eligible_agent_ids"]:
        raise HTTPException(403, "Agent not eligible for this proposal")

    p["state"] = "voting"
    vote_rec = {"id": str(uuid.uuid4()), **body.model_dump(), "effective_power": round(_effective_power(body.model_dump()), 3), "cast_at": _now()}
    p["votes"].append(vote_rec)
    agents[body.agent_id]["voting_history"].append({"proposal_id": pid, "choice": body.choice, "confidence": body.confidence, "cast_at": vote_rec["cast_at"]})
    return vote_rec

# ── Tally ────────────────────────────────────────────────────────────
@app.post("/v1/proposals/{pid}/tally")
def tally(pid: str):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    p = proposals[pid]
    if p["state"] not in ("voting", "tallying"):
        raise HTTPException(400, "Proposal must be in voting or tallying state")

    result = _compute_tally(p)
    p["tally"] = result
    p["state"] = "decided"
    return {"proposal_id": pid, **result}

# ── Dissent ──────────────────────────────────────────────────────────
@app.get("/v1/proposals/{pid}/dissent")
def dissent(pid: str):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    p = proposals[pid]
    if not p["tally"]:
        raise HTTPException(400, "Proposal has not been tallied")

    decision = p["tally"]["decision"]
    losing_choice = "reject" if decision == "approved" else "approve"
    dissenters = [v for v in p["votes"] if v["choice"] == losing_choice]
    high_conf_dissenters = [v for v in dissenters if v["confidence"] >= 0.8]

    return {
        "proposal_id": pid,
        "decision": decision,
        "total_dissenters": len(dissenters),
        "dissent_power": round(sum(v["effective_power"] for v in dissenters), 3),
        "high_confidence_dissenters": len(high_conf_dissenters),
        "dissenters": [{"agent_id": v["agent_id"], "agent_name": agents.get(v["agent_id"], {}).get("name", "?"), "confidence": v["confidence"], "effective_power": v["effective_power"], "rationale": v.get("rationale", "")} for v in dissenters],
    }

# ── Deadlock ─────────────────────────────────────────────────────────
@app.get("/v1/proposals/{pid}/deadlock")
def deadlock(pid: str):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    p = proposals[pid]
    eligible = p["eligible_agent_ids"] or list(agents.keys())
    all_voted = len(p["votes"]) >= len(eligible)

    if not p["votes"]:
        return {"proposal_id": pid, "deadlocked": False, "reason": "No votes yet"}

    approve_pwr = sum(_effective_power(v) for v in p["votes"] if v["choice"] == "approve")
    reject_pwr = sum(_effective_power(v) for v in p["votes"] if v["choice"] == "reject")
    total = approve_pwr + reject_pwr
    approve_pct = (approve_pwr / max(total, 0.001)) * 100

    threshold_map = {"simple_majority": 50, "supermajority_66": 66, "supermajority_75": 75, "unanimous": 100, "weighted_majority": 50, "ranked_choice": 50}
    threshold = threshold_map.get(p["protocol"], 50)

    is_deadlocked = all_voted and (threshold - 5) <= approve_pct <= (threshold + 5)
    suggestions = []
    if is_deadlocked:
        suggestions = ["Extend voting period to recruit more agents", "Lower quorum requirement", "Switch to simple_majority protocol", "Escalate to human decision-maker"]

    return {
        "proposal_id": pid,
        "deadlocked": is_deadlocked,
        "approve_pct": round(approve_pct, 1),
        "threshold": threshold,
        "margin": round(abs(approve_pct - threshold), 1),
        "all_eligible_voted": all_voted,
        "escalation_suggestions": suggestions,
    }

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    pl = list(proposals.values())
    decided = [p for p in pl if p["tally"]]
    by_protocol = {}
    for p in pl:
        by_protocol[p["protocol"]] = by_protocol.get(p["protocol"], 0) + 1
    by_decision = {}
    for p in decided:
        d = p["tally"]["decision"]
        by_decision[d] = by_decision.get(d, 0) + 1

    avg_participation = round(sum(p["tally"]["participation_pct"] for p in decided) / max(len(decided), 1), 1) if decided else 0
    avg_approve_pct = round(sum(p["tally"]["approve_pct"] for p in decided) / max(len(decided), 1), 1) if decided else 0

    return {
        "total_agents": len(agents),
        "total_proposals": len(pl),
        "decided_proposals": len(decided),
        "by_protocol": by_protocol,
        "by_decision": by_decision,
        "avg_participation_pct": avg_participation,
        "avg_approve_pct": avg_approve_pct,
        "total_votes_cast": sum(len(p["votes"]) for p in pl),
        "agents_by_type": {at.value: sum(1 for a in agents.values() if a["agent_type"] == at.value) for at in AgentType if any(a["agent_type"] == at.value for a in agents.values())},
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9925)
