"""Collaborative Learning Broker — Phase 30 Service 2 · Port 9926"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random, math

app = FastAPI(title="Collaborative Learning Broker", version="0.30.2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class ParticipantType(str, Enum):
    endpoint_agent = "endpoint_agent"
    network_monitor = "network_monitor"
    cloud_sentinel = "cloud_sentinel"
    identity_guardian = "identity_guardian"
    threat_hunter = "threat_hunter"
    siem_collector = "siem_collector"

class PrivacyLevel(str, Enum):
    public = "public"
    anonymised = "anonymised"
    differential_privacy = "differential_privacy"
    encrypted = "encrypted"

class LearningMode(str, Enum):
    federated_averaging = "federated_averaging"
    secure_aggregation = "secure_aggregation"
    gossip_protocol = "gossip_protocol"
    split_learning = "split_learning"

class SessionState(str, Enum):
    created = "created"
    recruiting = "recruiting"
    training = "training"
    aggregating = "aggregating"
    validating = "validating"
    completed = "completed"
    failed = "failed"

SESS_TRANSITIONS = {
    "created": ["recruiting"],
    "recruiting": ["training"],
    "training": ["aggregating"],
    "aggregating": ["validating"],
    "validating": ["completed", "failed", "training"],
}

# ── Models ───────────────────────────────────────────────────────────
class ParticipantCreate(BaseModel):
    name: str
    participant_type: ParticipantType
    data_size_estimate: int = Field(10000, ge=100)
    privacy_level: PrivacyLevel = PrivacyLevel.anonymised
    trust_score: float = Field(0.8, ge=0, le=1)

class SessionCreate(BaseModel):
    name: str
    mode: LearningMode
    min_participants: int = Field(3, ge=2)
    max_participants: int = Field(20, ge=2)
    total_rounds: int = Field(10, ge=1, le=100)
    privacy_budget_epsilon: float = Field(5.0, ge=0.1, le=20)
    convergence_threshold: float = Field(0.001, ge=0.0001, le=0.1)
    description: str = ""

class RoundUpdate(BaseModel):
    participant_id: str
    gradient_magnitude: float = Field(0.5, ge=0)
    local_loss: float = Field(0.5, ge=0)
    local_accuracy: float = Field(0.7, ge=0, le=1)
    samples_used: int = Field(1000, ge=1)

# ── Stores ───────────────────────────────────────────────────────────
participants: dict[str, dict] = {}
sessions: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Aggregation ──────────────────────────────────────────────────────
def _aggregate_round(session: dict, round_num: int) -> dict:
    rnd = session["rounds"].get(round_num, {})
    updates = rnd.get("updates", [])
    if not updates:
        return {"error": "No updates for this round"}

    # Weighted aggregation by trust_score * data_weight
    total_weight = 0
    weighted_loss = 0
    weighted_acc = 0
    magnitudes = []

    for u in updates:
        p = participants.get(u["participant_id"], {})
        weight = p.get("trust_score", 0.5) * u["samples_used"]
        total_weight += weight
        weighted_loss += u["local_loss"] * weight
        weighted_acc += u["local_accuracy"] * weight
        magnitudes.append(u["gradient_magnitude"])

    avg_loss = weighted_loss / max(total_weight, 1)
    avg_acc = weighted_acc / max(total_weight, 1)

    # Poisoning detection: z-score on gradient magnitudes
    mean_mag = sum(magnitudes) / max(len(magnitudes), 1)
    std_mag = (sum((m - mean_mag) ** 2 for m in magnitudes) / max(len(magnitudes) - 1, 1)) ** 0.5 if len(magnitudes) > 1 else 0
    poisoning_suspects = []
    for u in updates:
        if std_mag > 0:
            z = abs(u["gradient_magnitude"] - mean_mag) / std_mag
            if z > 2.5:
                poisoning_suspects.append({
                    "participant_id": u["participant_id"],
                    "participant_name": participants.get(u["participant_id"], {}).get("name", "?"),
                    "z_score": round(z, 2),
                    "gradient_magnitude": u["gradient_magnitude"],
                })

    # Privacy cost
    privacy_cost = 0.3 + random.uniform(0, 0.2)  # simulated epsilon cost per round

    return {
        "round": round_num,
        "participants_contributed": len(updates),
        "aggregated_loss": round(avg_loss, 6),
        "aggregated_accuracy": round(avg_acc, 4),
        "total_samples": sum(u["samples_used"] for u in updates),
        "poisoning_suspects": poisoning_suspects,
        "privacy_cost_epsilon": round(privacy_cost, 3),
        "aggregated_at": _now(),
    }

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "collaborative-learning-broker",
        "status": "healthy",
        "version": "0.30.2",
        "participants": len(participants),
        "sessions": len(sessions),
    }

# ── Participants ─────────────────────────────────────────────────────
@app.post("/v1/participants", status_code=201)
def create_participant(body: ParticipantCreate):
    pid = str(uuid.uuid4())
    rec = {"id": pid, **body.model_dump(), "quarantined": False, "poisoning_flags": 0, "created_at": _now()}
    participants[pid] = rec
    return rec

@app.get("/v1/participants")
def list_participants(participant_type: Optional[ParticipantType] = None):
    out = list(participants.values())
    if participant_type:
        out = [p for p in out if p["participant_type"] == participant_type]
    return out

# ── Sessions ─────────────────────────────────────────────────────────
@app.post("/v1/sessions", status_code=201)
def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    rec = {
        "id": sid,
        **body.model_dump(),
        "state": "created",
        "enrolled_participants": [],
        "rounds": {},
        "global_model_version": 0,
        "global_loss_history": [],
        "global_accuracy_history": [],
        "privacy_budget_used": 0.0,
        "created_at": _now(),
    }
    sessions[sid] = rec
    return rec

@app.get("/v1/sessions")
def list_sessions(state: Optional[SessionState] = None):
    out = list(sessions.values())
    if state:
        out = [s for s in out if s["state"] == state]
    return [{k: v for k, v in s.items() if k != "rounds"} for s in out]

@app.get("/v1/sessions/{sid}")
def get_session(sid: str):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    return sessions[sid]

# ── Join ─────────────────────────────────────────────────────────────
@app.post("/v1/sessions/{sid}/join")
def join_session(sid: str, participant_id: str = Query(...)):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    if participant_id not in participants:
        raise HTTPException(404, "Participant not found")
    s = sessions[sid]
    if s["state"] not in ("created", "recruiting"):
        raise HTTPException(400, "Session is not recruiting")
    if participant_id in s["enrolled_participants"]:
        raise HTTPException(409, "Already enrolled")
    if participants[participant_id]["quarantined"]:
        raise HTTPException(403, "Participant is quarantined")
    if len(s["enrolled_participants"]) >= s["max_participants"]:
        raise HTTPException(400, "Session is full")

    s["enrolled_participants"].append(participant_id)
    s["state"] = "recruiting"
    return {"session_id": sid, "participant_id": participant_id, "enrolled_count": len(s["enrolled_participants"])}

# ── Advance ──────────────────────────────────────────────────────────
@app.patch("/v1/sessions/{sid}/advance")
def advance_session(sid: str, target_state: SessionState = Query(...)):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    s = sessions[sid]
    allowed = SESS_TRANSITIONS.get(s["state"], [])
    if target_state not in allowed:
        raise HTTPException(400, f"Cannot transition from {s['state']} to {target_state}")
    if target_state == "training" and len(s["enrolled_participants"]) < s["min_participants"]:
        raise HTTPException(400, f"Need at least {s['min_participants']} participants")
    s["state"] = target_state
    return s

# ── Round Submit ─────────────────────────────────────────────────────
@app.post("/v1/sessions/{sid}/rounds/{round_num}/submit")
def submit_update(sid: str, round_num: int, body: RoundUpdate):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    s = sessions[sid]
    if s["state"] != "training":
        raise HTTPException(400, "Session must be in training state")
    if body.participant_id not in s["enrolled_participants"]:
        raise HTTPException(403, "Participant not enrolled in this session")

    if round_num not in s["rounds"]:
        s["rounds"][round_num] = {"updates": [], "aggregation": None}
    rnd = s["rounds"][round_num]
    if any(u["participant_id"] == body.participant_id for u in rnd["updates"]):
        raise HTTPException(409, "Participant already submitted for this round")

    entry = {**body.model_dump(), "submitted_at": _now()}
    rnd["updates"].append(entry)
    return entry

# ── Aggregate ────────────────────────────────────────────────────────
@app.post("/v1/sessions/{sid}/rounds/{round_num}/aggregate")
def aggregate(sid: str, round_num: int):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    s = sessions[sid]

    result = _aggregate_round(s, round_num)
    if "error" in result:
        raise HTTPException(400, result["error"])

    s["rounds"][round_num]["aggregation"] = result
    s["global_model_version"] += 1
    s["global_loss_history"].append(result["aggregated_loss"])
    s["global_accuracy_history"].append(result["aggregated_accuracy"])
    s["privacy_budget_used"] = round(s["privacy_budget_used"] + result["privacy_cost_epsilon"], 3)
    s["state"] = "aggregating"

    # Flag poisoning suspects
    for suspect in result["poisoning_suspects"]:
        pid = suspect["participant_id"]
        if pid in participants:
            participants[pid]["poisoning_flags"] += 1
            if participants[pid]["poisoning_flags"] >= 3:
                participants[pid]["quarantined"] = True

    # Check if regression (rollback trigger)
    if len(s["global_loss_history"]) >= 2 and s["global_loss_history"][-1] > s["global_loss_history"][-2] * 1.1:
        result["regression_detected"] = True
        result["recommendation"] = "Consider rolling back to previous model version"
    else:
        result["regression_detected"] = False

    return result

# ── Convergence ──────────────────────────────────────────────────────
@app.get("/v1/sessions/{sid}/convergence")
def convergence(sid: str):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    s = sessions[sid]
    losses = s["global_loss_history"]

    if len(losses) < 2:
        return {"session_id": sid, "status": "insufficient_data", "rounds_completed": len(losses)}

    recent_deltas = [abs(losses[i] - losses[i - 1]) for i in range(1, len(losses))]
    avg_delta = sum(recent_deltas[-5:]) / min(len(recent_deltas), 5)
    converged = avg_delta < s["convergence_threshold"]

    # Divergence: loss increasing 3+ consecutive
    diverging = False
    if len(losses) >= 4:
        last3 = losses[-3:]
        diverging = all(last3[i] > last3[i - 1] for i in range(1, len(last3)))

    return {
        "session_id": sid,
        "rounds_completed": len(losses),
        "latest_loss": round(losses[-1], 6) if losses else None,
        "avg_recent_delta": round(avg_delta, 6),
        "convergence_threshold": s["convergence_threshold"],
        "converged": converged,
        "diverging": diverging,
        "status": "converged" if converged else ("diverging" if diverging else "training"),
        "loss_trajectory": [round(l, 6) for l in losses],
    }

# ── Privacy Budget ───────────────────────────────────────────────────
@app.get("/v1/sessions/{sid}/privacy")
def privacy_budget(sid: str):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    s = sessions[sid]
    remaining = round(s["privacy_budget_epsilon"] - s["privacy_budget_used"], 3)
    pct_used = round(s["privacy_budget_used"] / max(s["privacy_budget_epsilon"], 0.001) * 100, 1)
    exhaustion_risk = pct_used > 80

    estimated_rounds_remaining = 0
    if s["privacy_budget_used"] > 0 and s["global_model_version"] > 0:
        avg_cost = s["privacy_budget_used"] / s["global_model_version"]
        estimated_rounds_remaining = int(remaining / max(avg_cost, 0.001))

    return {
        "session_id": sid,
        "total_budget_epsilon": s["privacy_budget_epsilon"],
        "used_epsilon": s["privacy_budget_used"],
        "remaining_epsilon": remaining,
        "pct_used": pct_used,
        "exhaustion_risk": exhaustion_risk,
        "estimated_rounds_remaining": estimated_rounds_remaining,
    }

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    sl = list(sessions.values())
    by_mode = {}
    for s in sl:
        by_mode[s["mode"]] = by_mode.get(s["mode"], 0) + 1
    by_state = {}
    for s in sl:
        by_state[s["state"]] = by_state.get(s["state"], 0) + 1

    completed = [s for s in sl if s["state"] == "completed"]
    avg_rounds = round(sum(s["global_model_version"] for s in completed) / max(len(completed), 1), 1) if completed else 0

    total_poisoning = sum(p["poisoning_flags"] for p in participants.values())
    quarantined = sum(1 for p in participants.values() if p["quarantined"])

    return {
        "total_participants": len(participants),
        "quarantined_participants": quarantined,
        "total_sessions": len(sl),
        "by_mode": by_mode,
        "by_state": by_state,
        "completed_sessions": len(completed),
        "avg_rounds_to_completion": avg_rounds,
        "total_poisoning_flags": total_poisoning,
        "total_model_versions": sum(s["global_model_version"] for s in sl),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9926)
