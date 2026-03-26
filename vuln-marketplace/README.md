# 💰 AVE Vulnerability Marketplace

> Bounty platform for responsible disclosure of novel agentic AI vulnerabilities
> with reward tiers and verification pipeline.

**Phase 13 · Item 2 · Port 8701**

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       AVE VULNERABILITY MARKETPLACE                       │
├───────────┬──────────┬──────────┬──────────┬──────────┬────────────────────┤
│ Submission│ Triage   │ Verifi-  │ Bounty   │ Payout   │ Leaderboard       │
│ Portal    │ Queue    │ cation   │ Calculator│ Ledger  │ & Reputation      │
│           │          │ Pipeline │          │          │                   │
├───────────┴──────────┴──────────┴──────────┴──────────┴────────────────────┤
│                        RESPONSIBLE DISCLOSURE LAYER                       │
├───────────┬──────────┬──────────┬──────────┬──────────┬────────────────────┤
│ Embargo   │ Vendor   │ CVE/AVE  │ Comms    │ Legal    │ Public            │
│ Timer     │ Notify   │ Assign   │ Channel  │ Safe     │ Disclosure        │
│           │          │          │          │ Harbour  │                   │
└───────────┴──────────┴──────────┴──────────┴──────────┴────────────────────┘
```

## Bounty Tiers

| Tier | Severity | Base Reward (USD) | Multiplier Range |
|------|----------|-------------------|------------------|
| 🏆 **Platinum** | Critical (AVSS ≥ 9.0) | $10,000 | 1.0×–3.0× |
| 🥇 **Gold** | High (AVSS 7.0–8.9) | $5,000 | 1.0×–2.0× |
| 🥈 **Silver** | Medium (AVSS 4.0–6.9) | $2,000 | 1.0×–1.5× |
| 🥉 **Bronze** | Low (AVSS < 4.0) | $500 | 1.0× |

### Multipliers

- **Novel category** (first-in-class): ×2.0
- **Working exploit PoC**: ×1.5
- **Defence recommendation**: ×1.25
- **Multi-framework impact**: ×1.5
- **Real-world evidence**: ×1.75

## Key Features

1. **Responsible Disclosure Pipeline** — 90-day embargo with vendor notification, coordinated public disclosure
2. **Automated AVSS Scoring** — Submissions auto-scored against AVSS rubric
3. **Multi-Stage Verification** — Triage → Reproduce → Validate → Score → Reward
4. **Bounty Calculator** — Base reward × severity × novelty × impact multipliers
5. **Researcher Reputation** — Track record, accuracy rating, tier progression
6. **Vendor Safe Harbour** — Legal protection framework for good-faith researchers
7. **Payout Ledger** — Transparent, auditable reward tracking
8. **Leaderboard** — Hall of Fame with researcher rankings and statistics

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health |
| `POST` | `/v1/submissions` | Submit a vulnerability |
| `GET` | `/v1/submissions` | List submissions (filtered) |
| `GET` | `/v1/submissions/{id}` | Submission details |
| `PATCH` | `/v1/submissions/{id}/status` | Update submission status |
| `POST` | `/v1/submissions/{id}/verify` | Advance through verification |
| `GET` | `/v1/bounties` | List bounty payouts |
| `GET` | `/v1/bounties/calculate` | Calculate bounty for params |
| `POST` | `/v1/bounties/{submission_id}/approve` | Approve bounty payout |
| `GET` | `/v1/researchers` | Researcher leaderboard |
| `GET` | `/v1/researchers/{id}` | Researcher profile |
| `POST` | `/v1/researchers` | Register researcher |
| `GET` | `/v1/programmes` | List bounty programmes |
| `POST` | `/v1/programmes` | Create bounty programme |
| `GET` | `/v1/stats` | Marketplace statistics |
| `GET` | `/v1/disclosure-timeline/{id}` | Disclosure timeline for submission |

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 8701 --reload
```

Docs at http://localhost:8701/docs
