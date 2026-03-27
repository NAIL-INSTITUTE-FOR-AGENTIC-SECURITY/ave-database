# Production Deployment Pipeline

> CI/CD pipeline engine with multi-stage builds, security scanning, canary deployments, and automated rollback for the NAIL AVE platform.

## Overview

The Production Deployment Pipeline provides a self-service deployment-as-a-service engine managing the full release lifecycle for every NAIL microservice. It orchestrates multi-stage build pipelines, runs security scans, executes progressive canary rollouts, monitors deployment health, and triggers automated rollback on anomaly detection. Every deployment is audited, reproducible, and traceable.

## Port

| Service | Port |
|---------|------|
| Production Deployment Pipeline | **9204** |

## Key Features

### Pipeline Management
- **Pipeline registry** — create, list, update, and archive deployment pipelines
- **Multi-stage pipelines** — ordered stages: build → test → scan → stage → canary → promote → verify
- **Stage gates** — manual approval gates between stages for critical services
- **Pipeline templates** — reusable pipeline definitions for common service types (FastAPI, Node.js, static)
- **Parameterisation** — configurable build args, target environment, canary percentage, rollback thresholds

### Build Stage
- **Multi-stage Docker builds** — optimised container images with build cache
- **Build artifacts** — versioned artifact storage with SHA256 integrity verification
- **Dependency resolution** — auto-detect and install Python/Node/system dependencies
- **Build matrix** — parallel builds for multiple architectures (amd64, arm64)
- **Build logs** — streaming build output with error highlighting

### Security Scanning
- **Container image scanning** — CVE detection using Trivy/Grype vulnerability databases
- **Dependency audit** — known-vulnerability checks on Python/Node packages
- **SAST** — static application security testing on source code
- **Secret detection** — scan for accidentally committed secrets, tokens, keys
- **Scan policy** — configurable severity thresholds (block on critical, warn on high)
- **SBOM generation** — Software Bill of Materials in SPDX/CycloneDX format

### Canary Deployments
- **Progressive rollout** — 5% → 25% → 50% → 100% traffic shift with configurable steps
- **Health gates** — automatic promotion only if error rate < threshold and latency < threshold
- **Traffic splitting** — weighted routing between current and canary versions
- **Canary metrics** — real-time comparison of canary vs baseline error rate, latency, throughput
- **Automatic promotion** — promote to full rollout when all health gates pass
- **Automatic rollback** — revert to previous version if any health gate fails

### Rollback Engine
- **One-click rollback** — instantly revert to any previous known-good deployment
- **Rollback triggers** — automatic on canary failure, SLO breach, or manual trigger
- **Rollback verification** — post-rollback health check confirming service restored
- **Rollback history** — full audit trail of all rollback events with reasons

### Environment Management
- **3 environments** — development, staging, production with promotion gates
- **Environment parity** — identical configurations across environments (12-factor)
- **Configuration management** — environment-specific config injection via env vars/secrets
- **Feature flags** — toggle features per environment without redeployment

### Audit & Compliance
- **Deployment audit log** — immutable record of every deployment (who, what, when, where)
- **Change tracking** — diff between deployed versions (image, config, env vars)
- **Approval records** — who approved which stage gate, with timestamp
- **Compliance reports** — deployment frequency, lead time, MTTR, change failure rate (DORA metrics)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Pipeline service health |
| POST | `/v1/pipelines` | Create deployment pipeline |
| GET | `/v1/pipelines` | List pipelines |
| GET | `/v1/pipelines/{pipeline_id}` | Pipeline details |
| POST | `/v1/deployments` | Trigger deployment |
| GET | `/v1/deployments` | List deployments |
| GET | `/v1/deployments/{deploy_id}` | Deployment status + stages |
| POST | `/v1/deployments/{deploy_id}/approve` | Approve stage gate |
| POST | `/v1/deployments/{deploy_id}/rollback` | Trigger rollback |
| GET | `/v1/deployments/{deploy_id}/canary` | Canary metrics |
| POST | `/v1/scans` | Trigger security scan |
| GET | `/v1/scans` | List scan results |
| GET | `/v1/scans/{scan_id}` | Scan detail + vulnerabilities |
| GET | `/v1/environments` | List environments |
| GET | `/v1/artifacts` | List build artifacts |
| GET | `/v1/rollbacks` | Rollback history |
| GET | `/v1/dora` | DORA metrics dashboard |
| GET | `/v1/analytics` | Pipeline analytics |

## Architecture

```
Git Push → [Build] → [Test] → [Security Scan] → [Stage Gate]
                                                      ↓
                                              [Canary Deploy 5%]
                                                      ↓
                                              [Health Monitor]
                                              ↙            ↘
                                    [Promote 100%]    [Rollback]
                                          ↓
                                   [Post-Deploy Verify]
```

## Production Notes

- **Build engine** → Docker BuildKit / Kaniko for rootless builds
- **Artifact store** → OCI registry (Harbor, ECR, GCR)
- **Security scanners** → Trivy, Grype, Semgrep, Gitleaks
- **Canary routing** → Istio / Linkerd / AWS App Mesh traffic splitting
- **Rollback** → Kubernetes rollout undo / ArgoCD sync
- **CI/CD orchestration** → GitHub Actions / ArgoCD / Tekton Pipelines
- **DORA metrics** → Google Four Keys / custom metric aggregation
- **Secrets management** → HashiCorp Vault / AWS Secrets Manager
