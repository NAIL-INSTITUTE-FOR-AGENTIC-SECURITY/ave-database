# Defence Orchestration Platform — AVE-Driven Protection

Automated deployment and lifecycle management of guardrails, monitors,
circuit-breakers, and remediation playbooks — all driven by AVE threat
intelligence.

## Overview

The Defence Orchestration Platform (DOP) translates AVE vulnerability
intelligence into actionable, deployed defences. When a new AVE card is
published (or severity changes), DOP automatically evaluates which
guardrails and monitors need to be activated, updated, or rolled back.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Defence Orchestration Platform                   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ Policy Engine │  │ Guardrail    │  │ Monitor            │     │
│  │              │  │ Manager      │  │ Manager            │     │
│  │ • Rule eval  │  │              │  │                    │     │
│  │ • AVE match  │  │ • Deploy     │  │ • Deploy probes    │     │
│  │ • Priority   │  │ • Configure  │  │ • Alert rules      │     │
│  │ • Conflict   │  │ • Test       │  │ • Dashboards       │     │
│  │   resolution │  │ • Rollback   │  │ • Anomaly detect   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬─────────────┘     │
│         │                 │                  │                    │
│  ┌──────▼─────────────────▼──────────────────▼───────────────┐  │
│  │                  Orchestration Core                         │  │
│  │  • AVE feed consumer       • State machine per defence     │  │
│  │  • Deployment scheduler    • Health monitoring              │  │
│  │  • Canary & gradual roll   • Audit & compliance log        │  │
│  └──────────────────────┬─────────────────────────────────────┘  │
│                         │                                        │
│  ┌──────────────────────▼─────────────────────────────────────┐  │
│  │               Integration Layer                              │ │
│  │  • LangChain callbacks  • LlamaGuard  • NeMo Guardrails    │ │
│  │  • OpenAI moderation    • Custom WASM  • OPA policies       │ │
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
         │               │                │
    ┌────▼────┐    ┌─────▼─────┐    ┌─────▼──────┐
    │ Agent A │    │ Agent B   │    │ Agent C    │
    │ (prod)  │    │ (staging) │    │ (canary)   │
    └─────────┘    └───────────┘    └────────────┘
```

## Core Concepts

### Defence Profiles

A Defence Profile is a declarative specification of protections applied to
an agent or fleet:

```yaml
profile: "high-security-agent"
version: "1.2.0"
target_agents:
  - "prod-customer-service-agent"
  - "prod-research-assistant"
guardrails:
  - type: "input_filter"
    name: "prompt-injection-detector"
    config:
      model: "nailinstitute/injection-classifier-v3"
      threshold: 0.85
      action: "block_and_log"
    ave_triggers:
      - "AVE-2025-0001"
      - category: "prompt_injection"
        min_severity: "medium"

  - type: "output_filter"
    name: "pii-redactor"
    config:
      entities: ["email", "phone", "ssn", "credit_card"]
      action: "redact"
    ave_triggers:
      - category: "data_exfiltration"

  - type: "tool_guard"
    name: "tool-call-validator"
    config:
      allow_list: ["search", "calculator", "calendar"]
      parameter_schemas: true
      action: "deny_and_alert"
    ave_triggers:
      - category: "tool_abuse"
        min_severity: "high"

monitors:
  - type: "anomaly_detector"
    name: "behavior-baseline"
    config:
      metrics: ["token_usage", "tool_calls_per_turn", "response_time"]
      window: "5m"
      alert_threshold: 3.0  # standard deviations
    ave_triggers:
      - category: "resource_exhaustion"

  - type: "circuit_breaker"
    name: "rate-limiter"
    config:
      max_requests: 100
      window: "1m"
      action: "throttle"
    ave_triggers:
      - category: "model_denial_of_service"

playbooks:
  - name: "critical-vuln-response"
    trigger:
      ave_severity: "critical"
    actions:
      - enable_guardrail: "prompt-injection-detector"
      - set_circuit_breaker: { max_requests: 10, window: "1m" }
      - notify: ["slack:#security-ops", "pagerduty:critical"]
      - log: "Critical AVE response activated"
