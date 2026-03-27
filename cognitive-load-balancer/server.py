"""Cognitive Load Balancer — Phase 25 Service 1 · Port 9900"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, math

app = FastAPI(title="Cognitive Load Balancer", version="0.25.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class AgentType(str, Enum):
    human = "human"
    ai = "ai"
    hybrid = "hybrid"

class TaskPriority(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class TaskState(str, Enum):
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    review = "review"
    completed = "completed"
    failed = "failed"

TASK_TRANSITIONS = {
    "pending": ["assigned"],
    "assigned": ["in_progress", "failed"],
    "in_progress": ["review", "failed"],
    "review": ["completed", "failed"],
}

# ── Models ───────────────────────────────────────────────────────────
class CognitiveProfile(BaseModel):
    processing_speed: float = Field(50, ge=0, le=100)
    working_memory_capacity: float = Field(50, ge=0, le=100)
    attention_span_minutes: int = Field(60, ge=5)
    stress_tolerance: float = Field(0.5, ge=0, le=1)
    preferred_task_types: list[str] = []

class AgentCreate(BaseModel):
    name: str
    agent_type: AgentType
    expertise_domains: list[str] = []
    max_concurrent_tasks: int = Field(5, ge=1)
    cognitive_profile: CognitiveProfile = CognitiveProfile()

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    cognitive_complexity: int = Field(5, ge=1, le=10)
    required_expertise: list[str] = []
    estimated_duration_minutes: int = Field(30, ge=1)
    priority: TaskPriority = TaskPriority.medium
    max_latency_minutes: int = Field(120, ge=1)

# ── Stores ───────────────────────────────────────────────────────────
agents: dict[str, dict] = {}
tasks: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "cognitive-load-balancer",
        "status": "healthy",
        "version": "0.25.1",
        "agents": len(agents),
        "tasks": len(tasks),
    }

# ── Agent CRUD ───────────────────────────────────────────────────────
@app.post("/v1/agents", status_code=201)
def create_agent(body: AgentCreate):
    aid = str(uuid.uuid4())
    rec = {
        "id": aid,
        **body.model_dump(),
        "fatigue_level": 0.0,
        "active_minutes": 0,
        "assigned_tasks": [],
        "status": "available",
        "created_at": _now(),
        "last_heartbeat": _now(),
    }
    agents[aid] = rec
    return rec

@app.get("/v1/agents")
def list_agents(
    agent_type: Optional[AgentType] = None,
    expertise: Optional[str] = None,
    available: Optional[bool] = None,
):
    out = list(agents.values())
    if agent_type:
        out = [a for a in out if a["agent_type"] == agent_type]
    if expertise:
        out = [a for a in out if expertise in a["expertise_domains"]]
    if available is not None:
        out = [a for a in out if (a["status"] == "available") == available]
    return out

@app.get("/v1/agents/{aid}")
def get_agent(aid: str):
    if aid not in agents:
        raise HTTPException(404, "Agent not found")
    a = agents[aid]
    a["queue_depth"] = len(a["assigned_tasks"])
    a["rest_needed"] = a["fatigue_level"] > 0.8
    a["productivity_multiplier"] = round(1 - a["fatigue_level"] * 0.5, 3)
    return a

@app.post("/v1/agents/{aid}/heartbeat")
def heartbeat(aid: str, fatigue_delta: float = 0.0, active_minutes_delta: int = 0):
    if aid not in agents:
        raise HTTPException(404, "Agent not found")
    a = agents[aid]
    a["fatigue_level"] = max(0.0, min(1.0, a["fatigue_level"] + fatigue_delta))
    a["active_minutes"] += active_minutes_delta
    a["last_heartbeat"] = _now()
    if a["fatigue_level"] > 0.8:
        a["status"] = "fatigued"
    return {"status": "ok", "fatigue_level": a["fatigue_level"]}

# ── Task CRUD ────────────────────────────────────────────────────────
@app.post("/v1/tasks", status_code=201)
def create_task(body: TaskCreate):
    tid = str(uuid.uuid4())
    rec = {
        "id": tid,
        **body.model_dump(),
        "state": "pending",
        "assigned_agent_id": None,
        "created_at": _now(),
        "assigned_at": None,
        "completed_at": None,
    }
    tasks[tid] = rec
    return rec

@app.get("/v1/tasks")
def list_tasks(
    state: Optional[TaskState] = None,
    priority: Optional[TaskPriority] = None,
    min_complexity: Optional[int] = None,
    max_complexity: Optional[int] = None,
):
    out = list(tasks.values())
    if state:
        out = [t for t in out if t["state"] == state]
    if priority:
        out = [t for t in out if t["priority"] == priority]
    if min_complexity is not None:
        out = [t for t in out if t["cognitive_complexity"] >= min_complexity]
    if max_complexity is not None:
        out = [t for t in out if t["cognitive_complexity"] <= max_complexity]
    return out

# ── Auto-assign ──────────────────────────────────────────────────────
def _score_agent(agent: dict, task: dict) -> float:
    # Expertise match (40%)
    req = set(task["required_expertise"])
    have = set(agent["expertise_domains"])
    expertise = len(req & have) / max(len(req), 1)

    # Cognitive fit (25%)
    cp = agent["cognitive_profile"]
    complexity_fit = 1 - abs(task["cognitive_complexity"] - cp["processing_speed"] / 10) / 10
    cognitive = max(0, complexity_fit)

    # Availability (20%)
    queue = len(agent["assigned_tasks"])
    avail = max(0, 1 - queue / agent["max_concurrent_tasks"])

    # Fatigue penalty (15%)
    fatigue_pen = 1 - agent["fatigue_level"]

    return expertise * 0.4 + cognitive * 0.25 + avail * 0.2 + fatigue_pen * 0.15

@app.post("/v1/tasks/{tid}/assign")
def assign_task(tid: str):
    if tid not in tasks:
        raise HTTPException(404, "Task not found")
    t = tasks[tid]
    if t["state"] != "pending":
        raise HTTPException(400, f"Task in state {t['state']}, expected pending")

    available = [a for a in agents.values() if a["status"] in ("available",) and len(a["assigned_tasks"]) < a["max_concurrent_tasks"]]
    if not available:
        raise HTTPException(409, "No available agents")

    scored = sorted(available, key=lambda a: _score_agent(a, t), reverse=True)
    best = scored[0]
    t["state"] = "assigned"
    t["assigned_agent_id"] = best["id"]
    t["assigned_at"] = _now()
    best["assigned_tasks"].append(tid)
    return {"task_id": tid, "assigned_to": best["id"], "score": round(_score_agent(best, t), 4)}

@app.patch("/v1/tasks/{tid}/advance")
def advance_task(tid: str, target_state: TaskState = Query(...)):
    if tid not in tasks:
        raise HTTPException(404, "Task not found")
    t = tasks[tid]
    allowed = TASK_TRANSITIONS.get(t["state"], [])
    if target_state not in allowed:
        raise HTTPException(400, f"Cannot transition from {t['state']} to {target_state}")
    t["state"] = target_state
    if target_state in ("completed", "failed"):
        t["completed_at"] = _now()
        if t["assigned_agent_id"] and t["assigned_agent_id"] in agents:
            ag = agents[t["assigned_agent_id"]]
            if tid in ag["assigned_tasks"]:
                ag["assigned_tasks"].remove(tid)
    return t

# ── Rebalance ────────────────────────────────────────────────────────
@app.post("/v1/rebalance")
def rebalance():
    moved = 0
    overloaded = [a for a in agents.values() if len(a["assigned_tasks"]) > a["max_concurrent_tasks"] * 0.8]
    underloaded = [a for a in agents.values() if len(a["assigned_tasks"]) < a["max_concurrent_tasks"] * 0.3 and a["status"] == "available"]
    for ol in overloaded:
        while len(ol["assigned_tasks"]) > a["max_concurrent_tasks"] * 0.5 and underloaded:
            tid = ol["assigned_tasks"].pop()
            target = underloaded[0]
            target["assigned_tasks"].append(tid)
            tasks[tid]["assigned_agent_id"] = target["id"]
            moved += 1
            if len(target["assigned_tasks"]) >= target["max_concurrent_tasks"] * 0.7:
                underloaded.pop(0)
    return {"moved": moved}

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    tl = list(tasks.values())
    al = list(agents.values())
    by_state = {}
    for t in tl:
        by_state[t["state"]] = by_state.get(t["state"], 0) + 1
    by_priority = {}
    for t in tl:
        by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1
    avg_fatigue = sum(a["fatigue_level"] for a in al) / max(len(al), 1)
    avg_queue = sum(len(a["assigned_tasks"]) for a in al) / max(len(al), 1)
    return {
        "total_agents": len(al),
        "total_tasks": len(tl),
        "tasks_by_state": by_state,
        "tasks_by_priority": by_priority,
        "avg_agent_fatigue": round(avg_fatigue, 3),
        "avg_queue_depth": round(avg_queue, 2),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9900)
