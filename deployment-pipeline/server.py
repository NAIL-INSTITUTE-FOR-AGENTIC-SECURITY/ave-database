"""
Production Deployment Pipeline — Core deployment orchestration server.

End-to-end deployment lifecycle from build through security scanning,
canary rollout, and production promotion.  Enforces stage gates,
tracks artifacts, manages environments, and computes DORA metrics
for continuous delivery performance.
"""

from __future__ import annotations

import hashlib
import random
import statistics
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NAIL Production Deployment Pipeline",
    description=(
        "Build, scan, canary deploy, promote, and rollback — "
        "with full audit trail and DORA metrics."
    ),
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Constants / Enums
# ---------------------------------------------------------------------------

PIPELINE_STAGES = ["build", "test", "scan", "stage", "canary", "promote", "verify"]

SERVICES = [
    "api-gateway", "event-bus", "threat-intel", "autonomous-redteam",
    "defence-mesh", "predictive-engine", "incident-commander",
    "ethical-reasoning", "civilisational-risk", "standards-evolution",
    "recursive-self-improvement", "temporal-forensics",
    "observability", "test-harness",
]


class PipelineStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    BUILDING = "building"
    TESTING = "testing"
    SCANNING = "scanning"
    STAGING = "staging"
    CANARY = "canary"
    PROMOTING = "promoting"
    VERIFYING = "verifying"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"
    CANCELLED = "cancelled"


class ScanSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScanType(str, Enum):
    CVE = "cve"
    DEPENDENCY_AUDIT = "dependency_audit"
    SAST = "sast"
    SECRET_DETECTION = "secret_detection"
    SBOM = "sbom"


class EnvironmentName(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class CanaryPhase(str, Enum):
    BASELINE = "baseline"
    PHASE_5 = "5_percent"
    PHASE_25 = "25_percent"
    PHASE_50 = "50_percent"
    PHASE_100 = "100_percent"
    ROLLED_BACK = "rolled_back"


class RollbackTrigger(str, Enum):
    CANARY_FAILURE = "canary_failure"
    SLO_BREACH = "slo_breach"
    MANUAL = "manual"
    SCAN_FAILURE = "scan_failure"
    TEST_FAILURE = "test_failure"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class Pipeline(BaseModel):
    id: str = Field(default_factory=lambda: f"PIPE-{uuid.uuid4().hex[:8].upper()}")
    name: str
    service: str = ""
    description: str = ""
    stages: list[str] = Field(default_factory=lambda: list(PIPELINE_STAGES))
    requires_approval: bool = True
    approval_stage: str = "promote"
    auto_canary: bool = True
    canary_error_threshold_pct: float = 5.0
    canary_latency_threshold_ms: float = 500.0
    scan_policy: str = "block_critical_warn_high"
    parameters: dict[str, Any] = Field(default_factory=dict)
    status: PipelineStatus = PipelineStatus.ACTIVE
    total_deployments: int = 0
    successful_deployments: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PipelineCreate(BaseModel):
    name: str
    service: str = ""
    description: str = ""
    stages: list[str] = Field(default_factory=lambda: list(PIPELINE_STAGES))
    requires_approval: bool = True
    auto_canary: bool = True
    canary_error_threshold_pct: float = 5.0
    canary_latency_threshold_ms: float = 500.0
    scan_policy: str = "block_critical_warn_high"


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: f"ART-{uuid.uuid4().hex[:8].upper()}")
    service: str
    version: str
    image_tag: str = ""
    sha256: str = ""
    architecture: str = "amd64"
    size_mb: float = 0.0
    build_duration_sec: float = 0.0
    dependencies: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ScanResult(BaseModel):
    id: str = Field(default_factory=lambda: f"SCAN-{uuid.uuid4().hex[:8].upper()}")
    artifact_id: str
    deployment_id: str = ""
    scan_type: ScanType
    scanner: str = ""  # trivy, grype, semgrep, gitleaks, etc.
    findings_count: int = 0
    findings: list[dict[str, Any]] = Field(default_factory=list)
    severity_counts: dict[str, int] = Field(default_factory=dict)
    passed: bool = True
    policy: str = ""
    sbom_format: str = ""  # spdx, cyclonedx (for SBOM scans)
    duration_sec: float = 0.0
    scanned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CanaryState(BaseModel):
    phase: CanaryPhase = CanaryPhase.BASELINE
    traffic_pct: int = 0
    error_rate_pct: float = 0.0
    latency_p95_ms: float = 0.0
    baseline_error_rate: float = 0.0
    baseline_latency_p95: float = 0.0
    health_checks_passed: int = 0
    health_checks_failed: int = 0
    auto_promoted: bool = False
    auto_rolled_back: bool = False
    phase_history: list[dict[str, Any]] = Field(default_factory=list)


