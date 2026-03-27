# API Gateway & Service Mesh

> Unified API gateway with authentication, rate limiting, circuit breaking, and service discovery across all 85+ NAIL microservices.

## Overview

The API Gateway & Service Mesh provides a single ingress point for the entire NAIL AVE platform. Every external and internal request flows through this gateway, which enforces authentication, applies rate limits, performs circuit breaking for unhealthy backends, and dynamically discovers registered services. It replaces ad-hoc direct-port access with a centralised, policy-driven routing fabric.

## Port

| Service | Port |
|---------|------|
| API Gateway & Service Mesh | **9200** |

## Key Features

### Authentication & Authorisation
- **API key management** — create, rotate, revoke keys with scoped permissions
- **JWT token validation** — RS256/HS256 token verification with configurable issuer and audience
- **Role-based access control (RBAC)** — 5 roles (admin, operator, analyst, auditor, readonly) with granular endpoint permissions
- **Per-key rate-limit overrides** — VIP keys can carry custom rate-limit tiers
- **Key usage tracking** — request count, last-used timestamp, quota monitoring

### Rate Limiting
- **Token-bucket algorithm** — configurable bucket capacity and refill rate per tier
- **4 rate-limit tiers** — free (60 req/min), standard (300 req/min), professional (1,200 req/min), enterprise (6,000 req/min)
- **Per-key and per-IP enforcement** — independent buckets for authenticated and anonymous traffic
- **Burst allowance** — short-burst capacity up to 2× sustained rate
- **Rate-limit headers** — X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset on every response

### Circuit Breaking
- **Per-backend circuit breaker** — 3 states: closed (healthy), open (tripped), half-open (testing)
- **Failure threshold** — configurable consecutive failure count to trip (default: 5)
- **Recovery timeout** — configurable seconds before half-open probe (default: 30s)
- **Half-open probe** — single request forwarded; success resets, failure re-trips
- **Health-aware routing** — requests to open circuits return 503 immediately with Retry-After header

### Service Discovery & Routing
- **Service registry** — dynamic registration/deregistration of backend services with health URLs
- **Path-prefix routing** — `/v1/{service}/...` automatically routes to the registered backend
- **Health polling** — periodic background health checks with configurable interval
- **Service metadata** — version, port, tags, description for each registered service
- **Hot-reload** — services can register/deregister without gateway restart

### Request Proxying
- **Full HTTP proxy** — GET/POST/PUT/PATCH/DELETE forwarded with headers and body
- **Request/response logging** — audit-grade log of every proxied request with latency
- **Timeout enforcement** — per-route configurable upstream timeout (default: 30s)
- **Error normalisation** — upstream errors wrapped in consistent NAIL error envelope

### Analytics & Audit
- **Real-time dashboard** — requests/sec, error rate, p50/p95/p99 latency by service
- **Top consumers** — most active API keys by request volume
- **Circuit breaker status** — live state of every backend circuit
- **Audit log** — immutable append-only log of all authentication and routing decisions

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Gateway health check |
| POST | `/v1/keys` | Create API key |
| GET | `/v1/keys` | List API keys |
| DELETE | `/v1/keys/{key_id}` | Revoke API key |
| POST | `/v1/services` | Register backend service |
| GET | `/v1/services` | List registered services |
| DELETE | `/v1/services/{service_id}` | Deregister service |
| GET | `/v1/services/{service_id}/health` | Check specific service health |
| GET | `/v1/circuits` | List all circuit breaker states |
| POST | `/v1/circuits/{service_id}/reset` | Manually reset a circuit |
| GET | `/v1/rate-limits` | View current rate-limit configuration |
| GET | `/v1/proxy/{service}/{path}` | Proxy request to backend service |
| GET | `/v1/audit` | Query audit log |
| GET | `/v1/analytics` | Gateway analytics dashboard |

## Architecture

```
Client → [Auth] → [Rate Limit] → [Circuit Breaker] → [Route] → Backend Service
                                                         ↑
                                              Service Registry (health polling)
```

## Production Notes

- **Authentication store** → Redis + PostgreSQL for key management
- **Rate limiting** → Redis sliding-window counters for distributed enforcement
- **Service discovery** → Consul / etcd / Kubernetes service API
- **Circuit breaker** → Resilience4j-style with distributed state
- **Audit log** → Append-only event store (Kafka → S3 archival)
- **TLS termination** → Envoy or NGINX sidecar for mTLS
