"""
End-to-End Test Harness — Core test orchestration server.

Comprehensive testing platform providing suite management, test case
execution, chaos engineering, regression detection, and compliance
reporting.  Validates every NAIL microservice individually and as an
integrated system before and after every deployment.
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
    title="NAIL End-to-End Test Harness",
    description=(
        "Test orchestration — suites, cases, chaos engineering, "
        "regression detection, and compliance reporting."
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

SERVICES = [
    "api-gateway", "event-bus", "threat-intel", "autonomous-redteam",
    "defence-mesh", "predictive-engine", "incident-commander",
    "ethical-reasoning", "civilisational-risk", "standards-evolution",
    "recursive-self-improvement", "temporal-forensics",
    "observability", "deployment-pipeline",
]


class SuiteType(str, Enum):
    SMOKE = "smoke"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    CHAOS = "chaos"
    COMPLIANCE = "compliance"


class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"


class AssertionType(str, Enum):
    STATUS_CODE = "status_code"
    JSON_PATH = "json_path"
    LATENCY_BOUND = "latency_bound"
    SCHEMA_VALIDATION = "schema_validation"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX_MATCH = "regex_match"


class FaultType(str, Enum):
    HTTP_500 = "http_500"
    TIMEOUT = "timeout"
    CONNECTION_REFUSED = "connection_refused"
    LATENCY_INJECTION = "latency_injection"
    PARTITION = "partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


COMPLIANCE_FRAMEWORKS = ["EU_AI_ACT", "NIST_AI_RMF", "ISO_27001", "ISO_42001", "SOC2_TYPE2"]

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class Assertion(BaseModel):
    type: AssertionType
    target: str = ""  # JSON path, header name, etc.
    expected: Any = None
    operator: str = "eq"  # eq, neq, gt, lt, gte, lte, contains, matches


class TestCase(BaseModel):
    id: str = Field(default_factory=lambda: f"TC-{uuid.uuid4().hex[:8].upper()}")
    suite_id: str = ""
    name: str
    description: str = ""
    endpoint: str = ""  # e.g., GET /v1/threats
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] = Field(default_factory=dict)
    assertions: list[Assertion] = Field(default_factory=list)
    setup_hook: str = ""  # Description of setup action
    teardown_hook: str = ""
    retry_count: int = 0
    max_retries: int = 3
    timeout_ms: int = 5000
    tags: list[str] = Field(default_factory=list)
    status: TestStatus = TestStatus.PENDING
    duration_ms: float = 0.0
    error_message: str = ""
    last_run: Optional[str] = None


class TestCaseCreate(BaseModel):
    name: str
    description: str = ""
    endpoint: str = ""
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] = Field(default_factory=dict)
    assertions: list[Assertion] = Field(default_factory=list)
    setup_hook: str = ""
    teardown_hook: str = ""
    max_retries: int = 3
    timeout_ms: int = 5000
    tags: list[str] = Field(default_factory=list)


class TestSuite(BaseModel):
    id: str = Field(default_factory=lambda: f"SUITE-{uuid.uuid4().hex[:8].upper()}")
    name: str
    suite_type: SuiteType = SuiteType.INTEGRATION
    description: str = ""
    service: str = ""
    dependencies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    test_case_ids: list[str] = Field(default_factory=list)
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SuiteCreate(BaseModel):
    name: str
    suite_type: SuiteType = SuiteType.INTEGRATION
    description: str = ""
    service: str = ""
    dependencies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)


class TestRun(BaseModel):
    id: str = Field(default_factory=lambda: f"RUN-{uuid.uuid4().hex[:8].upper()}")
    suite_id: str
    status: RunStatus = RunStatus.QUEUED
    environment: str = "dev"  # dev, staging, production
    dry_run: bool = False
    concurrency: int = 1
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_ms: float = 0.0
    case_results: list[dict[str, Any]] = Field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChaosExperiment(BaseModel):
    id: str = Field(default_factory=lambda: f"CHAOS-{uuid.uuid4().hex[:8].upper()}")
    name: str
    description: str = ""
    target_service: str = ""
    fault_type: FaultType = FaultType.LATENCY_INJECTION
    parameters: dict[str, Any] = Field(default_factory=dict)
    hypothesis: str = ""  # What we expect to happen
    blast_radius: float = Field(0.5, ge=0.0, le=1.0)  # % of traffic affected
    duration_sec: int = 60
    status: ExperimentStatus = ExperimentStatus.PENDING
    result_matches_hypothesis: Optional[bool] = None
    observations: list[str] = Field(default_factory=list)
    metrics_before: dict[str, float] = Field(default_factory=dict)
    metrics_after: dict[str, float] = Field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExperimentCreate(BaseModel):
    name: str
    description: str = ""
    target_service: str = ""
    fault_type: FaultType = FaultType.LATENCY_INJECTION
    parameters: dict[str, Any] = Field(default_factory=dict)
    hypothesis: str = ""
    blast_radius: float = 0.5
    duration_sec: int = 60


class Baseline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    suite_id: str
    run_id: str
    metrics: dict[str, float] = Field(default_factory=dict)
    captured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RegressionRule(BaseModel):
    id: str = Field(default_factory=lambda: f"REG-{uuid.uuid4().hex[:8].upper()}")
    suite_id: str
    metric_name: str
    threshold_pct: float = 10.0  # % degradation that triggers regression
    direction: str = "increase"  # increase (latency) or decrease (success rate)
    active: bool = True


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → PostgreSQL + Allure + Grafana)
# ---------------------------------------------------------------------------

SUITES: dict[str, TestSuite] = {}
CASES: dict[str, TestCase] = {}
RUNS: dict[str, TestRun] = {}
EXPERIMENTS: dict[str, ChaosExperiment] = {}
BASELINES: dict[str, Baseline] = {}  # suite_id → latest baseline
REGRESSION_RULES: list[RegressionRule] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731
_rng = random.Random(42)


def _execute_case(case: TestCase, dry_run: bool = False) -> dict[str, Any]:
    """Simulate executing a test case."""
    if dry_run:
        return {
            "case_id": case.id, "name": case.name,
            "status": "skipped", "duration_ms": 0,
            "message": "Dry run — skipped execution",
        }

    # Simulate execution with realistic outcomes
    latency = _rng.uniform(10, case.timeout_ms * 0.8)
    passed = _rng.random() < 0.88  # 88% pass rate for simulation

    case.duration_ms = round(latency, 2)
    case.last_run = _now().isoformat()

    if passed:
        case.status = TestStatus.PASSED
        return {
            "case_id": case.id, "name": case.name,
            "status": "passed", "duration_ms": case.duration_ms,
            "assertions_passed": len(case.assertions),
        }
    else:
        # Simulate failure with retry
        if case.retry_count < case.max_retries:
            case.retry_count += 1
            if _rng.random() < 0.6:  # 60% chance retry succeeds
                case.status = TestStatus.PASSED
                return {
                    "case_id": case.id, "name": case.name,
                    "status": "passed", "duration_ms": case.duration_ms,
                    "retries": case.retry_count,
                }

        case.status = TestStatus.FAILED
        failure_reasons = [
            "Assertion failed: status_code expected 200, got 500",
            "Assertion failed: response.threat_level expected 'critical', got 'high'",
            "Timeout: response exceeded 5000ms bound",
            "Schema validation: missing required field 'incident_id'",
            "JSON path $.data.score: expected >= 0.7, actual 0.42",
        ]
        case.error_message = _rng.choice(failure_reasons)

        return {
            "case_id": case.id, "name": case.name,
            "status": "failed", "duration_ms": case.duration_ms,
            "error": case.error_message,
            "retries": case.retry_count,
        }


def _execute_experiment(experiment: ChaosExperiment) -> None:
    """Simulate chaos experiment execution."""
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = _now().isoformat()

    # Capture before metrics
    experiment.metrics_before = {
        "error_rate_pct": round(_rng.uniform(0.5, 3.0), 2),
        "latency_p95_ms": round(_rng.uniform(50, 200), 2),
        "success_rate_pct": round(_rng.uniform(97, 99.9), 2),
        "throughput_rps": round(_rng.uniform(100, 1000), 1),
    }

    # Simulate fault injection
    observations = []

    if experiment.fault_type == FaultType.HTTP_500:
        observations.append(f"Injected HTTP 500 errors to {experiment.blast_radius * 100:.0f}% of {experiment.target_service} traffic")
        error_increase = experiment.blast_radius * _rng.uniform(20, 60)
        experiment.metrics_after = {
            "error_rate_pct": round(experiment.metrics_before["error_rate_pct"] + error_increase, 2),
            "latency_p95_ms": round(experiment.metrics_before["latency_p95_ms"] * 1.1, 2),
            "success_rate_pct": round(max(0, experiment.metrics_before["success_rate_pct"] - error_increase), 2),
            "throughput_rps": round(experiment.metrics_before["throughput_rps"] * 0.8, 1),
        }
        observations.append(f"Error rate increased by {error_increase:.1f}%")
        observations.append("Circuit breaker tripped after 5 consecutive failures")
        observations.append("Fallback handler activated")

    elif experiment.fault_type == FaultType.LATENCY_INJECTION:
        delay_ms = experiment.parameters.get("delay_ms", 2000)
        observations.append(f"Injected {delay_ms}ms latency to {experiment.blast_radius * 100:.0f}% of requests")
        experiment.metrics_after = {
            "error_rate_pct": round(experiment.metrics_before["error_rate_pct"] * 1.5, 2),
            "latency_p95_ms": round(experiment.metrics_before["latency_p95_ms"] + delay_ms * experiment.blast_radius, 2),
            "success_rate_pct": round(experiment.metrics_before["success_rate_pct"] - 2, 2),
            "throughput_rps": round(experiment.metrics_before["throughput_rps"] * 0.6, 1),
        }
        observations.append(f"P95 latency increased by {delay_ms * experiment.blast_radius:.0f}ms")
        observations.append("Timeout errors observed in downstream services")

    elif experiment.fault_type == FaultType.PARTITION:
        observations.append(f"Simulated network partition for {experiment.target_service}")
        experiment.metrics_after = {
            "error_rate_pct": round(experiment.metrics_before["error_rate_pct"] + 30, 2),
            "latency_p95_ms": round(experiment.metrics_before["latency_p95_ms"] * 3, 2),
            "success_rate_pct": round(max(0, experiment.metrics_before["success_rate_pct"] - 30), 2),
            "throughput_rps": round(experiment.metrics_before["throughput_rps"] * 0.3, 1),
        }
        observations.append("Service registry detected unhealthy backend")
        observations.append("Event bus queued messages for later delivery")
        observations.append("Retry mechanisms activated across dependent services")

    elif experiment.fault_type == FaultType.TIMEOUT:
        observations.append(f"Injected connection timeouts for {experiment.target_service}")
        experiment.metrics_after = {
            "error_rate_pct": round(experiment.metrics_before["error_rate_pct"] + 15, 2),
            "latency_p95_ms": round(experiment.metrics_before["latency_p95_ms"] * 2, 2),
            "success_rate_pct": round(max(0, experiment.metrics_before["success_rate_pct"] - 15), 2),
            "throughput_rps": round(experiment.metrics_before["throughput_rps"] * 0.5, 1),
        }
        observations.append("Circuit breaker opened for timed-out service")

    elif experiment.fault_type == FaultType.CONNECTION_REFUSED:
        observations.append(f"Simulated connection refused for {experiment.target_service}")
        experiment.metrics_after = {
            "error_rate_pct": round(experiment.metrics_before["error_rate_pct"] + 25, 2),
            "latency_p95_ms": experiment.metrics_before["latency_p95_ms"],
            "success_rate_pct": round(max(0, experiment.metrics_before["success_rate_pct"] - 25), 2),
            "throughput_rps": round(experiment.metrics_before["throughput_rps"] * 0.4, 1),
        }
        observations.append("Fast failure detected — no latency increase observed")

    else:  # RESOURCE_EXHAUSTION
        observations.append(f"Simulated memory pressure on {experiment.target_service}")
        experiment.metrics_after = {
            "error_rate_pct": round(experiment.metrics_before["error_rate_pct"] + 10, 2),
            "latency_p95_ms": round(experiment.metrics_before["latency_p95_ms"] * 2.5, 2),
            "success_rate_pct": round(max(0, experiment.metrics_before["success_rate_pct"] - 10), 2),
            "throughput_rps": round(experiment.metrics_before["throughput_rps"] * 0.5, 1),
        }
        observations.append("GC pressure observed, latency increased")

    # Evaluate hypothesis
    experiment.result_matches_hypothesis = _rng.random() < 0.7
    if experiment.result_matches_hypothesis:
        observations.append("✅ Hypothesis confirmed — system behaved as expected")
    else:
        observations.append("❌ Hypothesis rejected — unexpected system behaviour observed")

    experiment.observations = observations
    experiment.status = ExperimentStatus.COMPLETED
    experiment.completed_at = _now().isoformat()


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    rng = random.Random(42)

    # Create suites
    suite_defs = [
        ("API Gateway Smoke Tests", SuiteType.SMOKE, "api-gateway",
         "Quick health and auth verification for API gateway"),
        ("Event Bus Integration", SuiteType.INTEGRATION, "event-bus",
         "End-to-end publish/subscribe/consume flow"),
        ("Threat Pipeline Regression", SuiteType.REGRESSION, "threat-intel",
         "Regression tests for threat detection pipeline"),
        ("Defence Mesh Chaos", SuiteType.CHAOS, "defence-mesh",
         "Chaos experiments targeting defence mesh resilience"),
        ("EU AI Act Compliance", SuiteType.COMPLIANCE, "",
         "Compliance validation against EU AI Act requirements"),
        ("Incident Response E2E", SuiteType.INTEGRATION, "incident-commander",
         "Full incident lifecycle from detection to resolution"),
        ("Standards Voting Regression", SuiteType.REGRESSION, "standards-evolution",
         "Regression suite for standards proposal and voting"),
        ("Cross-Service Smoke", SuiteType.SMOKE, "",
         "Health check across all registered services"),
    ]

    for name, stype, svc, desc in suite_defs:
        suite = TestSuite(
            name=name, suite_type=stype, service=svc,
            description=desc, tags=[stype.value, svc or "cross-service"],
        )
        SUITES[suite.id] = suite

    suite_ids = list(SUITES.keys())

    # Create test cases for each suite
    case_templates = [
        ("Health endpoint responds 200", "GET /health", "GET",
         [Assertion(type=AssertionType.STATUS_CODE, expected=200)]),
        ("List resources returns array", "GET /v1/resources", "GET",
         [Assertion(type=AssertionType.STATUS_CODE, expected=200),
          Assertion(type=AssertionType.JSON_PATH, target="$.count", operator="gte", expected=0)]),
        ("Create resource returns 201", "POST /v1/resources", "POST",
         [Assertion(type=AssertionType.STATUS_CODE, expected=201)]),
        ("Response under 500ms", "GET /v1/analytics", "GET",
         [Assertion(type=AssertionType.LATENCY_BOUND, expected=500)]),
        ("Response matches schema", "GET /v1/details", "GET",
         [Assertion(type=AssertionType.SCHEMA_VALIDATION, target="response_schema.json")]),
        ("Error response contains message", "GET /v1/nonexistent", "GET",
         [Assertion(type=AssertionType.STATUS_CODE, expected=404),
          Assertion(type=AssertionType.CONTAINS, target="$.detail", expected="not found")]),
        ("Bulk operation processes all items", "POST /v1/bulk", "POST",
         [Assertion(type=AssertionType.STATUS_CODE, expected=201),
          Assertion(type=AssertionType.JSON_PATH, target="$.processed", operator="gt", expected=0)]),
        ("Auth required returns 401", "GET /v1/protected", "GET",
         [Assertion(type=AssertionType.STATUS_CODE, expected=401)]),
    ]

    for sid in suite_ids:
        suite = SUITES[sid]
        num_cases = rng.randint(3, 8)
        for i in range(num_cases):
            template = rng.choice(case_templates)
            case = TestCase(
                suite_id=sid,
                name=f"{template[0]} [{suite.service or 'cross'}]",
                endpoint=template[1],
                method=template[2],
                assertions=template[3],
                tags=[suite.suite_type.value],
                timeout_ms=rng.choice([3000, 5000, 10000]),
            )
            CASES[case.id] = case
            suite.test_case_ids.append(case.id)
            suite.total_cases += 1

    # Simulate some completed runs
    for i in range(15):
        sid = rng.choice(suite_ids)
        suite = SUITES[sid]
        run = TestRun(
            suite_id=sid,
            status=rng.choice([RunStatus.PASSED, RunStatus.PASSED, RunStatus.FAILED]),
            environment=rng.choice(["dev", "staging", "production"]),
            total_cases=suite.total_cases,
            started_at=(_now() - timedelta(hours=rng.randint(1, 168))).isoformat(),
        )

        # Simulate case results
        for cid in suite.test_case_ids:
            case = CASES[cid]
            result = _execute_case(case)
            run.case_results.append(result)
            if result["status"] == "passed":
                run.passed += 1
            elif result["status"] == "failed":
                run.failed += 1
            else:
                run.skipped += 1

        run.errors = sum(1 for r in run.case_results if r["status"] == "error")
        run.duration_ms = round(sum(r.get("duration_ms", 0) for r in run.case_results), 2)
        run.status = RunStatus.PASSED if run.failed == 0 else RunStatus.FAILED
        run.completed_at = (_now() - timedelta(hours=max(0, rng.randint(0, 167)))).isoformat()
        RUNS[run.id] = run

        # Update suite stats
        suite.passed = run.passed
        suite.failed = run.failed
        suite.skipped = run.skipped

    # Create chaos experiments
    exp_defs = [
        ("Gateway Circuit Breaker Test", "api-gateway", FaultType.HTTP_500,
         "Circuit breaker should trip after 5 failures and recover after 30s"),
        ("Event Bus Partition Resilience", "event-bus", FaultType.PARTITION,
         "Events should be queued and delivered after partition heals"),
        ("Defence Mesh Latency Tolerance", "defence-mesh", FaultType.LATENCY_INJECTION,
         "Defence orchestration should complete within SLO despite 2s latency injection"),
        ("Incident Commander Timeout Handling", "incident-commander", FaultType.TIMEOUT,
         "Incident commander should degrade gracefully under timeout conditions"),
        ("Threat Intel Memory Pressure", "threat-intel", FaultType.RESOURCE_EXHAUSTION,
         "Threat processing should shed load under memory pressure"),
    ]

    for name, target, fault, hypothesis in exp_defs:
        exp = ChaosExperiment(
            name=name, target_service=target, fault_type=fault,
            hypothesis=hypothesis, blast_radius=round(rng.uniform(0.1, 0.8), 2),
            duration_sec=rng.choice([30, 60, 120, 300]),
        )
        _execute_experiment(exp)
        EXPERIMENTS[exp.id] = exp

    # Create baselines
    for sid in suite_ids[:3]:
        runs_for_suite = [r for r in RUNS.values() if r.suite_id == sid and r.status == RunStatus.PASSED]
        if runs_for_suite:
            run = runs_for_suite[0]
            baseline = Baseline(
                suite_id=sid, run_id=run.id,
                metrics={
                    "pass_rate_pct": round(run.passed / max(run.total_cases, 1) * 100, 2),
                    "avg_duration_ms": round(run.duration_ms / max(run.total_cases, 1), 2),
                    "total_duration_ms": run.duration_ms,
                },
            )
            BASELINES[sid] = baseline

    # Regression rules
    for sid in suite_ids[:3]:
        REGRESSION_RULES.append(RegressionRule(
            suite_id=sid, metric_name="avg_duration_ms",
            threshold_pct=15.0, direction="increase",
        ))
        REGRESSION_RULES.append(RegressionRule(
            suite_id=sid, metric_name="pass_rate_pct",
            threshold_pct=5.0, direction="decrease",
        ))


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    total_cases = sum(s.total_cases for s in SUITES.values())
    total_experiments = len(EXPERIMENTS)

    return {
        "status": "healthy",
        "service": "end-to-end-test-harness",
        "version": "1.0.0",
        "suites": len(SUITES),
        "test_cases": total_cases,
        "runs": len(RUNS),
        "chaos_experiments": total_experiments,
        "baselines": len(BASELINES),
    }


# ---- Suites -----------------------------------------------------------------

@app.post("/v1/suites", status_code=status.HTTP_201_CREATED)
async def create_suite(data: SuiteCreate):
    suite = TestSuite(
        name=data.name, suite_type=data.suite_type,
        description=data.description, service=data.service,
        dependencies=data.dependencies, tags=data.tags,
        parameters=data.parameters,
    )
    SUITES[suite.id] = suite

    return {"id": suite.id, "name": suite.name, "type": suite.suite_type.value}


@app.get("/v1/suites")
async def list_suites(suite_type: Optional[SuiteType] = Query(None, alias="type"),
                      service: Optional[str] = None):
    suites = list(SUITES.values())
    if suite_type:
        suites = [s for s in suites if s.suite_type == suite_type]
    if service:
        suites = [s for s in suites if s.service == service]

    return {
        "count": len(suites),
        "suites": [
            {"id": s.id, "name": s.name, "type": s.suite_type.value,
             "service": s.service, "total_cases": s.total_cases,
             "passed": s.passed, "failed": s.failed, "skipped": s.skipped}
            for s in suites
        ],
    }


@app.get("/v1/suites/{suite_id}")
async def get_suite(suite_id: str):
    if suite_id not in SUITES:
        raise HTTPException(404, "Suite not found")

    suite = SUITES[suite_id]
    cases = [CASES[cid] for cid in suite.test_case_ids if cid in CASES]

    return {
        **suite.dict(),
        "cases": [
            {"id": c.id, "name": c.name, "status": c.status.value,
             "duration_ms": c.duration_ms, "endpoint": c.endpoint}
            for c in cases
        ],
    }


# ---- Test Cases -------------------------------------------------------------

@app.post("/v1/suites/{suite_id}/cases", status_code=status.HTTP_201_CREATED)
async def add_test_case(suite_id: str, data: TestCaseCreate):
    if suite_id not in SUITES:
        raise HTTPException(404, "Suite not found")

    case = TestCase(
        suite_id=suite_id, name=data.name,
        description=data.description, endpoint=data.endpoint,
        method=data.method, headers=data.headers,
        body=data.body, assertions=data.assertions,
        setup_hook=data.setup_hook, teardown_hook=data.teardown_hook,
        max_retries=data.max_retries, timeout_ms=data.timeout_ms,
        tags=data.tags,
    )
    CASES[case.id] = case
    SUITES[suite_id].test_case_ids.append(case.id)
    SUITES[suite_id].total_cases += 1

    return {"id": case.id, "name": case.name, "suite_id": suite_id}


@app.get("/v1/suites/{suite_id}/cases")
async def list_cases(suite_id: str):
    if suite_id not in SUITES:
        raise HTTPException(404, "Suite not found")

    suite = SUITES[suite_id]
    cases = [CASES[cid] for cid in suite.test_case_ids if cid in CASES]

    return {
        "suite_id": suite_id,
        "count": len(cases),
        "cases": [
            {"id": c.id, "name": c.name, "status": c.status.value,
             "endpoint": c.endpoint, "method": c.method,
             "assertions": len(c.assertions), "duration_ms": c.duration_ms}
            for c in cases
        ],
    }


# ---- Runs -------------------------------------------------------------------

@app.post("/v1/runs", status_code=status.HTTP_201_CREATED)
async def execute_run(
    suite_id: str,
    environment: str = "dev",
    dry_run: bool = False,
    concurrency: int = 1,
):
    if suite_id not in SUITES:
        raise HTTPException(404, "Suite not found")

    suite = SUITES[suite_id]
    run = TestRun(
        suite_id=suite_id, environment=environment,
        dry_run=dry_run, concurrency=concurrency,
        total_cases=suite.total_cases,
        started_at=_now().isoformat(),
    )
    run.status = RunStatus.RUNNING

    # Execute all test cases
    for cid in suite.test_case_ids:
        case = CASES.get(cid)
        if not case:
            continue
        result = _execute_case(case, dry_run=dry_run)
        run.case_results.append(result)
        if result["status"] == "passed":
            run.passed += 1
        elif result["status"] == "failed":
            run.failed += 1
        else:
            run.skipped += 1

    run.errors = sum(1 for r in run.case_results if r.get("status") == "error")
    run.duration_ms = round(sum(r.get("duration_ms", 0) for r in run.case_results), 2)
    run.status = RunStatus.PASSED if run.failed == 0 and run.errors == 0 else RunStatus.FAILED
    run.completed_at = _now().isoformat()

    RUNS[run.id] = run

    # Update suite stats
    suite.passed = run.passed
    suite.failed = run.failed
    suite.skipped = run.skipped

    return {
        "id": run.id, "suite_id": suite_id,
        "status": run.status.value, "environment": environment,
        "total": run.total_cases, "passed": run.passed,
        "failed": run.failed, "skipped": run.skipped,
        "duration_ms": run.duration_ms,
    }


@app.get("/v1/runs")
async def list_runs(suite_id: Optional[str] = None,
                    run_status: Optional[RunStatus] = Query(None, alias="status"),
                    limit: int = Query(50, ge=1, le=200)):
    runs = list(RUNS.values())
    if suite_id:
        runs = [r for r in runs if r.suite_id == suite_id]
    if run_status:
        runs = [r for r in runs if r.status == run_status]

    runs = sorted(runs, key=lambda r: r.created_at, reverse=True)[:limit]

    return {
        "count": len(runs),
        "runs": [
            {"id": r.id, "suite_id": r.suite_id, "status": r.status.value,
             "environment": r.environment, "total": r.total_cases,
             "passed": r.passed, "failed": r.failed,
             "duration_ms": r.duration_ms, "started_at": r.started_at}
            for r in runs
        ],
    }


@app.get("/v1/runs/{run_id}")
async def get_run(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(404, "Run not found")
    return RUNS[run_id].dict()


@app.get("/v1/runs/{run_id}/report")
async def get_run_report(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(404, "Run not found")

    run = RUNS[run_id]
    suite = SUITES.get(run.suite_id)

    failures = [r for r in run.case_results if r.get("status") == "failed"]
    pass_rate = round(run.passed / max(run.total_cases, 1) * 100, 2)

    return {
        "run_id": run_id,
        "suite": suite.name if suite else "unknown",
        "suite_type": suite.suite_type.value if suite else "unknown",
        "environment": run.environment,
        "status": run.status.value,
        "summary": {
            "total": run.total_cases,
            "passed": run.passed,
            "failed": run.failed,
            "skipped": run.skipped,
            "errors": run.errors,
            "pass_rate_pct": pass_rate,
            "duration_ms": run.duration_ms,
        },
        "failures": failures,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }


# ---- Chaos Experiments ------------------------------------------------------

@app.post("/v1/chaos/experiments", status_code=status.HTTP_201_CREATED)
async def create_experiment(data: ExperimentCreate):
    exp = ChaosExperiment(
        name=data.name, description=data.description,
        target_service=data.target_service, fault_type=data.fault_type,
        parameters=data.parameters, hypothesis=data.hypothesis,
        blast_radius=data.blast_radius, duration_sec=data.duration_sec,
    )
    EXPERIMENTS[exp.id] = exp

    return {"id": exp.id, "name": exp.name, "status": exp.status.value}


@app.get("/v1/chaos/experiments")
async def list_experiments(exp_status: Optional[ExperimentStatus] = Query(None, alias="status")):
    exps = list(EXPERIMENTS.values())
    if exp_status:
        exps = [e for e in exps if e.status == exp_status]

    return {
        "count": len(exps),
        "experiments": [
            {"id": e.id, "name": e.name, "target": e.target_service,
             "fault": e.fault_type.value, "status": e.status.value,
             "hypothesis_confirmed": e.result_matches_hypothesis,
             "blast_radius": e.blast_radius}
            for e in exps
        ],
    }


@app.post("/v1/chaos/experiments/{experiment_id}/run")
async def run_experiment(experiment_id: str):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(404, "Experiment not found")

    exp = EXPERIMENTS[experiment_id]
    if exp.status == ExperimentStatus.RUNNING:
        raise HTTPException(409, "Experiment already running")

    # Reset and re-execute
    exp.status = ExperimentStatus.PENDING
    exp.observations = []
    exp.metrics_before = {}
    exp.metrics_after = {}
    _execute_experiment(exp)

    return {
        "id": exp.id, "name": exp.name,
        "status": exp.status.value,
        "hypothesis_confirmed": exp.result_matches_hypothesis,
        "observations": exp.observations,
        "metrics_before": exp.metrics_before,
        "metrics_after": exp.metrics_after,
    }


@app.get("/v1/chaos/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(404, "Experiment not found")
    return EXPERIMENTS[experiment_id].dict()


# ---- Baselines & Regressions -----------------------------------------------

@app.get("/v1/baselines")
async def list_baselines():
    return {
        "count": len(BASELINES),
        "baselines": [
            {"suite_id": b.suite_id, "run_id": b.run_id,
             "metrics": b.metrics, "captured_at": b.captured_at}
            for b in BASELINES.values()
        ],
    }


@app.post("/v1/baselines/{suite_id}/capture")
async def capture_baseline(suite_id: str, run_id: str):
    if suite_id not in SUITES:
        raise HTTPException(404, "Suite not found")
    if run_id not in RUNS:
        raise HTTPException(404, "Run not found")

    run = RUNS[run_id]
    baseline = Baseline(
        suite_id=suite_id, run_id=run_id,
        metrics={
            "pass_rate_pct": round(run.passed / max(run.total_cases, 1) * 100, 2),
            "avg_duration_ms": round(run.duration_ms / max(run.total_cases, 1), 2),
            "total_duration_ms": run.duration_ms,
        },
    )
    BASELINES[suite_id] = baseline

    return {"suite_id": suite_id, "baseline": baseline.dict()}


@app.get("/v1/regressions")
async def check_regressions():
    regressions = []
    for rule in REGRESSION_RULES:
        if not rule.active:
            continue
        baseline = BASELINES.get(rule.suite_id)
        if not baseline:
            continue

        # Find latest run for this suite
        runs = sorted(
            [r for r in RUNS.values() if r.suite_id == rule.suite_id],
            key=lambda r: r.created_at, reverse=True,
        )
        if not runs:
            continue

        latest = runs[0]
        current_metrics = {
            "pass_rate_pct": round(latest.passed / max(latest.total_cases, 1) * 100, 2),
            "avg_duration_ms": round(latest.duration_ms / max(latest.total_cases, 1), 2),
            "total_duration_ms": latest.duration_ms,
        }

        baseline_val = baseline.metrics.get(rule.metric_name, 0)
        current_val = current_metrics.get(rule.metric_name, 0)

        if baseline_val == 0:
            continue

        if rule.direction == "increase":
            change_pct = ((current_val - baseline_val) / baseline_val) * 100
            is_regression = change_pct > rule.threshold_pct
        else:  # decrease
            change_pct = ((baseline_val - current_val) / baseline_val) * 100
            is_regression = change_pct > rule.threshold_pct

        if is_regression:
            regressions.append({
                "rule_id": rule.id,
                "suite_id": rule.suite_id,
                "metric": rule.metric_name,
                "baseline_value": baseline_val,
                "current_value": current_val,
                "change_pct": round(change_pct, 2),
                "threshold_pct": rule.threshold_pct,
                "direction": rule.direction,
                "regression": True,
            })

    return {"regressions_detected": len(regressions), "regressions": regressions}


# ---- Coverage ---------------------------------------------------------------

@app.get("/v1/coverage")
async def coverage_matrix():
    # Service-level coverage
    service_coverage = {}
    for svc in SERVICES:
        svc_suites = [s for s in SUITES.values() if s.service == svc]
        svc_cases = sum(s.total_cases for s in svc_suites)
        svc_passed = sum(s.passed for s in svc_suites)
        suite_types_covered = list(set(s.suite_type.value for s in svc_suites))

        service_coverage[svc] = {
            "suites": len(svc_suites),
            "test_cases": svc_cases,
            "passed": svc_passed,
            "coverage_pct": round(svc_passed / max(svc_cases, 1) * 100, 2),
            "suite_types": suite_types_covered,
            "missing_types": [st.value for st in SuiteType if st.value not in suite_types_covered],
        }

    # Compliance coverage
    compliance_suites = [s for s in SUITES.values() if s.suite_type == SuiteType.COMPLIANCE]

    return {
        "total_services": len(SERVICES),
        "services_with_tests": sum(1 for c in service_coverage.values() if c["test_cases"] > 0),
        "total_suites": len(SUITES),
        "total_cases": sum(s.total_cases for s in SUITES.values()),
        "service_coverage": service_coverage,
        "compliance_suites": len(compliance_suites),
        "frameworks_covered": COMPLIANCE_FRAMEWORKS,
    }


# ---- Analytics --------------------------------------------------------------

@app.get("/v1/analytics")
async def harness_analytics():
    # Run statistics
    total_runs = len(RUNS)
    passed_runs = sum(1 for r in RUNS.values() if r.status == RunStatus.PASSED)
    failed_runs = sum(1 for r in RUNS.values() if r.status == RunStatus.FAILED)

    # Case statistics
    total_cases_executed = sum(r.total_cases for r in RUNS.values())
    total_passed = sum(r.passed for r in RUNS.values())
    total_failed = sum(r.failed for r in RUNS.values())

    # Flakiness detection
    case_outcomes: dict[str, list[str]] = defaultdict(list)
    for run in RUNS.values():
        for result in run.case_results:
            case_outcomes[result.get("case_id", "")].append(result.get("status", ""))

    flaky_cases = []
    for cid, outcomes in case_outcomes.items():
        if len(outcomes) >= 3:
            unique = set(outcomes)
            if "passed" in unique and "failed" in unique:
                flaky_pct = outcomes.count("failed") / len(outcomes) * 100
                flaky_cases.append({"case_id": cid, "flakiness_pct": round(flaky_pct, 1),
                                    "runs": len(outcomes)})

    # Chaos summary
    confirmed = sum(1 for e in EXPERIMENTS.values() if e.result_matches_hypothesis is True)
    rejected = sum(1 for e in EXPERIMENTS.values() if e.result_matches_hypothesis is False)

    # Run durations
    durations = [r.duration_ms for r in RUNS.values() if r.duration_ms > 0]

    return {
        "total_runs": total_runs,
        "passed_runs": passed_runs,
        "failed_runs": failed_runs,
        "run_pass_rate_pct": round(passed_runs / max(total_runs, 1) * 100, 2),
        "total_cases_executed": total_cases_executed,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "case_pass_rate_pct": round(total_passed / max(total_cases_executed, 1) * 100, 2),
        "avg_run_duration_ms": round(statistics.mean(durations), 2) if durations else 0,
        "flaky_cases": sorted(flaky_cases, key=lambda x: x["flakiness_pct"], reverse=True)[:10],
        "chaos_experiments": len(EXPERIMENTS),
        "chaos_hypotheses_confirmed": confirmed,
        "chaos_hypotheses_rejected": rejected,
        "regressions_rules": len(REGRESSION_RULES),
        "baselines_captured": len(BASELINES),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9203)
