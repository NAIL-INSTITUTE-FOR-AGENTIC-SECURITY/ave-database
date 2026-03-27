"""Agent Reputation System — Phase 30 Service 3 · Port 9927"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random, math

app = FastAPI(title="Agent Reputation System", version="0.30.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class AgentType(str, Enum):
    detector = "detector"
    classifier = "classifier"
    responder = "responder"
    analyst = "analyst"
    scanner = "scanner"
    monitor = "monitor"
    orchestrator = "orchestrator"
    advisor = "advisor"

class EventType(str, Enum):
    correct_detection = "correct_detection"
    false_positive = "false_positive"
    false_negative = "false_negative"
    timely_response = "timely_response"
    delayed_response = "delayed_response"
    accurate_classification = "accurate_classification"
    inaccurate_classification = "inaccurate_classification"

# Positive vs negative events
POSITIVE_EVENTS = {"correct_detection", "timely_response", "accurate_classification"}
NEGATIVE_EVENTS = {"false_positive", "false_negative", "delayed_response", "inaccurate_classification"}

class ReputationTier(str, Enum):
    exemplary = "exemplary"
    trusted = "trusted"
    neutral = "neutral"
    suspect = "suspect"
    compromised = "compromised"

def _tier(score: float) -> str:
    if score >= 85:
        return "exemplary"
    elif score >= 70:
        return "trusted"
    elif score >= 50:
        return "neutral"
    elif score >= 30:
        return "suspect"
    return "compromised"

# ── Models ───────────────────────────────────────────────────────────
class AgentCreate(BaseModel):
    name: str
    agent_type: AgentType
    domain: str = "general"
    description: str = ""

class EventRecord(BaseModel):
    event_type: EventType
    magnitude: float = Field(0.5, ge=0, le=1)
    context: str = ""

# ── Stores ───────────────────────────────────────────────────────────
agents: dict[str, dict] = {}

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Reputation Calculation ───────────────────────────────────────────
def _calc_reputation(agent: dict) -> float:
    events = agent["events"]
    if not events:
        return agent["reputation"]

    # Exponential decay: recent events weighted more
    score = 50.0  # start from neutral
    decay = 0.95
    weight = 1.0

    for ev in reversed(events[-100:]):  # last 100 events
        delta = ev["magnitude"] * 5  # scale magnitude to 0-5 points
        if ev["event_type"] in POSITIVE_EVENTS:
            score += delta * weight
        else:
            score -= delta * weight * 1.2  # negative events slightly heavier
        weight *= decay

    return max(0, min(100, round(score, 1)))

def _trend(events: list[dict], window: int = 10) -> dict:
    if len(events) < 3:
        return {"direction": "insufficient_data", "slope": 0}

    recent = events[-window:]
    # Calculate reputation at each event point
    scores = []
    running = 50.0
    for ev in recent:
        delta = ev["magnitude"] * 5
        if ev["event_type"] in POSITIVE_EVENTS:
            running += delta
        else:
            running -= delta * 1.2
        running = max(0, min(100, running))
        scores.append(running)

    if len(scores) < 2:
        return {"direction": "stable", "slope": 0}

    slope = (scores[-1] - scores[0]) / len(scores)
    variance = sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)

    if variance > 100:
        direction = "volatile"
    elif slope > 0.5:
        direction = "improving"
    elif slope < -0.5:
        direction = "declining"
    else:
        direction = "stable"

    return {"direction": direction, "slope": round(slope, 3), "variance": round(variance, 2), "recent_scores": [round(s, 1) for s in scores]}

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "agent-reputation-system",
        "status": "healthy",
        "version": "0.30.3",
        "agents": len(agents),
    }

# ── Agents ───────────────────────────────────────────────────────────
@app.post("/v1/agents", status_code=201)
def create_agent(body: AgentCreate):
    aid = str(uuid.uuid4())
    rec = {
        "id": aid,
        **body.model_dump(),
        "reputation": 50.0,
        "tier": "neutral",
        "quarantined": False,
        "quarantine_reason": None,
        "events": [],
        "created_at": _now(),
    }
    agents[aid] = rec
    return {k: v for k, v in rec.items() if k != "events"}

@app.get("/v1/agents")
def list_agents(agent_type: Optional[AgentType] = None, tier: Optional[ReputationTier] = None):
    out = list(agents.values())
    if agent_type:
        out = [a for a in out if a["agent_type"] == agent_type]
    if tier:
        out = [a for a in out if a["tier"] == tier]
    return [{**{k: v for k, v in a.items() if k != "events"}, "event_count": len(a["events"])} for a in out]

@app.get("/v1/agents/{aid}")
def get_agent(aid: str):
    if aid not in agents:
        raise HTTPException(404, "Agent not found")
    a = agents[aid]
    return {**a, "event_count": len(a["events"]), "recent_events": a["events"][-20:]}

# ── Events ───────────────────────────────────────────────────────────
@app.post("/v1/agents/{aid}/events")
def record_event(aid: str, body: EventRecord):
    if aid not in agents:
        raise HTTPException(404, "Agent not found")
    a = agents[aid]
    entry = {"id": str(uuid.uuid4()), **body.model_dump(), "recorded_at": _now()}
    a["events"].append(entry)

    # Recalculate reputation
    a["reputation"] = _calc_reputation(a)
    a["tier"] = _tier(a["reputation"])

    # Auto-check for sudden drop
    if len(a["events"]) >= 5:
        recent_5_rep = _calc_reputation({**a, "events": a["events"][-5:]})
        older_5_rep = _calc_reputation({**a, "events": a["events"][-10:-5]}) if len(a["events"]) >= 10 else 50.0
        if older_5_rep - recent_5_rep > 15:
            entry["sudden_drop_alert"] = True

    # Probationary weight for quarantined agents
    if a["quarantined"]:
        entry["probationary"] = True
        entry["effective_weight"] = 0.3
    else:
        entry["effective_weight"] = 1.0

    return entry

# ── Trend ────────────────────────────────────────────────────────────
@app.get("/v1/agents/{aid}/trend")
def agent_trend(aid: str, window: int = Query(10, ge=3, le=50)):
    if aid not in agents:
        raise HTTPException(404, "Agent not found")
    a = agents[aid]
    t = _trend(a["events"], window)
    return {
        "agent_id": aid,
        "current_reputation": a["reputation"],
        "current_tier": a["tier"],
        "window": window,
        **t,
    }

# ── Anomaly Detection ────────────────────────────────────────────────
@app.get("/v1/agents/{aid}/anomalies")
def anomalies(aid: str):
    if aid not in agents:
        raise HTTPException(404, "Agent not found")
    a = agents[aid]
    anomalies_found = []

    # Check sudden drop
    if len(a["events"]) >= 10:
        recent_reps = []
        temp_events = []
        for ev in a["events"][-20:]:
            temp_events.append(ev)
            r = _calc_reputation({**a, "events": temp_events})
            recent_reps.append(r)
        if len(recent_reps) >= 2:
            max_drop = max(recent_reps[i] - recent_reps[i + 1] for i in range(len(recent_reps) - 1))
            if max_drop > 15:
                anomalies_found.append({"type": "sudden_drop", "severity": "high", "drop_magnitude": round(max_drop, 1)})

    # Erratic behaviour (high variance)
    t = _trend(a["events"])
    if t.get("variance", 0) > 150:
        anomalies_found.append({"type": "erratic_behaviour", "severity": "medium", "variance": t["variance"]})

    # High negative event ratio recently
    recent = a["events"][-20:]
    if recent:
        neg_ratio = sum(1 for e in recent if e["event_type"] in NEGATIVE_EVENTS) / len(recent)
        if neg_ratio > 0.7:
            anomalies_found.append({"type": "high_negative_ratio", "severity": "high", "ratio": round(neg_ratio, 2)})

    return {
        "agent_id": aid,
        "anomalies_detected": len(anomalies_found),
        "anomalies": anomalies_found,
        "recommendation": "quarantine" if any(a["severity"] == "high" for a in anomalies_found) else "monitor" if anomalies_found else "none",
    }

# ── Quarantine ───────────────────────────────────────────────────────
@app.patch("/v1/agents/{aid}/quarantine")
def toggle_quarantine(aid: str, quarantine: bool = Query(...), reason: str = Query("")):
    if aid not in agents:
        raise HTTPException(404, "Agent not found")
    a = agents[aid]
    a["quarantined"] = quarantine
    a["quarantine_reason"] = reason if quarantine else None
    return {k: v for k, v in a.items() if k != "events"}

# ── Rankings ─────────────────────────────────────────────────────────
@app.get("/v1/rankings")
def rankings(agent_type: Optional[AgentType] = None, limit: int = Query(20, ge=1, le=100)):
    out = list(agents.values())
    if agent_type:
        out = [a for a in out if a["agent_type"] == agent_type]

    ranked = sorted(out, key=lambda a: a["reputation"], reverse=True)
    total = len(ranked)
    result = []
    for i, a in enumerate(ranked[:limit]):
        percentile = round((1 - i / max(total, 1)) * 100, 1)
        result.append({
            "rank": i + 1,
            "agent_id": a["id"],
            "name": a["name"],
            "agent_type": a["agent_type"],
            "reputation": a["reputation"],
            "tier": a["tier"],
            "percentile": percentile,
            "quarantined": a["quarantined"],
        })
    return {"total_agents": total, "rankings": result}

# ── Compromise Scan ──────────────────────────────────────────────────
@app.get("/v1/compromise-scan")
def compromise_scan():
    suspects = []
    for a in agents.values():
        signals = 0
        reasons = []

        # Signal 1: Low reputation
        if a["reputation"] < 30:
            signals += 1
            reasons.append(f"Low reputation: {a['reputation']}")

        # Signal 2: Declining trend
        t = _trend(a["events"])
        if t["direction"] == "declining":
            signals += 1
            reasons.append(f"Declining trend (slope: {t['slope']})")

        # Signal 3: High recent negative ratio
        recent = a["events"][-10:]
        if recent:
            neg_ratio = sum(1 for e in recent if e["event_type"] in NEGATIVE_EVENTS) / len(recent)
            if neg_ratio > 0.6:
                signals += 1
                reasons.append(f"High negative ratio: {neg_ratio:.1%}")

        # Signal 4: Volatile behaviour
        if t.get("variance", 0) > 120:
            signals += 1
            reasons.append(f"Volatile (variance: {t.get('variance', 0)})")

        if signals >= 2:
            suspects.append({
                "agent_id": a["id"],
                "name": a["name"],
                "reputation": a["reputation"],
                "tier": a["tier"],
                "compromise_signals": signals,
                "reasons": reasons,
                "quarantined": a["quarantined"],
                "recommendation": "quarantine" if signals >= 3 else "investigate",
            })

    return {"scan_time": _now(), "agents_scanned": len(agents), "suspects": len(suspects), "results": sorted(suspects, key=lambda s: s["compromise_signals"], reverse=True)}

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    al = list(agents.values())
    by_tier = {}
    for a in al:
        by_tier[a["tier"]] = by_tier.get(a["tier"], 0) + 1
    by_type = {}
    for a in al:
        by_type[a["agent_type"]] = by_type.get(a["agent_type"], 0) + 1

    avg_rep_by_type = {}
    for at in set(a["agent_type"] for a in al):
        type_agents = [a for a in al if a["agent_type"] == at]
        avg_rep_by_type[at] = round(sum(a["reputation"] for a in type_agents) / len(type_agents), 1)

    total_events = sum(len(a["events"]) for a in al)
    quarantined = sum(1 for a in al if a["quarantined"])
    avg_rep = round(sum(a["reputation"] for a in al) / max(len(al), 1), 1) if al else 0

    return {
        "total_agents": len(al),
        "quarantined": quarantined,
        "by_tier": by_tier,
        "by_type": by_type,
        "avg_reputation": avg_rep,
        "avg_reputation_by_type": avg_rep_by_type,
        "total_events": total_events,
        "compromise_rate": round(quarantined / max(len(al), 1), 3),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9927)
