# Explainability Dashboard

**Phase 25 — Service 2 of 5 · Port `9901`**

Interactive decision explanation interface with multi-level abstraction,
causal chain visualisation, counterfactual reasoning, and audience-adaptive
explanation generation.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Decision Registry** | Record AI decisions with decision_type (classification/recommendation/action/prediction/escalation), model_id, input features, output, confidence, timestamp |
| **Multi-Level Abstraction** | 4 explanation levels: executive (one-sentence summary) → analyst (key factors + weights) → technical (full feature attribution) → audit (complete reasoning chain + model internals) |
| **Causal Chain Visualisation** | Build causal graphs: nodes (observations/inferences/decisions) with directed edges (causes/contributes_to/contradicts); topological ordering; critical path identification |
| **Feature Attribution** | Per-decision feature importance: SHAP-style attribution values (positive=pushes toward, negative=pushes away); top-K influential features; baseline comparison |
| **Counterfactual Reasoning** | "What-if" analysis: modify input features → recompute decision → show delta; minimal counterfactual (fewest changes to flip decision); plausibility scoring |
| **Audience Adaptation** | Tailor explanations to 4 audiences: executive/analyst/engineer/regulator; each gets domain-appropriate language, detail level, and relevant metrics |
| **Explanation Templates** | Pre-built templates for common decision types; customisable per organisation |
| **Feedback Loop** | Rate explanations (helpful/unclear/misleading); track explanation quality over time |
| **Analytics** | Decision volume by type/model, explanation quality ratings, counterfactual usage, audience distribution |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/decisions` | Record decision |
| `GET` | `/v1/decisions` | List decisions (filter by type/model/confidence) |
| `GET` | `/v1/decisions/{id}` | Get decision detail |
| `GET` | `/v1/decisions/{id}/explain` | Generate explanation at specified level |
| `POST` | `/v1/decisions/{id}/causal-chain` | Build causal chain |
| `GET` | `/v1/decisions/{id}/causal-chain` | Get causal chain |
| `POST` | `/v1/decisions/{id}/counterfactual` | Run counterfactual analysis |
| `POST` | `/v1/decisions/{id}/feedback` | Submit explanation feedback |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9901 --reload
```

> **Production note:** Replace simulated SHAP values with real model integration (SHAP/LIME) and add WebSocket streaming for interactive exploration.
