# Governance Token Ledger

**Phase 26 — Service 3 of 5 · Port `9907`**

Tokenised governance rights and voting system for multi-stakeholder AI
oversight with proposal lifecycle, weighted consensus mechanisms, delegation
chains, and transparent decision audit trails.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Stakeholder Registry** | Register stakeholders with role (founder/board_member/operator/auditor/community/regulator), organisation, voting_weight (1-100), delegation capability |
| **Token Allocation** | Governance tokens with token_type (voting/veto/proposal/delegation), balance tracking per stakeholder, mint/burn/transfer operations with full ledger history |
| **Proposal Lifecycle** | 7-state lifecycle: draft → submitted → discussion → voting → passed → enacted → archived (or rejected); configurable quorum_percentage + approval_threshold + voting_duration_hours |
| **Voting Mechanisms** | 4 voting types: simple_majority / supermajority (⅔) / weighted_consensus / ranked_choice; token-weighted votes; one-token-one-vote or quadratic voting options |
| **Delegation** | Liquid democracy: delegate voting power to another stakeholder per-topic or globally; delegation chains with max depth; revocable at any time |
| **Veto Power** | Designated veto holders (regulators/board) can block proposals; veto requires justification; override requires supermajority |
| **Proposal Categories** | 8 categories: policy_change / budget_allocation / system_deployment / access_modification / compliance_update / emergency_action / constitutional_amendment / community_initiative |
| **Execution Tracking** | Enacted proposals tracked through implementation: execution_status (pending/in_progress/completed/failed), responsible_party, deadline, verification |
| **Transparency** | Complete ledger of all token operations, votes, delegations, vetoes; immutable audit trail with timestamps and actor attribution |
| **Analytics** | Token distribution, voting participation rates, proposal outcomes, delegation network, veto frequency |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/stakeholders` | Register stakeholder |
| `GET` | `/v1/stakeholders` | List stakeholders |
| `POST` | `/v1/tokens/mint` | Mint governance tokens |
| `POST` | `/v1/tokens/transfer` | Transfer tokens |
| `GET` | `/v1/tokens/balances` | Token balances |
| `POST` | `/v1/proposals` | Create proposal |
| `GET` | `/v1/proposals` | List proposals (filter by state/category) |
| `PATCH` | `/v1/proposals/{id}/advance` | Advance proposal state |
| `POST` | `/v1/proposals/{id}/vote` | Cast vote |
| `POST` | `/v1/proposals/{id}/veto` | Exercise veto |
| `POST` | `/v1/delegations` | Delegate voting power |
| `DELETE` | `/v1/delegations/{id}` | Revoke delegation |
| `GET` | `/v1/ledger` | Full transaction ledger |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9907 --reload
```

> **Production note:** Replace in-memory ledger with blockchain or append-only database for immutability guarantees; add cryptographic signing for vote integrity.