class Deployment(BaseModel):
    id: str = Field(default_factory=lambda: f"DEP-{uuid.uuid4().hex[:8].upper()}")
    pipeline_id: str
    service: str = ""
    version: str = ""
    artifact_id: str = ""
    environment: EnvironmentName = EnvironmentName.DEV
    status: DeploymentStatus = DeploymentStatus.PENDING
    current_stage: str = "build"
    stage_log: list[dict[str, Any]] = Field(default_factory=list)
    canary: CanaryState = Field(default_factory=CanaryState)
    scan_ids: list[str] = Field(default_factory=list)
    approved_by: str = ""
    approval_time: Optional[str] = None
    rollback_from: str = ""  # If this is a rollback, which deployment it rolled back
    duration_sec: float = 0.0
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class DeploymentTrigger(BaseModel):
    pipeline_id: str
    version: str
    environment: EnvironmentName = EnvironmentName.DEV
    parameters: dict[str, Any] = Field(default_factory=dict)


class Rollback(BaseModel):
    id: str = Field(default_factory=lambda: f"RB-{uuid.uuid4().hex[:8].upper()}")
    deployment_id: str
    trigger: RollbackTrigger
    rollback_to_version: str = ""
    reason: str = ""
    verified: bool = False
    duration_sec: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EnvironmentState(BaseModel):
    name: EnvironmentName
    current_version: str = ""
    current_deployment_id: str = ""
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    last_deploy: Optional[str] = None
    healthy: bool = True


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → ArgoCD + Harbor + PostgreSQL + Vault)
# ---------------------------------------------------------------------------

PIPELINES: dict[str, Pipeline] = {}
DEPLOYMENTS: dict[str, Deployment] = {}
ARTIFACTS: dict[str, Artifact] = {}
SCANS: dict[str, ScanResult] = {}
ROLLBACKS: dict[str, Rollback] = {}
ENVIRONMENTS: dict[str, dict[str, EnvironmentState]] = {}  # service → env_name → state

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731
_rng = random.Random(42)


def _generate_sha256() -> str:
    return hashlib.sha256(_rng.randbytes(32)).hexdigest()


def _run_security_scans(artifact: Artifact, deployment_id: str, policy: str) -> list[ScanResult]:
    """Simulate running security scans on an artifact."""
    scans = []

    # CVE scan
    cve_findings = []
    for _ in range(_rng.randint(0, 8)):
        sev = _rng.choices(
            [ScanSeverity.CRITICAL, ScanSeverity.HIGH, ScanSeverity.MEDIUM, ScanSeverity.LOW],
            weights=[0.05, 0.15, 0.40, 0.40],
        )[0]
        cve_findings.append({
            "id": f"CVE-2024-{_rng.randint(10000, 99999)}",
            "severity": sev.value,
            "package": _rng.choice(["openssl", "libcurl", "zlib", "python-cryptography", "requests"]),
            "fixed_version": f"{_rng.randint(1, 5)}.{_rng.randint(0, 9)}.{_rng.randint(0, 9)}",
        })

    sev_counts = Counter(f["severity"] for f in cve_findings)
    cve_passed = sev_counts.get("critical", 0) == 0 if "block_critical" in policy else True

    scans.append(ScanResult(
        artifact_id=artifact.id, deployment_id=deployment_id,
        scan_type=ScanType.CVE, scanner="trivy",
        findings_count=len(cve_findings), findings=cve_findings,
        severity_counts=dict(sev_counts), passed=cve_passed,
        policy=policy, duration_sec=round(_rng.uniform(5, 30), 1),
    ))

    # SAST scan
    sast_findings = []
    for _ in range(_rng.randint(0, 4)):
        sast_findings.append({
            "rule": _rng.choice(["sql-injection", "xss", "path-traversal", "hardcoded-secret", "insecure-hash"]),
            "severity": _rng.choice(["high", "medium", "low"]),
            "file": f"src/{_rng.choice(['auth', 'api', 'utils', 'handlers'])}.py",
            "line": _rng.randint(10, 500),
        })

    scans.append(ScanResult(
        artifact_id=artifact.id, deployment_id=deployment_id,
        scan_type=ScanType.SAST, scanner="semgrep",
        findings_count=len(sast_findings), findings=sast_findings,
        severity_counts=dict(Counter(f["severity"] for f in sast_findings)),
        passed=not any(f["severity"] == "critical" for f in sast_findings),
        policy=policy, duration_sec=round(_rng.uniform(10, 60), 1),
    ))

    # Secret detection
    secret_findings = []
    if _rng.random() < 0.1:
        secret_findings.append({
            "type": "aws_access_key",
            "file": "config/settings.py",
            "line": _rng.randint(1, 100),
        })

    scans.append(ScanResult(
        artifact_id=artifact.id, deployment_id=deployment_id,
        scan_type=ScanType.SECRET_DETECTION, scanner="gitleaks",
        findings_count=len(secret_findings), findings=secret_findings,
        passed=len(secret_findings) == 0,
        policy=policy, duration_sec=round(_rng.uniform(3, 15), 1),
    ))

    # SBOM generation
    scans.append(ScanResult(
        artifact_id=artifact.id, deployment_id=deployment_id,
        scan_type=ScanType.SBOM, scanner="syft",
        findings_count=0,
        findings=[{"format": "spdx-json", "packages": _rng.randint(50, 200)}],
        passed=True, sbom_format="spdx",
        policy=policy, duration_sec=round(_rng.uniform(2, 10), 1),
    ))

    return scans


