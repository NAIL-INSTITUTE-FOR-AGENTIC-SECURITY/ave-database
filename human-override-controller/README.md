# Human Override Controller

**Phase 25 — Service 3 of 5 · Port `9902`**

Structured human-in-the-loop intervention system with escalation protocols,
approval workflows, override audit trails, and configurable autonomy
boundaries.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Autonomy Boundaries** | Define boundaries per AI system: autonomy_level (full_auto/supervised/approval_required/human_only), risk_threshold (actions above this risk score require approval), auto_approve_below confidence threshold |
| **Override Requests** | AI systems request human override when: action exceeds risk threshold, confidence below auto-approve level, or flagged by policy; includes action_description, risk_score, confidence, urgency |
| **Approval Workflows** | 5-state workflow: pending → under_review → approved → rejected → expired; configurable timeout_minutes; multi-approver support with quorum |
| **Escalation Protocols** | 3-tier escalation: L1 (team lead, timeout 30min) → L2 (department head, timeout 15min) → L3 (executive, timeout 5min); auto-escalate on timeout |
| **Override Actions** | 4 override types: approve_as_is / approve_with_modifications / reject / defer; modifications captured as structured changes |
| **Intervention Log** | Complete audit trail: who overrode, when, why (justification required), original vs modified action, outcome tracking |
| **Autonomy Adjustment** | Dynamic autonomy tuning: increase autonomy after N successful auto-actions; decrease after overrides or failures; per-system tracking |
| **Bulk Operations** | Batch approve/reject pending requests by category; emergency halt (freeze all AI actions pending review) |
| **Analytics** | Override rates by system/type, approval latency, escalation frequency, autonomy level distribution, intervention outcomes |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/boundaries` | Define autonomy boundary |
| `GET` | `/v1/boundaries` | List boundaries |
| `POST` | `/v1/overrides` | Request override |
| `GET` | `/v1/overrides` | List overrides (filter by state/system/urgency) |
| `GET` | `/v1/overrides/{id}` | Get override detail |
| `POST` | `/v1/overrides/{id}/review` | Submit review decision |
| `POST` | `/v1/overrides/{id}/escalate` | Manually escalate |
| `POST` | `/v1/emergency-halt` | Freeze all AI actions |
| `POST` | `/v1/emergency-resume` | Resume after halt |
| `GET` | `/v1/interventions` | Full intervention log |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9902 --reload
```

> **Production note:** Replace in-memory stores with event-sourced database, add WebSocket notifications for real-time override alerts, integrate with PagerDuty/Slack for escalations.
