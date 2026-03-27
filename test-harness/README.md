# End-to-End Test Harness

> Comprehensive integration test framework exercising cross-service workflows, chaos testing, and regression detection for the NAIL AVE platform.

## Overview

The End-to-End Test Harness provides a testing-as-a-service engine that orchestrates multi-service integration tests, injects controlled failures (chaos testing), detects regressions across releases, and generates compliance-grade test reports. It treats the entire NAIL platform as a system under test, exercising real API contracts between services.

## Port

| Service | Port |
|---------|------|
| End-to-End Test Harness | **9203** |

## Key Features

### Test Suite Management
- **Suite registry** — create, list, update, and archive test suites
- **5 suite types** — smoke, integration, regression, chaos, compliance
- **Dependency declaration** — suites can declare which services they require
- **Tagging** — arbitrary tags for filtering (e.g., `critical-path`, `nightly`, `pre-release`)
- **Parameterised suites** — configurable test parameters (target services, load level, duration)

### Test Case Engine
- **Test case CRUD** — define individual test cases within suites
- **Assertion library** — status code checks, JSON path assertions, latency bounds, schema validation
- **Multi-step workflows** — ordered test steps with data passing between steps (response → next request)
- **Setup/teardown hooks** — pre-test data seeding and post-test cleanup actions
- **Retry policy** — configurable retries per step with exponential backoff

### Test Execution
- **Run orchestration** — execute suites sequentially or in parallel with configurable concurrency
- **Live streaming** — real-time test execution status via polling endpoint
- **Timeout enforcement** — per-step and per-suite timeout limits
- **Environment targeting** — run against dev, staging, or production endpoints
- **Dry-run mode** — validate test definitions without executing

### Chaos Testing
- **Fault injection** — simulate service failures (HTTP 500, timeout, connection refused)
- **Latency injection** — add configurable artificial latency to service calls
- **Partition simulation** — simulate network partitions between services
- **Resource exhaustion** — simulate CPU/memory pressure on target services
- **Chaos experiments** — define hypothesis + steady state + injection + rollback
- **Blast radius control** — limit chaos scope to specific services/endpoints

### Regression Detection
- **Baseline capture** — record performance baselines (latency, throughput, error rate) per test run
- **Regression rules** — alert when metrics deviate beyond configurable thresholds from baseline
- **Diff reports** — side-by-side comparison of current vs baseline results
- **Flakiness detection** — flag tests with inconsistent pass/fail patterns across runs
- **Trend analysis** — track test health over time with pass-rate trends

### Reporting
- **Structured reports** — JSON/HTML test reports with pass/fail/skip counts, duration, logs
- **Compliance mapping** — map test cases to compliance requirements (EU AI Act, NIST, ISO 27001)
- **Coverage matrix** — which services and endpoints are covered by tests
- **Failure analysis** — root-cause hints from error patterns and correlated failures
- **Historical archive** — all past run results queryable by suite, date, environment

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Test harness health |
| POST | `/v1/suites` | Create test suite |
| GET | `/v1/suites` | List test suites |
| GET | `/v1/suites/{suite_id}` | Suite details + test cases |
| POST | `/v1/suites/{suite_id}/cases` | Add test case |
| GET | `/v1/suites/{suite_id}/cases` | List test cases |
| POST | `/v1/runs` | Execute test run |
| GET | `/v1/runs` | List test runs |
| GET | `/v1/runs/{run_id}` | Run details + results |
| GET | `/v1/runs/{run_id}/report` | Generated test report |
| POST | `/v1/chaos/experiments` | Create chaos experiment |
| GET | `/v1/chaos/experiments` | List chaos experiments |
| POST | `/v1/chaos/experiments/{exp_id}/run` | Execute chaos experiment |
| GET | `/v1/baselines` | View performance baselines |
| POST | `/v1/baselines/capture` | Capture new baseline |
| GET | `/v1/regressions` | Detected regressions |
| GET | `/v1/coverage` | Service/endpoint coverage matrix |
| GET | `/v1/analytics` | Test harness analytics |

## Architecture

```
Test Definition → [Orchestrator] → [Executor] → Target Services
                       ↓                ↓
                  Chaos Engine      Result Collector
                       ↓                ↓
                  Fault Injector    Report Generator
                                       ↓
                              Regression Detector ← Baseline Store
```

## Production Notes

- **Test orchestration** → Kubernetes Jobs / Argo Workflows / custom scheduler
- **Chaos engine** → LitmusChaos / Chaos Mesh / Gremlin integration
- **Result storage** → PostgreSQL + S3 for reports
- **Baseline store** → InfluxDB / PostgreSQL time-series
- **CI/CD integration** → GitHub Actions / GitLab CI / Jenkins webhook triggers
- **Compliance mapping** → OSCAL / custom requirement-to-test mapping