def _simulate_canary(deployment: Deployment, pipeline: Pipeline) -> None:
    """Simulate canary progressive rollout."""
    phases = [
        (CanaryPhase.PHASE_5, 5),
        (CanaryPhase.PHASE_25, 25),
        (CanaryPhase.PHASE_50, 50),
        (CanaryPhase.PHASE_100, 100),
    ]

    # Baseline metrics
    deployment.canary.baseline_error_rate = round(_rng.uniform(0.5, 2.0), 2)
    deployment.canary.baseline_latency_p95 = round(_rng.uniform(50, 200), 2)

    for phase, pct in phases:
        error_rate = round(deployment.canary.baseline_error_rate + _rng.uniform(-0.5, 2.0), 2)
        error_rate = max(0, error_rate)
        latency = round(deployment.canary.baseline_latency_p95 + _rng.uniform(-30, 80), 2)
        latency = max(10, latency)

        deployment.canary.phase = phase
        deployment.canary.traffic_pct = pct
        deployment.canary.error_rate_pct = error_rate
        deployment.canary.latency_p95_ms = latency

        phase_entry = {
            "phase": phase.value, "traffic_pct": pct,
            "error_rate_pct": error_rate, "latency_p95_ms": latency,
            "timestamp": _now().isoformat(),
        }

        # Health check
        if error_rate > pipeline.canary_error_threshold_pct or latency > pipeline.canary_latency_threshold_ms:
            deployment.canary.health_checks_failed += 1
            phase_entry["health"] = "failed"

            if pipeline.auto_canary and deployment.canary.health_checks_failed >= 2:
                deployment.canary.phase = CanaryPhase.ROLLED_BACK
                deployment.canary.auto_rolled_back = True
                phase_entry["action"] = "auto_rollback"
                deployment.canary.phase_history.append(phase_entry)
                return
        else:
            deployment.canary.health_checks_passed += 1
            phase_entry["health"] = "passed"

        deployment.canary.phase_history.append(phase_entry)

    # Full promotion
    deployment.canary.auto_promoted = True


