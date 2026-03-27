"""
Observability Stack — Core observability server.

Unified observability platform providing distributed tracing, metric
aggregation, log correlation, SLO management with error budgets,
and alerting.  Every NAIL microservice sends telemetry here, and
operators get a single-pane-of-glass view over the entire estate.
"""

from __future__ import annotations

import math
import random
import statistics
import uuid
from collections import Counter, defaultdict, deque
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
    title="NAIL Observability Stack",
    description=(
        "Distributed tracing, metric aggregation, log correlation, "
        "SLO management, alerting, and health dashboard."
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
    "test-harness", "deployment-pipeline",
]


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class AlertState(str, Enum):
    FIRING = "firing"
    PENDING = "pending"
    RESOLVED = "resolved"


class NotificationChannel(str, Enum):
    WEBHOOK = "webhook"
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

# ---- Tracing ----

class Span(BaseModel):
    span_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    trace_id: str = ""
    parent_span_id: str = ""
    operation: str = ""
    service: str = ""
    duration_ms: float = 0.0
    status: SpanStatus = SpanStatus.OK
    attributes: dict[str, Any] = Field(default_factory=dict)
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: str = ""


class SpanIngest(BaseModel):
    trace_id: str = ""
    parent_span_id: str = ""
    operation: str
    service: str
    duration_ms: float
    status: SpanStatus = SpanStatus.OK
    attributes: dict[str, Any] = Field(default_factory=dict)


class Trace(BaseModel):
    trace_id: str
    root_service: str = ""
    root_operation: str = ""
    span_count: int = 0
    total_duration_ms: float = 0.0
    has_error: bool = False
    services_involved: list[str] = Field(default_factory=list)
    started_at: str = ""


# ---- Metrics ----

class MetricPoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    metric_type: MetricType = MetricType.GAUGE
    service: str = ""
    value: float = 0.0
    labels: dict[str, str] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MetricIngest(BaseModel):
    name: str
    metric_type: MetricType = MetricType.GAUGE
    service: str = ""
    value: float
    labels: dict[str, str] = Field(default_factory=dict)


# ---- Logs ----

class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    level: LogLevel = LogLevel.INFO
    service: str = ""
    trace_id: str = ""
    span_id: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LogIngest(BaseModel):
    message: str
    level: LogLevel = LogLevel.INFO
    service: str = ""
    trace_id: str = ""
    span_id: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)


# ---- SLOs ----

class SLO(BaseModel):
    id: str = Field(default_factory=lambda: f"SLO-{uuid.uuid4().hex[:8].upper()}")
    name: str
    service: str
    description: str = ""
    target_type: str = "availability"  # availability, latency, error_rate
    target_value: float = 99.9  # e.g., 99.9% availability
    window_days: int = 30
    current_value: float = 100.0
    error_budget_total: float = 0.1  # 100 - target (%)
    error_budget_remaining: float = 0.1
    burn_rate: float = 0.0  # Current burn rate multiplier
    burn_rate_threshold: float = 2.0  # Alert when > 2×
    status: str = "healthy"  # healthy, warning, critical
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SLOCreate(BaseModel):
    name: str
    service: str
    description: str = ""
    target_type: str = "availability"
    target_value: float = 99.9
    window_days: int = 30
    burn_rate_threshold: float = 2.0


# ---- Alerts ----

class AlertRule(BaseModel):
    id: str = Field(default_factory=lambda: f"ALERT-{uuid.uuid4().hex[:8].upper()}")
    name: str
    description: str = ""
    condition: str = ""  # e.g., "error_rate > 5%"
    metric_name: str = ""
    slo_id: str = ""
    threshold: float = 0.0
    comparison: str = "gt"  # gt, lt, gte, lte, eq
    duration_sec: int = 60
    state: AlertState = AlertState.RESOLVED
    notification_channels: list[NotificationChannel] = Field(default_factory=list)
    group: str = ""
    silenced_until: Optional[str] = None
    last_fired: Optional[str] = None
    fire_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AlertCreate(BaseModel):
    name: str
    description: str = ""
    condition: str = ""
    metric_name: str = ""
    slo_id: str = ""
    threshold: float = 0.0
    comparison: str = "gt"
    duration_sec: int = 60
    notification_channels: list[NotificationChannel] = Field(default_factory=list)
    group: str = ""


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → Tempo + Prometheus + Loki + Grafana)
# ---------------------------------------------------------------------------

