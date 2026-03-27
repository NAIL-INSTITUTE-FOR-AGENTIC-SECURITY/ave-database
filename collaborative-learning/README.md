# Collaborative Learning Tracker

**Phase 25 — Service 5 of 5 · Port `9904`**

Bi-directional learning system tracking how humans and AI agents improve
each other's performance over time with learning sessions, skill progression,
knowledge transfer metrics, and mutual improvement analytics.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Learner Registry** | Register human and AI learners with learner_type (human/ai), skill domains, current skill levels (0-100 per domain), learning_style (visual/textual/interactive/experiential for humans; supervised/reinforcement/few_shot/transfer for AI) |
| **Learning Sessions** | Create sessions with session_type (human_teaches_ai/ai_teaches_human/collaborative/peer_review/mentoring), participants, target skills, pre/post assessments |
| **Session Lifecycle** | 5-state workflow: scheduled → in_progress → assessment → completed → archived |
| **Skill Progression** | Track per-learner per-skill improvement: before/after scores per session, cumulative progress, learning velocity (improvement per hour), plateau detection |
| **Knowledge Transfer Metrics** | Measure transfer effectiveness: transfer_efficiency (skill_gain / time_invested), retention_rate (skill maintained after N days), applicability_score (skill applied in real tasks) |
| **Mutual Improvement Tracking** | For each human-AI pair: track how human feedback improves AI accuracy AND how AI assistance improves human speed/accuracy; net mutual benefit score |
| **Learning Paths** | Define ordered learning paths with prerequisites; track completion percentage; recommend next session based on skill gaps |
| **Insight Generation** | Auto-generate insights: "Human operators improve 15% faster when AI provides real-time guidance" style observations from session data |
| **Analytics** | Learning velocity by type/domain, transfer efficiency, session completion rates, mutual improvement trends, skill distribution |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/learners` | Register learner |
| `GET` | `/v1/learners` | List learners (filter by type/domain) |
| `GET` | `/v1/learners/{id}` | Get learner detail + skills |
| `POST` | `/v1/sessions` | Create learning session |
| `GET` | `/v1/sessions` | List sessions |
| `GET` | `/v1/sessions/{id}` | Get session detail |
| `PATCH` | `/v1/sessions/{id}/advance` | Advance session state |
| `POST` | `/v1/sessions/{id}/assess` | Record pre/post assessment |
| `GET` | `/v1/learners/{id}/progression` | Skill progression history |
| `GET` | `/v1/pairs/{a}/{b}/mutual` | Mutual improvement for a pair |
| `POST` | `/v1/insights` | Generate insights from data |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9904 --reload
```

> **Production note:** Replace in-memory stores with time-series database for skill progression tracking; integrate with LMS platforms for session management.