def _simulate_deployment(deployment: Deployment, pipeline: Pipeline) -> None:
    """Simulate full deployment lifecycle."""
    stages_completed = []
    total_duration = 0.0

    for stage in pipeline.stages:
        deployment.current_stage = stage
        stage_start = _now().isoformat()
        stage_duration = round(_rng.uniform(5, 120), 1)
        total_duration += stage_duration

        if stage == "build":
            # Create artifact
            artifact = Artifact(
                service=deployment.service,
                version=deployment.version,
                image_tag=f"{deployment.service}:{deployment.version}",
                sha256=_generate_sha256(),
                size_mb=round(_rng.uniform(50, 300), 1),
                build_duration_sec=stage_duration,
            )
            ARTIFACTS[artifact.id] = artifact
            deployment.artifact_id = artifact.id

            stages_completed.append({
                "stage": stage, "status": "passed",
                "duration_sec": stage_duration,
                "artifact_id": artifact.id,
                "timestamp": stage_start,
            })

        elif stage == "test":
            passed = _rng.random() < 0.95
            stages_completed.append({
                "stage": stage, "status": "passed" if passed else "failed",
                "duration_sec": stage_duration,
                "tests_run": _rng.randint(50, 200),
                "tests_passed": _rng.randint(48, 200) if passed else _rng.randint(30, 45),
                "timestamp": stage_start,
            })
            if not passed:
                deployment.status = DeploymentStatus.FAILED
                deployment.stage_log = stages_completed
                deployment.duration_sec = total_duration
                return

        elif stage == "scan":
            artifact = ARTIFACTS.get(deployment.artifact_id)
            if artifact:
                scans = _run_security_scans(artifact, deployment.id, pipeline.scan_policy)
                for scan in scans:
                    SCANS[scan.id] = scan
                    deployment.scan_ids.append(scan.id)

                all_passed = all(s.passed for s in scans)
                stages_completed.append({
                    "stage": stage, "status": "passed" if all_passed else "failed",
                    "duration_sec": sum(s.duration_sec for s in scans),
                    "scans_run": len(scans),
                    "scans_passed": sum(1 for s in scans if s.passed),
                    "timestamp": stage_start,
                })

                if not all_passed:
                    deployment.status = DeploymentStatus.FAILED
                    deployment.stage_log = stages_completed
                    deployment.duration_sec = total_duration
                    return

        elif stage == "stage":
            stages_completed.append({
                "stage": stage, "status": "passed",
                "duration_sec": stage_duration,
                "environment": "staging",
                "timestamp": stage_start,
            })
            deployment.status = DeploymentStatus.STAGING

        elif stage == "canary":
            _simulate_canary(deployment, pipeline)
            canary_passed = deployment.canary.phase != CanaryPhase.ROLLED_BACK

            stages_completed.append({
                "stage": stage, "status": "passed" if canary_passed else "rolled_back",
                "duration_sec": stage_duration,
                "final_phase": deployment.canary.phase.value,
                "auto_promoted": deployment.canary.auto_promoted,
                "auto_rolled_back": deployment.canary.auto_rolled_back,
                "timestamp": stage_start,
            })

            if not canary_passed:
                deployment.status = DeploymentStatus.ROLLED_BACK
                deployment.stage_log = stages_completed
                deployment.duration_sec = total_duration
                return

        elif stage == "promote":
            if pipeline.requires_approval:
                deployment.status = DeploymentStatus.AWAITING_APPROVAL
                # Auto-approve for simulation
                deployment.approved_by = "auto-approver"
                deployment.approval_time = _now().isoformat()

            stages_completed.append({
                "stage": stage, "status": "passed",
                "duration_sec": stage_duration,
                "approved_by": deployment.approved_by,
                "timestamp": stage_start,
            })
            deployment.status = DeploymentStatus.PROMOTING

        elif stage == "verify":
            passed = _rng.random() < 0.97
            stages_completed.append({
                "stage": stage, "status": "passed" if passed else "failed",
                "duration_sec": stage_duration,
                "health_checks": _rng.randint(3, 10),
                "timestamp": stage_start,
            })

            if not passed:
                deployment.status = DeploymentStatus.FAILED
                deployment.stage_log = stages_completed
                deployment.duration_sec = total_duration
                return

    deployment.status = DeploymentStatus.DEPLOYED
    deployment.stage_log = stages_completed
    deployment.duration_sec = round(total_duration, 1)
    deployment.completed_at = _now().isoformat()

    # Update environment state
    svc = deployment.service
    env = deployment.environment.value
    if svc not in ENVIRONMENTS:
        ENVIRONMENTS[svc] = {}
    ENVIRONMENTS[svc][env] = EnvironmentState(
        name=deployment.environment,
        current_version=deployment.version,
        current_deployment_id=deployment.id,
        last_deploy=_now().isoformat(),
    )


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    rng = random.Random(42)

    # Create pipelines for key services
    pipe_services = [
        "api-gateway", "event-bus", "threat-intel", "defence-mesh",
        "incident-commander", "ethical-reasoning", "observability",
    ]

    for svc in pipe_services:
        pipe = Pipeline(
            name=f"{svc}-pipeline",
            service=svc,
            description=f"CI/CD pipeline for {svc} service",
            canary_error_threshold_pct=round(rng.uniform(2, 8), 1),
            canary_latency_threshold_ms=round(rng.uniform(200, 600), 0),
        )
        PIPELINES[pipe.id] = pipe

    pipe_ids = list(PIPELINES.keys())

    # Simulate deployments
    for i in range(25):
        pid = rng.choice(pipe_ids)
        pipeline = PIPELINES[pid]
        version = f"{rng.randint(1, 3)}.{rng.randint(0, 15)}.{rng.randint(0, 99)}"
        env = rng.choices(
            [EnvironmentName.DEV, EnvironmentName.STAGING, EnvironmentName.PRODUCTION],
            weights=[0.4, 0.35, 0.25],
        )[0]

        dep = Deployment(
            pipeline_id=pid,
            service=pipeline.service,
            version=version,
            environment=env,
            started_at=(_now() - timedelta(hours=rng.randint(1, 720))).isoformat(),
        )

        _simulate_deployment(dep, pipeline)
        DEPLOYMENTS[dep.id] = dep

        # Update pipeline stats
        pipeline.total_deployments += 1
        if dep.status == DeploymentStatus.DEPLOYED:
            pipeline.successful_deployments += 1

    # Create some rollbacks
    deployed = [d for d in DEPLOYMENTS.values() if d.status == DeploymentStatus.DEPLOYED]
    for i in range(min(5, len(deployed))):
        dep = rng.choice(deployed)
        rb = Rollback(
            deployment_id=dep.id,
            trigger=rng.choice(list(RollbackTrigger)),
            rollback_to_version=f"{rng.randint(1, 2)}.{rng.randint(0, 10)}.{rng.randint(0, 50)}",
            reason=rng.choice([
                "Error rate exceeded SLO budget",
                "Canary health check failure",
                "Manual rollback requested by on-call",
                "Critical CVE discovered post-deploy",
                "Regression detected in integration tests",
            ]),
            verified=rng.random() < 0.8,
            duration_sec=round(rng.uniform(30, 300), 1),
        )
        ROLLBACKS[rb.id] = rb

    # Initialise environments
    for svc in SERVICES:
        if svc not in ENVIRONMENTS:
            ENVIRONMENTS[svc] = {}
        for env in EnvironmentName:
            if env.value not in ENVIRONMENTS[svc]:
                ENVIRONMENTS[svc][env.value] = EnvironmentState(
                    name=env,
                    current_version=f"1.{rng.randint(0, 5)}.{rng.randint(0, 20)}",
                    feature_flags={
                        "enhanced_logging": True,
                        "canary_enabled": env == EnvironmentName.PRODUCTION,
                        "debug_mode": env == EnvironmentName.DEV,
                    },
                    healthy=rng.random() < 0.95,
                )


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    active_deployments = sum(
        1 for d in DEPLOYMENTS.values()
        if d.status in (DeploymentStatus.BUILDING, DeploymentStatus.TESTING,
                        DeploymentStatus.SCANNING, DeploymentStatus.CANARY)
    )

    return {
        "status": "healthy",
        "service": "production-deployment-pipeline",
        "version": "1.0.0",
        "pipelines": len(PIPELINES),
        "total_deployments": len(DEPLOYMENTS),
        "active_deployments": active_deployments,
        "artifacts": len(ARTIFACTS),
        "scans": len(SCANS),
        "rollbacks": len(ROLLBACKS),
    }