SPANS: dict[str, Span] = {}  # span_id → Span
TRACES: dict[str, Trace] = {}  # trace_id → Trace
METRICS: list[MetricPoint] = []
METRIC_SERIES: dict[str, list[MetricPoint]] = defaultdict(list)  # name → points
LOGS: list[LogEntry] = []
SLOS: dict[str, SLO] = {}
ALERTS: dict[str, AlertRule] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731
_rng = random.Random(42)


def _assemble_trace(trace_id: str) -> Trace:
    """Assemble a trace from its spans."""
    spans = [s for s in SPANS.values() if s.trace_id == trace_id]
    if not spans:
        return Trace(trace_id=trace_id)

    root = next((s for s in spans if not s.parent_span_id), spans[0])
    services = list(set(s.service for s in spans))
    has_error = any(s.status == SpanStatus.ERROR for s in spans)
    total = sum(s.duration_ms for s in spans)

    trace = Trace(
        trace_id=trace_id,
        root_service=root.service,
        root_operation=root.operation,
        span_count=len(spans),
        total_duration_ms=round(total, 2),
        has_error=has_error,
        services_involved=services,
        started_at=root.start_time,
    )
    TRACES[trace_id] = trace
    return trace


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * pct / 100)
    idx = min(idx, len(sorted_vals) - 1)
    return round(sorted_vals[idx], 2)


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    rng = random.Random(42)

    # Generate traces with spans
    for i in range(80):
        trace_id = uuid.uuid4().hex[:32]
        service = rng.choice(SERVICES)
        num_spans = rng.randint(2, 8)

        parent_id = ""
        for j in range(num_spans):
            svc = service if j == 0 else rng.choice(SERVICES)
            span = Span(
                trace_id=trace_id,
                parent_span_id=parent_id,
                operation=rng.choice([
                    "GET /health", "POST /v1/threats", "POST /v1/incidents",
                    "GET /v1/defences", "POST /v1/trust/evaluate",
                    "POST /v1/events/publish", "GET /v1/analytics",
                    "POST /v1/predict", "GET /v1/metrics",
                ]),
                service=svc,
                duration_ms=round(rng.uniform(1, 500), 2),
                status=rng.choices(
                    [SpanStatus.OK, SpanStatus.ERROR],
                    weights=[0.92, 0.08],
                )[0],
                attributes={"http.method": "GET" if rng.random() > 0.4 else "POST",
                             "http.status_code": rng.choice([200, 200, 201, 400, 500])},
                start_time=(_now() - timedelta(minutes=rng.randint(1, 1440))).isoformat(),
            )
            SPANS[span.span_id] = span
            parent_id = span.span_id

        _assemble_trace(trace_id)

    # Generate metrics
    metric_defs = [
        ("request_count", MetricType.COUNTER),
        ("error_count", MetricType.COUNTER),
        ("request_latency_ms", MetricType.HISTOGRAM),
        ("active_connections", MetricType.GAUGE),
        ("memory_usage_mb", MetricType.GAUGE),
        ("cpu_usage_pct", MetricType.GAUGE),
        ("queue_depth", MetricType.GAUGE),
    ]

    for svc in SERVICES:
        for name, mtype in metric_defs:
            for t in range(20):
                if mtype == MetricType.COUNTER:
                    value = rng.randint(10, 10000)
                elif name == "request_latency_ms":
                    value = round(rng.uniform(5, 300), 2)
                elif name == "memory_usage_mb":
                    value = round(rng.uniform(64, 512), 2)
                elif name == "cpu_usage_pct":
                    value = round(rng.uniform(5, 85), 2)
                elif name == "active_connections":
                    value = rng.randint(1, 200)
                else:
                    value = round(rng.uniform(0, 100), 2)

                point = MetricPoint(
                    name=name, metric_type=mtype, service=svc,
                    value=value, labels={"env": "production"},
                    timestamp=(_now() - timedelta(minutes=t)).isoformat(),
                )
                METRICS.append(point)
                METRIC_SERIES[f"{svc}:{name}"].append(point)

    # Generate logs
    log_msgs = [
        ("Request processed successfully", LogLevel.INFO),
        ("Authentication token refreshed", LogLevel.INFO),
        ("Cache miss for key", LogLevel.DEBUG),
        ("Retrying failed request", LogLevel.WARN),
        ("Connection timeout to upstream", LogLevel.ERROR),
        ("Rate limit exceeded for consumer", LogLevel.WARN),
        ("Deployment verification passed", LogLevel.INFO),
        ("Circuit breaker tripped", LogLevel.ERROR),
        ("Health check failed", LogLevel.ERROR),
        ("Schema validation error", LogLevel.WARN),
        ("Event replay completed", LogLevel.INFO),
        ("Background task started", LogLevel.DEBUG),
    ]

    trace_ids = list(TRACES.keys())
    for i in range(300):
        msg, level = rng.choice(log_msgs)
        svc = rng.choice(SERVICES)
        tid = rng.choice(trace_ids) if trace_ids and rng.random() > 0.3 else ""

        log = LogEntry(
            message=f"{msg} [{i + 1}]",
            level=level,
            service=svc,
            trace_id=tid,
            attributes={"request_id": str(uuid.uuid4())[:8]},
            timestamp=(_now() - timedelta(minutes=rng.randint(0, 1440))).isoformat(),
        )
        LOGS.append(log)

    # SLOs
    slo_defs = [
        ("API Gateway Availability", "api-gateway", "availability", 99.95, 99.97),
        ("API Gateway Latency P95", "api-gateway", "latency", 200.0, 185.0),
        ("Event Bus Availability", "event-bus", "availability", 99.99, 99.995),
        ("Threat Intel Error Rate", "threat-intel", "error_rate", 1.0, 0.8),
        ("Incident Commander Availability", "incident-commander", "availability", 99.9, 99.92),
        ("Defence Mesh Latency P99", "defence-mesh", "latency", 500.0, 420.0),
    ]

    for name, svc, target_type, target, current in slo_defs:
        error_budget = round(100 - target, 4) if target_type == "availability" else round(target * 0.1, 4)
        budget_remaining = round(error_budget * rng.uniform(0.2, 0.95), 4)
        burn_rate = round(rng.uniform(0.3, 3.5), 2)

        slo = SLO(
            name=name, service=svc, target_type=target_type,
            target_value=target, current_value=current,
            error_budget_total=error_budget,
            error_budget_remaining=budget_remaining,
            burn_rate=burn_rate,
            burn_rate_threshold=2.0,
            status="critical" if burn_rate > 2.0 else ("warning" if burn_rate > 1.5 else "healthy"),
        )
        SLOS[slo.id] = slo

    # Alerts
    alert_defs = [
        ("High Error Rate", "error_rate > 5%", "error_count", 5.0, "gt",
         [NotificationChannel.SLACK, NotificationChannel.PAGERDUTY], "errors"),
        ("High Latency P95", "latency_p95 > 300ms", "request_latency_ms", 300.0, "gt",
         [NotificationChannel.SLACK], "performance"),
        ("Low Availability SLO Breach", "availability < 99.9%", "", 99.9, "lt",
         [NotificationChannel.PAGERDUTY, NotificationChannel.EMAIL], "slo"),
        ("High Memory Usage", "memory > 80%", "memory_usage_mb", 80.0, "gt",
         [NotificationChannel.WEBHOOK], "resources"),
        ("Error Budget Exhausted", "error_budget_remaining < 10%", "", 10.0, "lt",
         [NotificationChannel.PAGERDUTY, NotificationChannel.SLACK], "slo"),
    ]

    states = [AlertState.FIRING, AlertState.RESOLVED, AlertState.RESOLVED,
              AlertState.PENDING, AlertState.RESOLVED]

    for i, (name, cond, metric, thresh, comp, channels, group) in enumerate(alert_defs):
        alert = AlertRule(
            name=name, condition=cond, metric_name=metric,
            threshold=thresh, comparison=comp,
            notification_channels=channels, group=group,
            state=states[i],
            fire_count=rng.randint(0, 25),
            last_fired=(_now() - timedelta(hours=rng.randint(1, 48))).isoformat() if states[i] != AlertState.RESOLVED else None,
        )
        ALERTS[alert.id] = alert


