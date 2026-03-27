"""Collaborative Learning Tracker — Phase 25 Service 5 · Port 9904"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random

app = FastAPI(title="Collaborative Learning Tracker", version="0.25.5")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class LearnerType(str, Enum):
    human = "human"
    ai = "ai"

class LearningStyle(str, Enum):
    visual = "visual"
    textual = "textual"
    interactive = "interactive"
    experiential = "experiential"
    supervised = "supervised"
    reinforcement = "reinforcement"
    few_shot = "few_shot"
    transfer = "transfer"

class SessionType(str, Enum):
    human_teaches_ai = "human_teaches_ai"
    ai_teaches_human = "ai_teaches_human"
    collaborative = "collaborative"
    peer_review = "peer_review"
    mentoring = "mentoring"

class SessionState(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    assessment = "assessment"
    completed = "completed"
    archived = "archived"

SESSION_TRANSITIONS = {
    "scheduled": ["in_progress"],
    "in_progress": ["assessment"],
    "assessment": ["completed"],
    "completed": ["archived"],
}

# ── Models ───────────────────────────────────────────────────────────
class SkillLevel(BaseModel):
    domain: str
    level: float = Field(50.0, ge=0, le=100)

class LearnerCreate(BaseModel):
    name: str
    learner_type: LearnerType
    learning_style: LearningStyle
    skill_domains: list[SkillLevel] = []

class SessionCreate(BaseModel):
    session_type: SessionType
    participant_ids: list[str]
    target_skills: list[str] = []
    description: str = ""

class AssessmentCreate(BaseModel):
    learner_id: str
    skill_domain: str
    score: float = Field(ge=0, le=100)
    phase: str = Field("pre", pattern="^(pre|post)$")

# ── Stores ───────────────────────────────────────────────────────────
learners: dict[str, dict] = {}
sessions: dict[str, dict] = {}
assessments: list[dict] = []
insights: list[dict] = []

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "collaborative-learning-tracker",
        "status": "healthy",
        "version": "0.25.5",
        "learners": len(learners),
        "sessions": len(sessions),
    }

# ── Learner CRUD ─────────────────────────────────────────────────────
@app.post("/v1/learners", status_code=201)
def create_learner(body: LearnerCreate):
    lid = str(uuid.uuid4())
    skills = {s.domain: s.level for s in body.skill_domains}
    rec = {
        "id": lid,
        "name": body.name,
        "learner_type": body.learner_type,
        "learning_style": body.learning_style,
        "skills": skills,
        "progression_history": [],
        "sessions_completed": 0,
        "total_learning_hours": 0.0,
        "created_at": _now(),
    }
    learners[lid] = rec
    return rec

@app.get("/v1/learners")
def list_learners(learner_type: Optional[LearnerType] = None, domain: Optional[str] = None):
    out = list(learners.values())
    if learner_type:
        out = [l for l in out if l["learner_type"] == learner_type]
    if domain:
        out = [l for l in out if domain in l["skills"]]
    return out

@app.get("/v1/learners/{lid}")
def get_learner(lid: str):
    if lid not in learners:
        raise HTTPException(404, "Learner not found")
    return learners[lid]

# ── Session CRUD ─────────────────────────────────────────────────────
@app.post("/v1/sessions", status_code=201)
def create_session(body: SessionCreate):
    for pid in body.participant_ids:
        if pid not in learners:
            raise HTTPException(404, f"Learner {pid} not found")
    sid = str(uuid.uuid4())
    rec = {
        "id": sid,
        **body.model_dump(),
        "state": "scheduled",
        "assessments": {"pre": {}, "post": {}},
        "created_at": _now(),
        "started_at": None,
        "completed_at": None,
    }
    sessions[sid] = rec
    return rec

@app.get("/v1/sessions")
def list_sessions(session_type: Optional[SessionType] = None, state: Optional[SessionState] = None):
    out = list(sessions.values())
    if session_type:
        out = [s for s in out if s["session_type"] == session_type]
    if state:
        out = [s for s in out if s["state"] == state]
    return out

@app.get("/v1/sessions/{sid}")
def get_session(sid: str):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    return sessions[sid]

@app.patch("/v1/sessions/{sid}/advance")
def advance_session(sid: str, target_state: SessionState = Query(...)):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    s = sessions[sid]
    allowed = SESSION_TRANSITIONS.get(s["state"], [])
    if target_state not in allowed:
        raise HTTPException(400, f"Cannot transition from {s['state']} to {target_state}")
    s["state"] = target_state
    if target_state == "in_progress":
        s["started_at"] = _now()
    if target_state == "completed":
        s["completed_at"] = _now()
        # Update learner stats
        for pid in s["participant_ids"]:
            if pid in learners:
                learners[pid]["sessions_completed"] += 1
                learners[pid]["total_learning_hours"] += 1.0  # placeholder
                # Update skills from post-assessments
                for domain, score in s["assessments"].get("post", {}).get(pid, {}).items():
                    old = learners[pid]["skills"].get(domain, 50.0)
                    learners[pid]["skills"][domain] = score
                    learners[pid]["progression_history"].append({
                        "session_id": sid,
                        "domain": domain,
                        "before": old,
                        "after": score,
                        "delta": round(score - old, 2),
                        "timestamp": _now(),
                    })
    return s

# ── Assessments ──────────────────────────────────────────────────────
@app.post("/v1/sessions/{sid}/assess", status_code=201)
def record_assessment(sid: str, body: AssessmentCreate):
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    s = sessions[sid]
    if body.learner_id not in s["participant_ids"]:
        raise HTTPException(400, "Learner not a participant in this session")

    phase_key = body.phase
    if body.learner_id not in s["assessments"][phase_key]:
        s["assessments"][phase_key][body.learner_id] = {}
    s["assessments"][phase_key][body.learner_id][body.skill_domain] = body.score

    rec = {"session_id": sid, **body.model_dump(), "recorded_at": _now()}
    assessments.append(rec)
    return rec

# ── Skill Progression ───────────────────────────────────────────────
@app.get("/v1/learners/{lid}/progression")
def skill_progression(lid: str, domain: Optional[str] = None):
    if lid not in learners:
        raise HTTPException(404, "Learner not found")
    history = learners[lid]["progression_history"]
    if domain:
        history = [h for h in history if h["domain"] == domain]

    # Compute velocity
    if len(history) >= 2:
        total_delta = sum(h["delta"] for h in history)
        velocity = round(total_delta / len(history), 3)
    else:
        velocity = 0.0

    # Plateau detection
    recent = history[-5:] if len(history) >= 5 else history
    plateau = all(abs(h["delta"]) < 1.0 for h in recent) if recent else False

    return {
        "learner_id": lid,
        "current_skills": learners[lid]["skills"],
        "history": history,
        "velocity": velocity,
        "plateau_detected": plateau,
    }

# ── Mutual Improvement ──────────────────────────────────────────────
@app.get("/v1/pairs/{a_id}/{b_id}/mutual")
def mutual_improvement(a_id: str, b_id: str):
    if a_id not in learners or b_id not in learners:
        raise HTTPException(404, "One or both learners not found")

    # Find shared sessions
    shared = [s for s in sessions.values() if a_id in s["participant_ids"] and b_id in s["participant_ids"] and s["state"] == "completed"]

    a_gains = []
    b_gains = []
    for s in shared:
        for domain, score in s["assessments"].get("post", {}).get(a_id, {}).items():
            pre = s["assessments"].get("pre", {}).get(a_id, {}).get(domain, 50.0)
            a_gains.append(score - pre)
        for domain, score in s["assessments"].get("post", {}).get(b_id, {}).items():
            pre = s["assessments"].get("pre", {}).get(b_id, {}).get(domain, 50.0)
            b_gains.append(score - pre)

    a_avg = round(sum(a_gains) / max(len(a_gains), 1), 2)
    b_avg = round(sum(b_gains) / max(len(b_gains), 1), 2)

    return {
        "pair": [a_id, b_id],
        "shared_sessions": len(shared),
        "learner_a": {"id": a_id, "name": learners[a_id]["name"], "avg_gain": a_avg},
        "learner_b": {"id": b_id, "name": learners[b_id]["name"], "avg_gain": b_avg},
        "net_mutual_benefit": round(a_avg + b_avg, 2),
    }

# ── Insights ─────────────────────────────────────────────────────────
@app.post("/v1/insights")
def generate_insights():
    generated = []

    # Insight: best session type
    type_gains = {}
    for s in sessions.values():
        if s["state"] != "completed":
            continue
        gains = []
        for pid in s["participant_ids"]:
            for domain, score in s["assessments"].get("post", {}).get(pid, {}).items():
                pre = s["assessments"].get("pre", {}).get(pid, {}).get(domain, 50.0)
                gains.append(score - pre)
        if gains:
            avg = sum(gains) / len(gains)
            if s["session_type"] not in type_gains:
                type_gains[s["session_type"]] = []
            type_gains[s["session_type"]].append(avg)

    for stype, gains in type_gains.items():
        avg = round(sum(gains) / len(gains), 2)
        generated.append({
            "type": "session_type_effectiveness",
            "insight": f"Session type '{stype}' yields avg +{avg} skill improvement per session",
            "data": {"session_type": stype, "avg_gain": avg, "sessions_counted": len(gains)},
            "generated_at": _now(),
        })

    # Insight: learner type comparison
    human_progress = [l for l in learners.values() if l["learner_type"] == "human" and l["progression_history"]]
    ai_progress = [l for l in learners.values() if l["learner_type"] == "ai" and l["progression_history"]]

    if human_progress:
        h_avg = sum(sum(h["delta"] for h in l["progression_history"]) / len(l["progression_history"]) for l in human_progress) / len(human_progress)
        generated.append({
            "type": "human_learning_rate",
            "insight": f"Human learners improve at avg {round(h_avg, 2)} points/session",
            "data": {"avg_delta": round(h_avg, 2), "learner_count": len(human_progress)},
            "generated_at": _now(),
        })

    if ai_progress:
        a_avg = sum(sum(h["delta"] for h in l["progression_history"]) / len(l["progression_history"]) for l in ai_progress) / len(ai_progress)
        generated.append({
            "type": "ai_learning_rate",
            "insight": f"AI learners improve at avg {round(a_avg, 2)} points/session",
            "data": {"avg_delta": round(a_avg, 2), "learner_count": len(ai_progress)},
            "generated_at": _now(),
        })

    insights.extend(generated)
    return {"generated": len(generated), "insights": generated}

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    sl = list(sessions.values())
    ll = list(learners.values())
    by_state = {}
    for s in sl:
        by_state[s["state"]] = by_state.get(s["state"], 0) + 1
    by_type = {}
    for s in sl:
        by_type[s["session_type"]] = by_type.get(s["session_type"], 0) + 1
    by_learner_type = {}
    for l in ll:
        by_learner_type[l["learner_type"]] = by_learner_type.get(l["learner_type"], 0) + 1

    total_sessions_completed = sum(1 for s in sl if s["state"] == "completed")
    total_hours = sum(l["total_learning_hours"] for l in ll)
    return {
        "total_learners": len(ll),
        "learners_by_type": by_learner_type,
        "total_sessions": len(sl),
        "sessions_by_state": by_state,
        "sessions_by_type": by_type,
        "sessions_completed": total_sessions_completed,
        "total_learning_hours": round(total_hours, 1),
        "total_assessments": len(assessments),
        "total_insights": len(insights),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9904)