# ---- Pipelines --------------------------------------------------------------

@app.post("/v1/pipelines", status_code=status.HTTP_201_CREATED)
async def create_pipeline(data: PipelineCreate):
    pipe = Pipeline(
        name=data.name, service=data.service,
        description=data.description, stages=data.stages,
        requires_approval=data.requires_approval,
        auto_canary=data.auto_canary,
        canary_error_threshold_pct=data.canary_error_threshold_pct,
        canary_latency_threshold_ms=data.canary_latency_threshold_ms,
        scan_policy=data.scan_policy,
    )
    PIPELINES[pipe.id] = pipe

    return {"id": pipe.id, "name": pipe.name, "stages": pipe.stages}


@app.get("/v1/pipelines")
async def list_pipelines(pipe_status: Optional[PipelineStatus] = Query(None, alias="status")):
    pipes = list(PIPELINES.values())
    if pipe_status:
        pipes = [p for p in pipes if p.status == pipe_status]

    return {
        "count": len(pipes),
        "pipelines": [
            {"id": p.id, "name": p.name, "service": p.service,
             "status": p.status.value, "stages": p.stages,
             "total_deployments": p.total_deployments,
             "success_rate_pct": round(p.successful_deployments / max(p.total_deployments, 1) * 100, 1)}
            for p in pipes
        ],
    }