_seed()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "observability-stack",
        "version": "1.0.0",
        "traces": len(TRACES),
        "spans": len(SPANS),
        "metric_points": len(METRICS),
        "logs": len(LOGS),
        "slos": len(SLOS),
        "alerts": len(ALERTS),
        "firing_alerts": sum(1 for a in ALERTS.values() if a.state == AlertState.FIRING),
    }


# ---- Tracing ----------------------------------------------------------------

@app.post("/v1/traces/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_spans(spans: list[SpanIngest]):
    results = []
    for s in spans:
        trace_id = s.trace_id or uuid.uuid4().hex[:32]
        span = Span(
            trace_id=trace_id,
            parent_span_id=s.parent_span_id,
            operation=s.operation,
            service=s.service,
            duration_ms=s.duration_ms,
            status=s.status,
            attributes=s.attributes,
        )
        SPANS[span.span_id] = span
        _assemble_trace(trace_id)
        results.append({"span_id": span.span_id, "trace_id": trace_id})

    return {"ingested": len(results), "spans": results}


@app.get("/v1/traces")
async def search_traces(
    service: Optional[str] = None,
    has_error: Optional[bool] = None,
    min_duration_ms: Optional[float] = None,
    limit: int = Query(50, ge=1, le=500),
):
    traces = list(TRACES.values())
    if service:
        traces = [t for t in traces if service in t.services_involved]
    if has_error is not None:
        traces = [t for t in traces if t.has_error == has_error]
    if min_duration_ms is not None:
        traces = [t for t in traces if t.total_duration_ms >= min_duration_ms]

    traces = sorted(traces, key=lambda t: t.started_at, reverse=True)[:limit]

    return {
        "count": len(traces),
        "traces": [
            {"trace_id": t.trace_id, "root_service": t.root_service,
             "root_operation": t.root_operation, "span_count": t.span_count,
             "duration_ms": t.total_duration_ms, "has_error": t.has_error,
             "services": t.services_involved, "started_at": t.started_at}
            for t in traces
        ],
    }


@app.get("/v1/traces/{trace_id}")
async def get_trace(trace_id: str):
    trace = TRACES.get(trace_id)
    if not trace:
        raise HTTPException(404, "Trace not found")

    spans = sorted(
        [s for s in SPANS.values() if s.trace_id == trace_id],
        key=lambda s: s.start_time,
    )

    return {
        "trace_id": trace.trace_id,
        "root_service": trace.root_service,
        "root_operation": trace.root_operation,
        "total_duration_ms": trace.total_duration_ms,
        "has_error": trace.has_error,
        "services_involved": trace.services_involved,
        "span_count": len(spans),
        "spans": [
            {"span_id": s.span_id, "parent": s.parent_span_id,
             "operation": s.operation, "service": s.service,
             "duration_ms": s.duration_ms, "status": s.status.value,
             "start_time": s.start_time}
            for s in spans
        ],
    }


# ---- Metrics ----------------------------------------------------------------

@app.post("/v1/metrics/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_metrics(points: list[MetricIngest]):
    results = []
    for p in points:
        point = MetricPoint(
            name=p.name, metric_type=p.metric_type,
            service=p.service, value=p.value, labels=p.labels,
        )
        METRICS.append(point)
        METRIC_SERIES[f"{p.service}:{p.name}"].append(point)
        results.append({"id": point.id, "name": p.name})

    if len(METRICS) > 50000:
        METRICS[:] = METRICS[-50000:]

    return {"ingested": len(results), "points": results}


@app.get("/v1/metrics")
async def query_metrics(
    name: Optional[str] = None,
    service: Optional[str] = None,
    metric_type: Optional[MetricType] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    points = METRICS[-5000:]
    if name:
        points = [p for p in points if p.name == name]
    if service:
        points = [p for p in points if p.service == service]
    if metric_type:
        points = [p for p in points if p.metric_type == metric_type]

    points = points[-limit:]

    return {
        "count": len(points),
        "points": [
            {"id": p.id, "name": p.name, "type": p.metric_type.value,
             "service": p.service, "value": p.value,
             "labels": p.labels, "timestamp": p.timestamp}
            for p in points
        ],
    }


@app.get("/v1/metrics/service/{service_name}")
async def service_metrics(service_name: str):
    """Aggregated metrics for a specific service."""
    svc_metrics = [p for p in METRICS if p.service == service_name]
    if not svc_metrics:
        raise HTTPException(404, f"No metrics found for service '{service_name}'")

    by_name: dict[str, list[float]] = defaultdict(list)
    for p in svc_metrics:
        by_name[p.name].append(p.value)

    aggregated = {}
    for name, values in by_name.items():
        aggregated[name] = {
            "count": len(values),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "mean": round(statistics.mean(values), 2),
            "p50": _percentile(values, 50),
            "p95": _percentile(values, 95),
            "p99": _percentile(values, 99),
        }

    return {"service": service_name, "metrics": aggregated}


# ---- Logs -------------------------------------------------------------------

@app.post("/v1/logs/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_logs(entries: list[LogIngest]):
    results = []
    for l in entries:
        log = LogEntry(
            message=l.message, level=l.level, service=l.service,
            trace_id=l.trace_id, span_id=l.span_id, attributes=l.attributes,
        )
        LOGS.append(log)
        results.append({"id": log.id, "level": l.level.value})

    if len(LOGS) > 50000:
        LOGS[:] = LOGS[-50000:]

    return {"ingested": len(results), "logs": results}


@app.get("/v1/logs")
async def search_logs(
    service: Optional[str] = None,
    level: Optional[LogLevel] = None,
    query: Optional[str] = None,
    trace_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    logs = list(LOGS)
    if service:
        logs = [l for l in logs if l.service == service]
    if level:
        logs = [l for l in logs if l.level == level]
    if query:
        q = query.lower()
        logs = [l for l in logs if q in l.message.lower()]
    if trace_id:
        logs = [l for l in logs if l.trace_id == trace_id]

    logs = sorted(logs, key=lambda l: l.timestamp, reverse=True)[:limit]

    return {
        "count": len(logs),
        "logs": [
            {"id": l.id, "message": l.message, "level": l.level.value,
             "service": l.service, "trace_id": l.trace_id,
             "span_id": l.span_id, "timestamp": l.timestamp}
            for l in logs
        ],
    }


@app.get("/v1/logs/by-trace/{trace_id}")
async def logs_by_trace(trace_id: str):
    logs = sorted(
        [l for l in LOGS if l.trace_id == trace_id],
        key=lambda l: l.timestamp,
    )
    return {
        "trace_id": trace_id,
        "count": len(logs),
        "logs": [
            {"id": l.id, "message": l.message, "level": l.level.value,
             "service": l.service, "timestamp": l.timestamp}
            for l in logs
        ],
    }


# ---- SLOs -------------------------------------------------------------------

@app.post("/v1/slos", status_code=status.HTTP_201_CREATED)
async def create_slo(data: SLOCreate):
    error_budget = round(100 - data.target_value, 4) if data.target_type == "availability" else round(data.target_value * 0.1, 4)

    slo = SLO(
        name=data.name, service=data.service,
        description=data.description,
        target_type=data.target_type,
        target_value=data.target_value,
        window_days=data.window_days,
        current_value=data.target_value,  # Start at target
        error_budget_total=error_budget,
        error_budget_remaining=error_budget,
        burn_rate_threshold=data.burn_rate_threshold,
    )
    SLOS[slo.id] = slo

    return {"id": slo.id, "name": slo.name, "target": slo.target_value}


@app.get("/v1/slos")
async def list_slos(service: Optional[str] = None,
                    slo_status: Optional[str] = Query(None, alias="status")):
    slos = list(SLOS.values())
    if service:
        slos = [s for s in slos if s.service == service]
    if slo_status:
        slos = [s for s in slos if s.status == slo_status]

    return {
        "count": len(slos),
        "slos": [
            {"id": s.id, "name": s.name, "service": s.service,
             "target_type": s.target_type, "target": s.target_value,
             "current": s.current_value, "status": s.status,
             "error_budget_remaining_pct": round(s.error_budget_remaining / max(s.error_budget_total, 0.0001) * 100, 1),
             "burn_rate": s.burn_rate}
            for s in slos
        ],
    }


@app.get("/v1/slos/{slo_id}")
async def get_slo(slo_id: str):
    if slo_id not in SLOS:
        raise HTTPException(404, "SLO not found")
    slo = SLOS[slo_id]
    return {
        **slo.dict(),
        "error_budget_remaining_pct": round(
            slo.error_budget_remaining / max(slo.error_budget_total, 0.0001) * 100, 1),
        "burn_rate_alert": slo.burn_rate > slo.burn_rate_threshold,
    }


# ---- Alerts -----------------------------------------------------------------

@app.post("/v1/alerts", status_code=status.HTTP_201_CREATED)
async def create_alert(data: AlertCreate):
    alert = AlertRule(
        name=data.name, description=data.description,
        condition=data.condition, metric_name=data.metric_name,
        slo_id=data.slo_id, threshold=data.threshold,
        comparison=data.comparison, duration_sec=data.duration_sec,
        notification_channels=data.notification_channels,
        group=data.group,
    )
    ALERTS[alert.id] = alert

    return {"id": alert.id, "name": alert.name, "state": alert.state.value}


@app.get("/v1/alerts")
async def list_alerts(alert_state: Optional[AlertState] = Query(None, alias="state"),
                      group: Optional[str] = None):
    alerts = list(ALERTS.values())
    if alert_state:
        alerts = [a for a in alerts if a.state == alert_state]
    if group:
        alerts = [a for a in alerts if a.group == group]

    return {
        "count": len(alerts),
        "alerts": [
            {"id": a.id, "name": a.name, "condition": a.condition,
             "state": a.state.value, "group": a.group,
             "fire_count": a.fire_count, "last_fired": a.last_fired,
             "channels": [c.value for c in a.notification_channels]}
            for a in alerts
        ],
    }


@app.post("/v1/alerts/{alert_id}/silence")
async def silence_alert(alert_id: str, duration_hours: int = 1):
    if alert_id not in ALERTS:
        raise HTTPException(404, "Alert not found")

    alert = ALERTS[alert_id]
    alert.silenced_until = (_now() + timedelta(hours=duration_hours)).isoformat()

    return {"id": alert_id, "silenced_until": alert.silenced_until}


# ---- Dashboard --------------------------------------------------------------

@app.get("/v1/dashboard")
async def observability_dashboard():
    # Trace stats
    error_traces = sum(1 for t in TRACES.values() if t.has_error)
    trace_durations = [t.total_duration_ms for t in TRACES.values()]

    # Service-level stats
    service_stats = {}
    for svc in SERVICES:
        svc_spans = [s for s in SPANS.values() if s.service == svc]
        svc_errors = sum(1 for s in svc_spans if s.status == SpanStatus.ERROR)
        svc_durations = [s.duration_ms for s in svc_spans]
        svc_logs = [l for l in LOGS if l.service == svc]
        error_logs = sum(1 for l in svc_logs if l.level in (LogLevel.ERROR, LogLevel.FATAL))

        service_stats[svc] = {
            "spans": len(svc_spans),
            "error_spans": svc_errors,
            "error_rate_pct": round(svc_errors / max(len(svc_spans), 1) * 100, 2),
            "latency_p50_ms": _percentile(svc_durations, 50),
            "latency_p95_ms": _percentile(svc_durations, 95),
            "latency_p99_ms": _percentile(svc_durations, 99),
            "log_count": len(svc_logs),
            "error_log_count": error_logs,
        }

    # Alert summary
    alert_summary = Counter(a.state.value for a in ALERTS.values())

    # SLO summary
    slo_summary = Counter(s.status for s in SLOS.values())

    # Log volume by level
    log_levels = Counter(l.level.value for l in LOGS)

    return {
        "total_traces": len(TRACES),
        "error_traces": error_traces,
        "trace_error_rate_pct": round(error_traces / max(len(TRACES), 1) * 100, 2),
        "trace_duration_p50_ms": _percentile(trace_durations, 50),
        "trace_duration_p95_ms": _percentile(trace_durations, 95),
        "total_spans": len(SPANS),
        "total_metric_points": len(METRICS),
        "total_logs": len(LOGS),
        "log_levels": dict(log_levels),
        "service_stats": service_stats,
        "slo_summary": dict(slo_summary),
        "alert_summary": dict(alert_summary),
        "monitored_services": len(SERVICES),
    }


# ---- Analytics --------------------------------------------------------------

@app.get("/v1/analytics")
async def observability_analytics():
    # Top slow services
    service_latencies: dict[str, list[float]] = defaultdict(list)
    for s in SPANS.values():
        service_latencies[s.service].append(s.duration_ms)

    slowest = sorted(
        [(svc, _percentile(vals, 95)) for svc, vals in service_latencies.items()],
        key=lambda x: x[1], reverse=True,
    )[:10]

    # Error hotspots
    service_errors: Counter = Counter()
    for s in SPANS.values():
        if s.status == SpanStatus.ERROR:
            service_errors[s.service] += 1

    # SLO burn rates
    slo_burns = [
        {"name": s.name, "service": s.service, "burn_rate": s.burn_rate,
         "budget_remaining_pct": round(s.error_budget_remaining / max(s.error_budget_total, 0.0001) * 100, 1)}
        for s in sorted(SLOS.values(), key=lambda s: s.burn_rate, reverse=True)
    ]

    return {
        "slowest_services_p95": [{"service": s, "latency_p95_ms": l} for s, l in slowest],
        "error_hotspots": [{"service": s, "errors": c} for s, c in service_errors.most_common(10)],
        "slo_burn_rates": slo_burns,
        "firing_alerts": sum(1 for a in ALERTS.values() if a.state == AlertState.FIRING),
        "total_traces": len(TRACES),
        "total_log_entries": len(LOGS),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9202)
