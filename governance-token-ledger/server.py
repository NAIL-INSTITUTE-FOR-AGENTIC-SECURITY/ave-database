"""Governance Token Ledger — Phase 26 Service 3 · Port 9907"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

app = FastAPI(title="Governance Token Ledger", version="0.26.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class StakeholderRole(str, Enum):
    founder = "founder"
    board_member = "board_member"
    operator = "operator"
    auditor = "auditor"
    community = "community"
    regulator = "regulator"

class TokenType(str, Enum):
    voting = "voting"
    veto = "veto"
    proposal = "proposal"
    delegation = "delegation"

class ProposalState(str, Enum):
    draft = "draft"
    submitted = "submitted"
    discussion = "discussion"
    voting = "voting"
    passed = "passed"
    rejected = "rejected"
    enacted = "enacted"
    archived = "archived"

PROPOSAL_TRANSITIONS = {
    "draft": ["submitted"],
    "submitted": ["discussion"],
    "discussion": ["voting"],
    "voting": ["passed", "rejected"],
    "passed": ["enacted"],
    "enacted": ["archived"],
    "rejected": ["archived"],
}

class ProposalCategory(str, Enum):
    policy_change = "policy_change"
    budget_allocation = "budget_allocation"
    system_deployment = "system_deployment"
    access_modification = "access_modification"
    compliance_update = "compliance_update"
    emergency_action = "emergency_action"
    constitutional_amendment = "constitutional_amendment"
    community_initiative = "community_initiative"

class VotingType(str, Enum):
    simple_majority = "simple_majority"
    supermajority = "supermajority"
    weighted_consensus = "weighted_consensus"
    ranked_choice = "ranked_choice"

# ── Models ───────────────────────────────────────────────────────────
class StakeholderCreate(BaseModel):
    name: str
    role: StakeholderRole
    organisation: str = ""
    voting_weight: int = Field(1, ge=1, le=100)

class MintRequest(BaseModel):
    stakeholder_id: str
    token_type: TokenType
    amount: int = Field(1, ge=1)
    reason: str = ""

class TransferRequest(BaseModel):
    from_id: str
    to_id: str
    token_type: TokenType
    amount: int = Field(1, ge=1)

class ProposalCreate(BaseModel):
    title: str
    description: str = ""
    category: ProposalCategory
    proposer_id: str
    voting_type: VotingType = VotingType.simple_majority
    quorum_percentage: float = Field(50.0, ge=0, le=100)
    approval_threshold: float = Field(50.1, ge=0, le=100)
    voting_duration_hours: int = Field(72, ge=1)

class VoteRequest(BaseModel):
    voter_id: str
    vote: str = Field(..., pattern="^(for|against|abstain)$")

class VetoRequest(BaseModel):
    vetoer_id: str
    justification: str

class DelegationCreate(BaseModel):
    delegator_id: str
    delegate_id: str
    topic: str = "global"

# ── Stores ───────────────────────────────────────────────────────────
stakeholders: dict[str, dict] = {}
balances: dict[str, dict[str, int]] = {}   # stakeholder_id -> {token_type: amount}
proposals: dict[str, dict] = {}
votes: dict[str, list[dict]] = {}          # proposal_id -> [votes]
delegations: dict[str, dict] = {}
ledger: list[dict] = []                    # immutable transaction log

def _now():
    return datetime.now(timezone.utc).isoformat()

def _log_tx(tx_type: str, **kwargs):
    entry = {"tx_id": str(uuid.uuid4()), "type": tx_type, "timestamp": _now(), **kwargs}
    ledger.append(entry)
    return entry

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "governance-token-ledger",
        "status": "healthy",
        "version": "0.26.3",
        "stakeholders": len(stakeholders),
        "proposals": len(proposals),
        "ledger_entries": len(ledger),
    }

# ── Stakeholders ─────────────────────────────────────────────────────
@app.post("/v1/stakeholders", status_code=201)
def create_stakeholder(body: StakeholderCreate):
    sid = str(uuid.uuid4())
    rec = {"id": sid, **body.model_dump(), "created_at": _now()}
    stakeholders[sid] = rec
    balances[sid] = {t.value: 0 for t in TokenType}
    _log_tx("stakeholder_registered", stakeholder_id=sid, role=body.role)
    return rec

@app.get("/v1/stakeholders")
def list_stakeholders(role: Optional[StakeholderRole] = None):
    out = list(stakeholders.values())
    if role:
        out = [s for s in out if s["role"] == role]
    return out

# ── Token Operations ─────────────────────────────────────────────────
@app.post("/v1/tokens/mint", status_code=201)
def mint_tokens(body: MintRequest):
    if body.stakeholder_id not in stakeholders:
        raise HTTPException(404, "Stakeholder not found")
    balances[body.stakeholder_id][body.token_type] += body.amount
    _log_tx("mint", stakeholder_id=body.stakeholder_id, token_type=body.token_type, amount=body.amount, reason=body.reason)
    return {"stakeholder_id": body.stakeholder_id, "token_type": body.token_type, "new_balance": balances[body.stakeholder_id][body.token_type]}

@app.post("/v1/tokens/transfer")
def transfer_tokens(body: TransferRequest):
    if body.from_id not in stakeholders:
        raise HTTPException(404, "Sender not found")
    if body.to_id not in stakeholders:
        raise HTTPException(404, "Recipient not found")
    if balances[body.from_id][body.token_type] < body.amount:
        raise HTTPException(400, "Insufficient balance")
    balances[body.from_id][body.token_type] -= body.amount
    balances[body.to_id][body.token_type] += body.amount
    _log_tx("transfer", from_id=body.from_id, to_id=body.to_id, token_type=body.token_type, amount=body.amount)
    return {"from_balance": balances[body.from_id][body.token_type], "to_balance": balances[body.to_id][body.token_type]}

@app.get("/v1/tokens/balances")
def get_balances(stakeholder_id: Optional[str] = None):
    if stakeholder_id:
        if stakeholder_id not in balances:
            raise HTTPException(404, "Stakeholder not found")
        return {"stakeholder_id": stakeholder_id, "balances": balances[stakeholder_id]}
    return {sid: balances[sid] for sid in balances}

# ── Proposals ────────────────────────────────────────────────────────
@app.post("/v1/proposals", status_code=201)
def create_proposal(body: ProposalCreate):
    if body.proposer_id not in stakeholders:
        raise HTTPException(404, "Proposer not found")
    # Check proposal tokens
    if balances[body.proposer_id].get("proposal", 0) < 1:
        raise HTTPException(400, "Proposer needs at least 1 proposal token")
    balances[body.proposer_id]["proposal"] -= 1

    pid = str(uuid.uuid4())
    rec = {
        "id": pid,
        **body.model_dump(),
        "state": "draft",
        "vetoed": False,
        "veto_justification": None,
        "execution_status": None,
        "created_at": _now(),
    }
    proposals[pid] = rec
    votes[pid] = []
    _log_tx("proposal_created", proposal_id=pid, proposer_id=body.proposer_id, category=body.category)
    return rec

@app.get("/v1/proposals")
def list_proposals(state: Optional[ProposalState] = None, category: Optional[ProposalCategory] = None):
    out = list(proposals.values())
    if state:
        out = [p for p in out if p["state"] == state]
    if category:
        out = [p for p in out if p["category"] == category]
    return out

@app.patch("/v1/proposals/{pid}/advance")
def advance_proposal(pid: str, target_state: ProposalState = Query(...)):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    p = proposals[pid]
    allowed = PROPOSAL_TRANSITIONS.get(p["state"], [])
    if target_state not in allowed:
        raise HTTPException(400, f"Cannot transition from {p['state']} to {target_state}")

    # If moving to passed/rejected, tally votes
    if target_state in ("passed", "rejected") and p["state"] == "voting":
        tally = _tally_votes(pid)
        if p["vetoed"]:
            target_state = "rejected"
        elif tally["approval_percentage"] >= p["approval_threshold"] and tally["participation_percentage"] >= p["quorum_percentage"]:
            target_state = "passed"
        else:
            target_state = "rejected"

    p["state"] = target_state
    if target_state == "enacted":
        p["execution_status"] = "pending"
    _log_tx("proposal_state_change", proposal_id=pid, new_state=target_state)
    return p

# ── Voting ───────────────────────────────────────────────────────────
def _get_effective_weight(voter_id: str) -> int:
    base = stakeholders.get(voter_id, {}).get("voting_weight", 1)
    # Add delegated weight
    delegated = sum(
        stakeholders.get(d["delegator_id"], {}).get("voting_weight", 0)
        for d in delegations.values()
        if d["delegate_id"] == voter_id
    )
    return base + delegated

def _tally_votes(pid: str) -> dict:
    v_list = votes.get(pid, [])
    total_weight = sum(s.get("voting_weight", 1) for s in stakeholders.values())
    for_weight = sum(v["weight"] for v in v_list if v["vote"] == "for")
    against_weight = sum(v["weight"] for v in v_list if v["vote"] == "against")
    participated_weight = sum(v["weight"] for v in v_list)
    return {
        "for": for_weight,
        "against": against_weight,
        "abstain": participated_weight - for_weight - against_weight,
        "total_weight": total_weight,
        "participation_percentage": round(participated_weight / max(total_weight, 1) * 100, 1),
        "approval_percentage": round(for_weight / max(participated_weight, 1) * 100, 1),
    }

@app.post("/v1/proposals/{pid}/vote")
def cast_vote(pid: str, body: VoteRequest):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    if proposals[pid]["state"] != "voting":
        raise HTTPException(400, "Proposal not in voting state")
    if body.voter_id not in stakeholders:
        raise HTTPException(404, "Voter not found")
    # Check voting tokens
    if balances[body.voter_id].get("voting", 0) < 1:
        raise HTTPException(400, "Voter needs at least 1 voting token")

    # Check no duplicate
    if any(v["voter_id"] == body.voter_id for v in votes[pid]):
        raise HTTPException(409, "Already voted")

    weight = _get_effective_weight(body.voter_id)
    vote_rec = {"voter_id": body.voter_id, "vote": body.vote, "weight": weight, "cast_at": _now()}
    votes[pid].append(vote_rec)
    _log_tx("vote_cast", proposal_id=pid, voter_id=body.voter_id, vote=body.vote, weight=weight)
    return {**vote_rec, "tally": _tally_votes(pid)}

# ── Veto ─────────────────────────────────────────────────────────────
@app.post("/v1/proposals/{pid}/veto")
def veto_proposal(pid: str, body: VetoRequest):
    if pid not in proposals:
        raise HTTPException(404, "Proposal not found")
    if body.vetoer_id not in stakeholders:
        raise HTTPException(404, "Vetoer not found")
    # Only regulators and board members can veto
    role = stakeholders[body.vetoer_id]["role"]
    if role not in ("regulator", "board_member"):
        raise HTTPException(403, "Only regulators and board members can veto")
    if balances[body.vetoer_id].get("veto", 0) < 1:
        raise HTTPException(400, "Vetoer needs at least 1 veto token")

    balances[body.vetoer_id]["veto"] -= 1
    proposals[pid]["vetoed"] = True
    proposals[pid]["veto_justification"] = body.justification
    _log_tx("veto", proposal_id=pid, vetoer_id=body.vetoer_id, justification=body.justification)
    return {"proposal_id": pid, "vetoed": True, "justification": body.justification}

# ── Delegation ───────────────────────────────────────────────────────
@app.post("/v1/delegations", status_code=201)
def create_delegation(body: DelegationCreate):
    if body.delegator_id not in stakeholders:
        raise HTTPException(404, "Delegator not found")
    if body.delegate_id not in stakeholders:
        raise HTTPException(404, "Delegate not found")
    if body.delegator_id == body.delegate_id:
        raise HTTPException(400, "Cannot delegate to self")

    did = str(uuid.uuid4())
    rec = {"id": did, **body.model_dump(), "active": True, "created_at": _now()}
    delegations[did] = rec
    _log_tx("delegation_created", delegation_id=did, delegator=body.delegator_id, delegate=body.delegate_id, topic=body.topic)
    return rec

@app.delete("/v1/delegations/{did}")
def revoke_delegation(did: str):
    if did not in delegations:
        raise HTTPException(404, "Delegation not found")
    delegations[did]["active"] = False
    _log_tx("delegation_revoked", delegation_id=did)
    return {"status": "revoked", "delegation_id": did}

# ── Ledger ───────────────────────────────────────────────────────────
@app.get("/v1/ledger")
def get_ledger(tx_type: Optional[str] = None, limit: int = Query(200, ge=1)):
    out = ledger
    if tx_type:
        out = [e for e in out if e["type"] == tx_type]
    return out[-limit:]

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    pl = list(proposals.values())
    by_state = {}
    for p in pl:
        by_state[p["state"]] = by_state.get(p["state"], 0) + 1
    by_category = {}
    for p in pl:
        by_category[p["category"]] = by_category.get(p["category"], 0) + 1
    total_tokens = {}
    for bal in balances.values():
        for tt, amt in bal.items():
            total_tokens[tt] = total_tokens.get(tt, 0) + amt
    total_votes = sum(len(v) for v in votes.values())
    vetoed = sum(1 for p in pl if p.get("vetoed"))
    return {
        "total_stakeholders": len(stakeholders),
        "total_proposals": len(pl),
        "proposals_by_state": by_state,
        "proposals_by_category": by_category,
        "token_supply": total_tokens,
        "total_votes_cast": total_votes,
        "proposals_vetoed": vetoed,
        "active_delegations": sum(1 for d in delegations.values() if d.get("active")),
        "ledger_entries": len(ledger),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9907)
