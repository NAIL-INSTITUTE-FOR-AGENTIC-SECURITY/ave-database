"""Explainability Dashboard — Phase 25 Service 2 · Port 9901"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, random, math

app = FastAPI(title="Explainability Dashboard", version="0.25.2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class DecisionType(str, Enum):
    classification = "classification"
    recommendation = "recommendation"
    action = "action"
    prediction = "prediction"
    escalation = "escalation"

class ExplanationLevel(str, Enum):
    executive = "executive"
    analyst = "analyst"
    technical = "technical"
    audit = "audit"

class FeedbackRating(str, Enum):
    helpful = "helpful"
    unclear = "unclear"
    misleading = "misleading"

# ── Models ───────────────────────────────────────────────────────────
class FeatureAttribution(BaseModel):
    feature_name: str
    value: float
    attribution: float = Field(0.0, description="SHAP-style attribution")
    direction: str = "positive"

class DecisionCreate(BaseModel):
    decision_type: DecisionType
    model_id: str
    input_features: dict = {}
    output: str
    confidence: float = Field(0.5, ge=0, le=1)
    context: str = ""

class CounterfactualRequest(BaseModel):
    modified_features: dict = {}

class FeedbackCreate(BaseModel):
    rating: FeedbackRating
    audience: ExplanationLevel = ExplanationLevel.analyst
    comment: str = ""

# ── Stores ───────────────────────────────────────────────────────────
decisions: dict[str, dict] = {}
causal_chains: dict[str, dict] = {}
feedbacks: list[dict] = []

def _now():
    return datetime.now(timezone.utc).isoformat()

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "explainability-dashboard",
        "status": "healthy",
        "version": "0.25.2",
        "decisions": len(decisions),
        "feedbacks": len(feedbacks),
    }

# ── Decision CRUD ────────────────────────────────────────────────────
@app.post("/v1/decisions", status_code=201)
def create_decision(body: DecisionCreate):
    did = str(uuid.uuid4())
    # Simulate feature attributions
    attrs = []
    for fname, fval in body.input_features.items():
        attr_val = round(random.uniform(-1, 1), 4)
        attrs.append({
            "feature_name": fname,
            "value": fval,
            "attribution": attr_val,
            "direction": "positive" if attr_val > 0 else "negative",
        })
    attrs.sort(key=lambda x: abs(x["attribution"]), reverse=True)

    rec = {
        "id": did,
        **body.model_dump(),
        "feature_attributions": attrs,
        "created_at": _now(),
    }
    decisions[did] = rec
    return rec

@app.get("/v1/decisions")
def list_decisions(
    decision_type: Optional[DecisionType] = None,
    model_id: Optional[str] = None,
    min_confidence: Optional[float] = None,
):
    out = list(decisions.values())
    if decision_type:
        out = [d for d in out if d["decision_type"] == decision_type]
    if model_id:
        out = [d for d in out if d["model_id"] == model_id]
    if min_confidence is not None:
        out = [d for d in out if d["confidence"] >= min_confidence]
    return out

@app.get("/v1/decisions/{did}")
def get_decision(did: str):
    if did not in decisions:
        raise HTTPException(404, "Decision not found")
    return decisions[did]

# ── Explanation Generation ───────────────────────────────────────────
def _generate_explanation(d: dict, level: ExplanationLevel) -> dict:
    attrs = d["feature_attributions"]
    top3 = attrs[:3] if attrs else []
    top_names = [a["feature_name"] for a in top3]

    if level == ExplanationLevel.executive:
        text = (
            f"The AI ({d['model_id']}) made a {d['decision_type']} decision: "
            f"\"{d['output']}\" with {d['confidence']:.0%} confidence. "
            f"Key factors: {', '.join(top_names) or 'N/A'}."
        )
        return {"level": level, "summary": text}

    if level == ExplanationLevel.analyst:
        return {
            "level": level,
            "summary": f"{d['decision_type'].title()} → {d['output']}",
            "confidence": d["confidence"],
            "top_factors": top3,
            "factor_count": len(attrs),
        }

    if level == ExplanationLevel.technical:
        return {
            "level": level,
            "model_id": d["model_id"],
            "input_features": d["input_features"],
            "output": d["output"],
            "confidence": d["confidence"],
            "all_attributions": attrs,
        }

    # audit
    return {
        "level": level,
        "decision_id": d["id"],
        "model_id": d["model_id"],
        "timestamp": d["created_at"],
        "input_features": d["input_features"],
        "output": d["output"],
        "confidence": d["confidence"],
        "all_attributions": attrs,
        "causal_chain": causal_chains.get(d["id"]),
        "context": d.get("context", ""),
    }

@app.get("/v1/decisions/{did}/explain")
def explain_decision(did: str, level: ExplanationLevel = ExplanationLevel.analyst):
    if did not in decisions:
        raise HTTPException(404, "Decision not found")
    return _generate_explanation(decisions[did], level)

# ── Causal Chain ─────────────────────────────────────────────────────
@app.post("/v1/decisions/{did}/causal-chain")
def build_causal_chain(did: str):
    if did not in decisions:
        raise HTTPException(404, "Decision not found")
    d = decisions[did]
    nodes = []
    edges = []
    # Build chain from features → inference → decision
    for i, attr in enumerate(d["feature_attributions"]):
        nid = f"obs_{i}"
        nodes.append({"id": nid, "type": "observation", "label": attr["feature_name"], "value": attr["value"]})
        edges.append({"from": nid, "to": "inference_0", "relation": "contributes_to", "weight": attr["attribution"]})

    nodes.append({"id": "inference_0", "type": "inference", "label": f"Combined signal ({d['confidence']:.0%})"})
    edges.append({"from": "inference_0", "to": "decision_0", "relation": "causes"})
    nodes.append({"id": "decision_0", "type": "decision", "label": d["output"]})

    chain = {
        "decision_id": did,
        "nodes": nodes,
        "edges": edges,
        "critical_path": ["decision_0", "inference_0"] + [f"obs_{i}" for i in range(min(3, len(d["feature_attributions"])))],
        "built_at": _now(),
    }
    causal_chains[did] = chain
    return chain

@app.get("/v1/decisions/{did}/causal-chain")
def get_causal_chain(did: str):
    if did not in causal_chains:
        raise HTTPException(404, "Causal chain not built yet")
    return causal_chains[did]

# ── Counterfactual ───────────────────────────────────────────────────
@app.post("/v1/decisions/{did}/counterfactual")
def counterfactual(did: str, body: CounterfactualRequest):
    if did not in decisions:
        raise HTTPException(404, "Decision not found")
    d = decisions[did]
    original_features = dict(d["input_features"])
    modified_features = {**original_features, **body.modified_features}
    changes = {k: {"original": original_features.get(k), "modified": v} for k, v in body.modified_features.items()}

    # Simulate re-decision
    delta_confidence = sum(random.uniform(-0.1, 0.1) for _ in body.modified_features) 
    new_confidence = max(0, min(1, d["confidence"] + delta_confidence))
    flipped = new_confidence < 0.5 and d["confidence"] >= 0.5

    return {
        "decision_id": did,
        "original_output": d["output"],
        "counterfactual_output": d["output"] if not flipped else f"NOT {d['output']}",
        "original_confidence": d["confidence"],
        "counterfactual_confidence": round(new_confidence, 4),
        "changes": changes,
        "decision_flipped": flipped,
        "plausibility_score": round(random.uniform(0.5, 1.0), 3),
    }

# ── Feedback ─────────────────────────────────────────────────────────
@app.post("/v1/decisions/{did}/feedback", status_code=201)
def submit_feedback(did: str, body: FeedbackCreate):
    if did not in decisions:
        raise HTTPException(404, "Decision not found")
    fb = {"decision_id": did, **body.model_dump(), "created_at": _now()}
    feedbacks.append(fb)
    return fb

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    dl = list(decisions.values())
    by_type = {}
    for d in dl:
        by_type[d["decision_type"]] = by_type.get(d["decision_type"], 0) + 1
    by_model = {}
    for d in dl:
        by_model[d["model_id"]] = by_model.get(d["model_id"], 0) + 1
    fb_ratings = {}
    for f in feedbacks:
        fb_ratings[f["rating"]] = fb_ratings.get(f["rating"], 0) + 1
    return {
        "total_decisions": len(dl),
        "by_type": by_type,
        "by_model": by_model,
        "total_feedbacks": len(feedbacks),
        "feedback_ratings": fb_ratings,
        "causal_chains_built": len(causal_chains),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9901)
