# Cognitive Load Balancer

**Phase 25 — Service 1 of 5 · Port `9900`**

Adaptive task allocation engine that distributes work between human and AI
agents based on cognitive complexity scoring, fatigue modelling, expertise
matching, and real-time workload balancing.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Agent Registry** | Register human and AI agents with agent_type (human/ai/hybrid), expertise domains, max concurrent tasks, availability schedule, cognitive profile |
| **Cognitive Profiling** | Per-agent cognitive profile: processing_speed (0-100), working_memory_capacity (0-100), attention_span_minutes, stress_tolerance (0-1), preferred_task_types |
| **Fatigue Modelling** | Real-time fatigue tracking for human agents: fatigue_level 0-1 (increases with task load, decreases with rest), active_minutes tracking, rest_needed flag at >0.8, productivity multiplier (1 - fatigue×0.5) |
| **Task Ingestion** | Create tasks with cognitive_complexity (1-10), required_expertise domains, estimated_duration_minutes, priority (critical/high/medium/low), max_latency_minutes |
| **Task Lifecycle** | 6-state workflow: pending → assigned → in_progress → review → completed → failed |
| **Allocation Engine** | Multi-factor scoring: expertise_match (40%) + cognitive_fit (25%) + availability (20%) + fatigue_penalty (15%); assigns to highest-scoring available agent |
| **Workload Balancing** | Per-agent queue depth monitoring; rebalance endpoint redistributes overloaded queues; configurable max queue depth per agent |
| **Delegation Rules** | Configurable rules: AI-only for complexity ≤3, human-required for complexity ≥8, hybrid for 4-7; override per task |
| **Analytics** | Task volume by complexity/priority/state, agent utilisation rates, avg assignment latency, fatigue distribution, expertise coverage gaps |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/agents` | Register agent |
| `GET` | `/v1/agents` | List agents (filter by type/expertise/available) |
| `GET` | `/v1/agents/{id}` | Get agent detail with fatigue + workload |
| `POST` | `/v1/agents/{id}/heartbeat` | Update agent fatigue/status |
| `POST` | `/v1/tasks` | Create task |
| `GET` | `/v1/tasks` | List tasks (filter by state/priority/complexity) |
| `POST` | `/v1/tasks/{id}/assign` | Auto-assign task to best agent |
| `PATCH` | `/v1/tasks/{id}/advance` | Advance task state |
| `POST` | `/v1/rebalance` | Rebalance workload across agents |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9900 --reload
```

> **Production note:** Replace in-memory stores with Redis for real-time workload state and integrate with calendar APIs for availability scheduling.
