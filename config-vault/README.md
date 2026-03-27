# Distributed Configuration Vault

**Phase 23 — Service 3 of 5 · Port `9702`**

Encrypted configuration management with versioning, rollback, audit trails,
environment-aware secret rotation, and policy-based access control.

---

## Core Concepts

### Namespaces
Configurations are grouped into **namespaces** (e.g., `production`, `staging`,
`development`). Each namespace isolates its configs and secrets.

### Configuration Entries
Each entry has:
- **key** / **value** / **namespace** / **environment**
- **encrypted** flag — values encrypted at rest with AES-256-GCM (simulated)
- **version** — auto-incremented on update
- **history** — full version history with diff tracking

### Secrets
Secrets are special config entries with:
- **rotation_policy**: `manual` | `scheduled` | `on_access`
- **rotation_interval_hours** — for scheduled rotation
- **last_rotated_at** / **next_rotation_at**
- **access_count** — tracked for on_access rotation trigger

### Access Policies
| Policy | Description |
|--------|-------------|
| `read_only` | Can read config values |
| `read_write` | Can read and update configs |
| `admin` | Full access including delete and policy changes |
| `rotate_only` | Can only trigger secret rotation |

### Audit Trail
Every operation is logged:
- **actor** / **action** / **key** / **namespace** / **timestamp**
- **old_value_hash** / **new_value_hash** (SHA-256, never raw values)

### Rollback
Any config entry can be rolled back to a previous version. The rollback
itself is a new version entry for full traceability.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/namespaces` | Create namespace |
| `GET` | `/v1/namespaces` | List namespaces |
| `POST` | `/v1/configs` | Set config entry |
| `GET` | `/v1/configs` | List configs with filters |
| `GET` | `/v1/configs/{key}` | Get config value |
| `POST` | `/v1/configs/{key}/rollback` | Rollback to version |
| `GET` | `/v1/configs/{key}/history` | Version history |
| `POST` | `/v1/secrets` | Create secret |
| `POST` | `/v1/secrets/{key}/rotate` | Rotate secret |
| `GET` | `/v1/audit` | Audit trail |
| `GET` | `/v1/analytics` | Vault analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9702
```

---

*Part of the NAIL Institute AVE Database — Phase 23: Autonomous Resilience & Self-Healing Infrastructure*