```

### Guardrail Types

| Type | Description | Examples |
|------|-------------|----------|
| **Input Filter** | Inspect and filter agent inputs | Injection detection, content classification |
| **Output Filter** | Inspect and filter agent outputs | PII redaction, toxicity filtering |
| **Tool Guard** | Validate and control tool invocations | Allow/deny lists, parameter validation |
| **Memory Guard** | Protect agent memory operations | Write validation, poisoning detection |
| **Delegation Guard** | Control inter-agent delegation | Auth verification, scope enforcement |
| **Context Guard** | Monitor context window utilisation | Token budgets, content priority |

### Monitor Types

| Type | Description | Metrics |
|------|-------------|---------|
| **Anomaly Detector** | Statistical deviation from baseline | Token usage, latency, error rate |
| **Behaviour Monitor** | Sequence-based pattern detection | Tool call chains, goal drift |
| **Circuit Breaker** | Rate/threshold-based cutoffs | Request rate, error budget |
| **Compliance Monitor** | Policy adherence verification | Guardrail bypass attempts |
| **Cost Monitor** | Financial usage tracking | API spend, compute hours |

## API

### Profile Management

```
POST   /v1/profiles                 Create a new defence profile
GET    /v1/profiles                 List all profiles
GET    /v1/profiles/{id}            Get profile details
PUT    /v1/profiles/{id}            Update profile
DELETE /v1/profiles/{id}            Delete profile (soft)
POST   /v1/profiles/{id}/deploy     Deploy profile to targets
POST   /v1/profiles/{id}/rollback   Rollback to previous version
GET    /v1/profiles/{id}/status      Deployment status
```

### Guardrail Management

```
POST   /v1/guardrails               Register a guardrail
GET    /v1/guardrails               List guardrails
GET    /v1/guardrails/{id}          Get guardrail details
PUT    /v1/guardrails/{id}/config   Update guardrail config
POST   /v1/guardrails/{id}/test     Test guardrail with sample input
GET    /v1/guardrails/{id}/metrics  Get guardrail performance metrics
```

### Monitor Management

```
POST   /v1/monitors                 Register a monitor
GET    /v1/monitors                 List monitors
GET    /v1/monitors/{id}/alerts     Get monitor alert history
PUT    /v1/monitors/{id}/threshold  Update alert thresholds
```

### Playbook Management

```
POST   /v1/playbooks                Create a playbook
GET    /v1/playbooks                List playbooks
POST   /v1/playbooks/{id}/execute   Manually trigger a playbook
GET    /v1/playbooks/{id}/history   Execution history
```

### AVE Integration

```
POST   /v1/ave/webhook              Receive AVE live feed events
GET    /v1/ave/coverage             AVE categories covered by active defences
GET    /v1/ave/gaps                 AVE categories with no active defence
```

## Deployment Lifecycle

```
  ┌───────┐     ┌──────────┐     ┌──────────┐     ┌──────┐
  │ Draft │ ──▶ │ Canary   │ ──▶ │ Staged   │ ──▶ │ Full │
  │       │     │ (5%)     │     │ (25/50%) │     │      │
  └───────┘     └──────────┘     └──────────┘     └──────┘
       │              │                │               │
       │        ┌─────▼──────┐  ┌─────▼──────┐       │
       │        │ Auto-test  │  │ Auto-test  │       │
       │        │ & metrics  │  │ & metrics  │       │
       │        └────────────┘  └────────────┘       │
       │                                              │
       └──────────── Rollback on failure ─────────────┘
```

1. **Draft**: Profile created, guardrails configured, tests written
2. **Canary**: Deployed to 5% of traffic; metrics collected for 30 min
3. **Staged**: Gradually expanded (25% → 50%); performance validated
4. **Full**: 100% deployment; continuous monitoring active
5. **Rollback**: Automatic on latency increase >20% or error rate >1%

## Requirements

- Python 3.11+
- FastAPI (orchestration API)
- Redis (state management, pub/sub)
- PostgreSQL (profile storage, audit log)
- Docker (guardrail containers)

## Contact

- **Email**: defence-ops@nailinstitute.org
- **Slack**: `#defence-orchestration`
