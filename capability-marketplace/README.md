# Agent Capability Marketplace

**Phase 22 — Service 3 of 5 · Port `9602`**

Curated registry of vetted agent capabilities with trust scoring, dependency
analysis, supply-chain attestation, and secure capability distribution.

---

## Core Concepts

### Capabilities
A **capability** is a discrete, composable unit of agent functionality —
tool use, reasoning strategy, integration adapter, or security control.

### Trust Scoring (0–100)
Trust is computed from multiple signals:
| Factor | Weight | Description |
|--------|--------|-------------|
| **attestation_score** | 30% | Code-signing + provenance verification |
| **review_score** | 25% | Peer review ratings (1–5 stars) |
| **vulnerability_score** | 25% | Inverse of known CVEs / issues |
| **usage_score** | 20% | Adoption across verified deployments |

### Supply-Chain Attestation
Each capability carries an **attestation record**:
- **signer** — entity that vouches for the capability
- **signature_method** — `sha256_rsa` / `ed25519` / `sigstore`
- **build_provenance** — source repo, commit hash, build system
- **sbom** — software bill of materials (dependency list)
- **verified** — boolean post-verification status

### Dependency Graph
Capabilities can declare dependencies on other capabilities. The marketplace
performs **cycle detection** and **transitive trust propagation** — a
capability's effective trust cannot exceed its lowest-trust dependency.

### Capability States
`draft` → `submitted` → `under_review` → `approved` → `published` → `deprecated` → `revoked`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/capabilities` | Register capability |
| `GET` | `/v1/capabilities` | List / search capabilities |
| `GET` | `/v1/capabilities/{id}` | Capability detail |
| `PATCH` | `/v1/capabilities/{id}/publish` | Advance to published |
| `POST` | `/v1/capabilities/{id}/review` | Submit peer review |
| `POST` | `/v1/capabilities/{id}/attest` | Add attestation |
| `GET` | `/v1/capabilities/{id}/dependencies` | Dependency tree |
| `GET` | `/v1/capabilities/{id}/dependents` | Reverse dependencies |
| `GET` | `/v1/analytics` | Marketplace analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9602
```

---

*Part of the NAIL Institute AVE Database — Phase 22: Adaptive Learning & Evolutionary Defence*