@app.get("/v1/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    if pipeline_id not in PIPELINES:
        raise HTTPException(404, "Pipeline not found")
    return PIPELINES[pipeline_id].dict()


# ---- Deployments ------------------------------------------------------------

@app.post("/v1/deployments", status_code=status.HTTP_201_CREATED)
async def trigger_deployment(data: DeploymentTrigger):
    if data.pipeline_id not in PIPELINES:
        raise HTTPException(400, f"Pipeline '{data.pipeline_id}' not found")

    pipeline = PIPELINES[data.pipeline_id]

    dep = Deployment(
        pipeline_id=data.pipeline_id,
        service=pipeline.service,
        version=data.version,
        environment=data.environment,
    )

    _simulate_deployment(dep, pipeline)
    DEPLOYMENTS[dep.id] = dep

    pipeline.total_deployments += 1
    if dep.status == DeploymentStatus.DEPLOYED:
        pipeline.successful_deployments += 1

    return {
        "id": dep.id, "service": dep.service,
        "version": dep.version, "environment": dep.environment.value,
        "status": dep.status.value, "duration_sec": dep.duration_sec,
    }


@app.get("/v1/deployments")
async def list_deployments(
    service: Optional[str] = None,
    environment: Optional[EnvironmentName] = None,
    dep_status: Optional[DeploymentStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
):
    deps = list(DEPLOYMENTS.values())
    if service:
        deps = [d for d in deps if d.service == service]
    if environment:
        deps = [d for d in deps if d.environment == environment]
    if dep_status:
        deps = [d for d in deps if d.status == dep_status]

    deps = sorted(deps, key=lambda d: d.started_at, reverse=True)[:limit]

    return {
        "count": len(deps),
        "deployments": [
            {"id": d.id, "service": d.service, "version": d.version,
             "environment": d.environment.value, "status": d.status.value,
             "current_stage": d.current_stage, "duration_sec": d.duration_sec,
             "started_at": d.started_at, "completed_at": d.completed_at}
            for d in deps
        ],
    }


@app.get("/v1/deployments/{deployment_id}")
async def get_deployment(deployment_id: str):
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(404, "Deployment not found")

    dep = DEPLOYMENTS[deployment_id]
    return {
        **dep.dict(),
        "canary": dep.canary.dict(),
    }


@app.post("/v1/deployments/{deployment_id}/approve")
async def approve_deployment(deployment_id: str, approver: str = "manual"):
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(404, "Deployment not found")

    dep = DEPLOYMENTS[deployment_id]
    if dep.status != DeploymentStatus.AWAITING_APPROVAL:
        raise HTTPException(409, f"Deployment is not awaiting approval (status: {dep.status.value})")

    dep.approved_by = approver
    dep.approval_time = _now().isoformat()
    dep.status = DeploymentStatus.PROMOTING

    return {"id": deployment_id, "approved_by": approver, "status": "promoting"}


@app.post("/v1/deployments/{deployment_id}/rollback")
async def rollback_deployment(deployment_id: str, reason: str = "Manual rollback"):
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(404, "Deployment not found")

    dep = DEPLOYMENTS[deployment_id]
    dep.status = DeploymentStatus.ROLLED_BACK
    dep.completed_at = _now().isoformat()

    rb = Rollback(
        deployment_id=deployment_id,
        trigger=RollbackTrigger.MANUAL,
        reason=reason,
        rollback_to_version=dep.version,
        verified=True,
        duration_sec=round(_rng.uniform(15, 120), 1),
    )
    ROLLBACKS[rb.id] = rb

    return {"rollback_id": rb.id, "deployment_id": deployment_id,
            "status": "rolled_back", "duration_sec": rb.duration_sec}


@app.get("/v1/deployments/{deployment_id}/canary")
async def get_canary_status(deployment_id: str):
    if deployment_id not in DEPLOYMENTS:
        raise HTTPException(404, "Deployment not found")

    dep = DEPLOYMENTS[deployment_id]
    return {
        "deployment_id": deployment_id,
        "service": dep.service,
        "version": dep.version,
        **dep.canary.dict(),
    }


# ---- Scans ------------------------------------------------------------------

@app.post("/v1/scans/trigger", status_code=status.HTTP_201_CREATED)
async def trigger_scan(artifact_id: str, scan_type: ScanType):
    if artifact_id not in ARTIFACTS:
        raise HTTPException(404, "Artifact not found")

    artifact = ARTIFACTS[artifact_id]
    scans = _run_security_scans(artifact, "", "block_critical_warn_high")
    filtered = [s for s in scans if s.scan_type == scan_type]

    if filtered:
        scan = filtered[0]
        SCANS[scan.id] = scan
        return {"id": scan.id, "type": scan.scan_type.value, "passed": scan.passed,
                "findings": scan.findings_count}

    raise HTTPException(400, f"Scan type '{scan_type.value}' not available")


@app.get("/v1/scans")
async def list_scans(scan_type: Optional[ScanType] = None,
                     passed: Optional[bool] = None,
                     limit: int = Query(50, ge=1, le=200)):
    scans = list(SCANS.values())
    if scan_type:
        scans = [s for s in scans if s.scan_type == scan_type]
    if passed is not None:
        scans = [s for s in scans if s.passed == passed]

    scans = sorted(scans, key=lambda s: s.scanned_at, reverse=True)[:limit]

    return {
        "count": len(scans),
        "scans": [
            {"id": s.id, "type": s.scan_type.value, "scanner": s.scanner,
             "artifact": s.artifact_id, "findings": s.findings_count,
             "passed": s.passed, "scanned_at": s.scanned_at}
            for s in scans
        ],
    }


@app.get("/v1/scans/{scan_id}")
async def get_scan(scan_id: str):
    if scan_id not in SCANS:
        raise HTTPException(404, "Scan not found")
    return SCANS[scan_id].dict()


# ---- Environments -----------------------------------------------------------

@app.get("/v1/environments")
async def list_environments(service: Optional[str] = None):
    if service:
        envs = ENVIRONMENTS.get(service, {})
        return {
            "service": service,
            "environments": {
                name: {"version": e.current_version, "deployment": e.current_deployment_id,
                       "healthy": e.healthy, "last_deploy": e.last_deploy,
                       "feature_flags": e.feature_flags}
                for name, e in envs.items()
            },
        }

    return {
        "services": len(ENVIRONMENTS),
        "environments": {
            svc: {
                name: {"version": e.current_version, "healthy": e.healthy}
                for name, e in envs.items()
            }
            for svc, envs in ENVIRONMENTS.items()
        },
    }


# ---- Artifacts --------------------------------------------------------------

@app.get("/v1/artifacts")
async def list_artifacts(service: Optional[str] = None,
                         limit: int = Query(50, ge=1, le=200)):
    arts = list(ARTIFACTS.values())
    if service:
        arts = [a for a in arts if a.service == service]

    arts = sorted(arts, key=lambda a: a.created_at, reverse=True)[:limit]

    return {
        "count": len(arts),
        "artifacts": [
            {"id": a.id, "service": a.service, "version": a.version,
             "image_tag": a.image_tag, "sha256": a.sha256[:16] + "...",
             "size_mb": a.size_mb, "created_at": a.created_at}
            for a in arts
        ],
    }


# ---- Rollbacks --------------------------------------------------------------

@app.get("/v1/rollbacks")
async def list_rollbacks(limit: int = Query(50, ge=1, le=200)):
    rbs = sorted(ROLLBACKS.values(), key=lambda r: r.created_at, reverse=True)[:limit]

    return {
        "count": len(rbs),
        "rollbacks": [
            {"id": r.id, "deployment_id": r.deployment_id,
             "trigger": r.trigger.value, "reason": r.reason,
             "verified": r.verified, "duration_sec": r.duration_sec,
             "created_at": r.created_at}
            for r in rbs
        ],
    }


# ---- DORA Metrics -----------------------------------------------------------

@app.get("/v1/dora")
async def dora_metrics():
    """Compute DORA (DevOps Research and Assessment) metrics."""
    all_deps = list(DEPLOYMENTS.values())
    prod_deps = [d for d in all_deps if d.environment == EnvironmentName.PRODUCTION]
    successful_prod = [d for d in prod_deps if d.status == DeploymentStatus.DEPLOYED]
    failed_prod = [d for d in prod_deps if d.status in (DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK)]

    # 1. Deployment Frequency (per day over last 30 days)
    thirty_days_ago = (_now() - timedelta(days=30)).isoformat()
    recent_prod = [d for d in successful_prod if d.started_at >= thirty_days_ago]
    deployment_frequency = round(len(recent_prod) / 30, 2)

    # 2. Lead Time for Changes (build start → production deploy)
    lead_times = []
    for d in successful_prod:
        if d.duration_sec > 0:
            lead_times.append(d.duration_sec)

    avg_lead_time_sec = round(statistics.mean(lead_times), 1) if lead_times else 0
    median_lead_time_sec = round(statistics.median(lead_times), 1) if lead_times else 0

    # 3. Change Failure Rate
    total_changes = len(prod_deps) if prod_deps else 1
    change_failure_rate = round(len(failed_prod) / total_changes * 100, 2)

    # 4. Mean Time to Recovery
    recovery_times = [r.duration_sec for r in ROLLBACKS.values() if r.duration_sec > 0]
    mttr_sec = round(statistics.mean(recovery_times), 1) if recovery_times else 0

    # Classification
    def classify_frequency(f: float) -> str:
        if f >= 1: return "elite"
        if f >= 0.14: return "high"  # weekly
        if f >= 0.03: return "medium"  # monthly
        return "low"

    def classify_lead_time(t: float) -> str:
        if t < 3600: return "elite"  # < 1 hour
        if t < 86400: return "high"  # < 1 day
        if t < 604800: return "medium"  # < 1 week
        return "low"

    def classify_cfr(r: float) -> str:
        if r < 5: return "elite"
        if r < 10: return "high"
        if r < 15: return "medium"
        return "low"

    def classify_mttr(t: float) -> str:
        if t < 3600: return "elite"
        if t < 86400: return "high"
        if t < 604800: return "medium"
        return "low"

    return {
        "deployment_frequency": {
            "value": deployment_frequency,
            "unit": "deployments_per_day",
            "classification": classify_frequency(deployment_frequency),
            "period_days": 30,
        },
        "lead_time_for_changes": {
            "avg_seconds": avg_lead_time_sec,
            "median_seconds": median_lead_time_sec,
            "classification": classify_lead_time(avg_lead_time_sec),
        },
        "change_failure_rate": {
            "value_pct": change_failure_rate,
            "total_changes": total_changes,
            "failed_changes": len(failed_prod),
            "classification": classify_cfr(change_failure_rate),
        },
        "mean_time_to_recovery": {
            "seconds": mttr_sec,
            "classification": classify_mttr(mttr_sec),
            "rollbacks_measured": len(recovery_times),
        },
        "overall_classification": classify_frequency(deployment_frequency),
        "total_deployments": len(all_deps),
        "production_deployments": len(prod_deps),
    }


# ---- Analytics --------------------------------------------------------------

@app.get("/v1/analytics")
async def pipeline_analytics():
    total_deps = len(DEPLOYMENTS)
    by_status = Counter(d.status.value for d in DEPLOYMENTS.values())
    by_env = Counter(d.environment.value for d in DEPLOYMENTS.values())
    by_service = Counter(d.service for d in DEPLOYMENTS.values())

    # Scan statistics
    total_scans = len(SCANS)
    scan_pass_rate = round(
        sum(1 for s in SCANS.values() if s.passed) / max(total_scans, 1) * 100, 1)
    findings_by_severity = Counter()
    for scan in SCANS.values():
        for sev, count in scan.severity_counts.items():
            findings_by_severity[sev] += count

    # Pipeline success rates
    pipe_stats = {}
    for p in PIPELINES.values():
        pipe_stats[p.name] = {
            "total": p.total_deployments,
            "successful": p.successful_deployments,
            "success_rate_pct": round(p.successful_deployments / max(p.total_deployments, 1) * 100, 1),
        }

    # Deployment durations
    durations = [d.duration_sec for d in DEPLOYMENTS.values() if d.duration_sec > 0]

    return {
        "total_deployments": total_deps,
        "deployments_by_status": dict(by_status),
        "deployments_by_environment": dict(by_env),
        "deployments_by_service": dict(by_service),
        "avg_deployment_duration_sec": round(statistics.mean(durations), 1) if durations else 0,
        "total_scans": total_scans,
        "scan_pass_rate_pct": scan_pass_rate,
        "findings_by_severity": dict(findings_by_severity),
        "total_artifacts": len(ARTIFACTS),
        "total_rollbacks": len(ROLLBACKS),
        "pipeline_stats": pipe_stats,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9204)
