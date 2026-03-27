# Cross-Phase Integration Gateway

**Phase 22 — Service 5 of 5 · Port `9604`**

Unified API gateway federating all 22 phases with service discovery, rate
limiting, circuit breaking, unified authentication, and request routing.

---

## Core Concepts

### Service Registry
Every microservice across all 22 phases registers with the gateway. Each entry
includes:
- **service_id** / **phase** / **name** / **base_url** / **port**
- **health_status**: `healthy` | `degraded` | `unhealthy` | `unknown`
- **capabilities**: list of offered API paths
- **version** / **last_heartbeat**

### Rate Limiting
Token-bucket rate limiter per client:
| Tier | Requests/min | Burst |
|------|-------------|-------|
| `free` | 60 | 10 |
| `standard` | 300 | 50 |
| `premium` | 1000 | 200 |
| `enterprise` | 5000 | 1000 |

### Circuit Breaker
Per-service circuit breaker with three states:
- **closed** — requests flow normally
- **open** — requests fail-fast after failure threshold reached
- **half_open** — limited probe requests to test recovery

Configuration: `failure_threshold` (default 5), `recovery_timeout_seconds`
(default 30), `half_open_max_requests` (default 3).

### Unified Authentication
API key-based auth with scoped permissions:
- **api_key_id** / **client_name** / **tier** / **scopes** (list of service IDs)
- **rate_limit_override** (optional per-key override)
- **expires_at** / **revoked**

### Request Routing
The gateway proxies requests to backend services, recording:
- Route, method, target service, response status, latency
- Rate limit consumption tracking
- Circuit breaker state transitions

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Gateway health + service summary |
| `POST` | `/v1/services` | Register a service |
| `GET` | `/v1/services` | List registered services |
| `GET` | `/v1/services/{id}` | Service detail |
| `POST` | `/v1/services/{id}/heartbeat` | Service heartbeat |
| `POST` | `/v1/api-keys` | Create API key |
| `GET` | `/v1/api-keys` | List API keys |
| `POST` | `/v1/api-keys/{id}/revoke` | Revoke API key |
| `POST` | `/v1/route` | Route a request through the gateway |
| `GET` | `/v1/circuit-breakers` | Circuit breaker states |
| `GET` | `/v1/analytics` | Gateway analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9604
```

---

*Part of the NAIL Institute AVE Database — Phase 22: Adaptive Learning & Evolutionary Defence*
