# 🧰 Universal Defence SDK

> Developer-friendly SDK abstracting the entire AVE ecosystem into
> simple API calls — scan, protect, report, govern — with plug-and-play
> framework adapters for Python, TypeScript, Go, and Rust.

## Overview

The Universal Defence SDK is the single integration point for developers
who want to embed agentic AI security into their applications.  Instead
of calling 14+ individual NAIL microservices, developers install the SDK,
configure their target language and framework, and call high-level
operations: **scan** (vulnerability assessment), **protect** (apply
guardrails), **report** (compliance / governance), and **govern**
(policy enforcement).  The SDK routes to the correct backend services
transparently.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    Universal Defence SDK                       │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │  scan()  │  │ protect()│  │ report() │  │  govern()    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │
│       │              │              │               │         │
│  ┌────▼──────────────▼──────────────▼───────────────▼───────┐ │
│  │                  SDK Router & Dispatcher                  │ │
│  │  Service Discovery │ Config Resolver │ Auth Manager       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Language │  │ Framework    │  │ Plugin   │  │ Telemetry│ │
│  │ Adapters │  │ Adapters     │  │ Registry │  │ Collector│ │
│  │ Py/TS/Go │  │ LC/CA/AG/LI  │  │          │  │          │ │
│  │ /Rust    │  │              │  │          │  │          │ │
│  └──────────┘  └──────────────┘  └──────────┘  └──────────┘ │
└───────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **4 High-Level Ops** | scan, protect, report, govern — covers full security lifecycle |
| **4 Language SDKs** | Python, TypeScript, Go, Rust with idiomatic APIs |
| **5 Framework Adapters** | LangChain, CrewAI, AutoGen, LlamaIndex, Custom |
| **Service Router** | Automatically routes SDK calls to correct backend services |
| **Plugin Registry** | Extensible plugin system for custom integrations |
| **Config Profiles** | Pre-built config bundles per use case (chat, RAG, multi-agent) |
| **Telemetry** | Aggregated security telemetry across all SDK operations |
| **Offline Mode** | Local-only scanning when backend unreachable |
| **Batch Operations** | Bulk scan/protect for pipeline and CI/CD use cases |
| **Schema Validation** | Input/output validation against AVE schema |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | SDK service health and backend connectivity |
| `POST` | `/v1/scan` | Scan a payload / agent config for vulnerabilities |
| `POST` | `/v1/protect` | Apply guardrail protection to a payload |
| `POST` | `/v1/report` | Generate compliance / governance report |
| `POST` | `/v1/govern` | Enforce governance policy on a deployment |
| `GET` | `/v1/languages` | List supported language SDKs |
| `GET` | `/v1/frameworks` | List supported framework adapters |
| `GET` | `/v1/plugins` | List registered plugins |
| `POST` | `/v1/plugins` | Register a custom plugin |
| `GET` | `/v1/profiles` | List pre-built config profiles |
| `POST` | `/v1/batch` | Batch scan/protect operations |
| `GET` | `/v1/telemetry` | Aggregated SDK telemetry |
| `GET` | `/v1/analytics` | SDK usage analytics |

## Running

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 8904
```

## Port

| Service | Port |
|---------|------|
| Universal Defence SDK | **8904** |

## Production Notes

- Replace in-memory stores with **PostgreSQL** + **Redis**
- Publish real SDK packages to **PyPI, npm, crates.io, pkg.go.dev**
- Add **gRPC** transport for high-throughput SDK calls
- Implement real **service mesh** integration (Istio / Linkerd)
