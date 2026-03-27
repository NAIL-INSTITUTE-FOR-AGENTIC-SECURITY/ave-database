# Observability Stack

> Unified observability with OpenTelemetry instrumentation, distributed tracing, metric aggregation, log correlation, and SLO dashboards for the NAIL AVE platform.

## Overview

The Observability Stack provides a single pane of glass across all 85+ NAIL microservices. It collects traces, metrics, and logs via the OpenTelemetry protocol, correlates them by trace ID, aggregates service-level objectives, and surfaces actionable alerts. Every request flowing through the platform is traceable end-to-end, every metric is queryable, and every log line is correlated to its originating trace.

## Port

| Service | Port |
|---------|------|
| Observability Stack | **9202** |

## Key Features

### Distributed Tracing
- **Trace ingestion** — accept OpenTelemetry trace spans via HTTP (OTLP/HTTP)
- **Trace context propagation** — W3C Trace Context (traceparent/tracestate) headers
- **Span model** — trace_id, span_id, parent_span_id, operation, service, duration, status, attributes
- **Trace assembly** — reconstruct full request tree from collected spans
- **Trace search** — find traces by service, operation, duration threshold, status, time range
- **Slow trace detection** — flag traces exceeding p99 latency thresholds
- **Error trace highlighting** — surface traces containing error spans

### Metric Aggregation
- **Metric ingestion** — accept counter, gauge, and histogram metrics
- **Service-level metrics** — request_count, error_count, latency_p50/p95/p99 per service
- **Custom metrics** — arbitrary named metrics with label dimensions
- **Time-series storage** — 1-minute resolution with configurable retention (30/90/365 days)
- **Metric queries** — filter by service, metric name, labels, time range
- **Aggregations** — sum, avg, min, max, percentile across time windows

### Log Correlation
- **Structured log ingestion** — accept JSON logs with trace_id, span_id, service, level, message
- **Trace-log correlation** — retrieve all logs for a given trace ID
- **Log levels** — DEBUG, INFO, WARN, ERROR, FATAL with level-based filtering
- **Full-text search** — search log messages by keyword
- **Log volume analytics** — logs/sec by service and level

### Service Level Objectives (SLOs)
- **SLO definitions** — define target availability, latency, and error rate per service
- **Error budget tracking** — remaining error budget as percentage of 30-day window
- **Burn rate alerts** — alert when error budget consumption exceeds 2× normal rate
- **SLO dashboard** — current status, budget remaining, trend for every defined SLO
- **Historical SLO compliance** — weekly/monthly compliance reports

### Alerting
- **Alert rules** — define threshold-based alert rules on any metric or SLO
- **Alert states** — firing, pending, resolved with state transition history
- **Notification channels** — webhook, email, Slack, PagerDuty (configurable)
- **Alert grouping** — deduplicate related alerts by service/category
- **Silence/inhibit** — temporarily silence alerts during maintenance windows

### Health Dashboard
- **Service health map** — real-time health status of all registered services
- **Dependency graph** — visualise inter-service call patterns from trace data
- **Anomaly detection** — flag services with unusual latency or error rate spikes
- **Capacity indicators** — request throughput vs baseline per service

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Observability stack health |
| POST | `/v1/traces` | Ingest trace spans |
| GET | `/v1/traces` | Search/list traces |
| GET | `/v1/traces/{trace_id}` | Get full trace detail |
| POST | `/v1/metrics` | Ingest metrics |
| GET | `/v1/metrics` | Query metrics |
| GET | `/v1/metrics/{service}` | Service-specific metrics |
| POST | `/v1/logs` | Ingest structured logs |
| GET | `/v1/logs` | Search logs |
| GET | `/v1/logs/trace/{trace_id}` | Logs for a specific trace |
| POST | `/v1/slos` | Define SLO |
| GET | `/v1/slos` | List SLOs with status |
| GET | `/v1/slos/{slo_id}` | SLO detail + error budget |
| POST | `/v1/alerts` | Create alert rule |
| GET | `/v1/alerts` | List alert rules + states |
| GET | `/v1/dashboard` | Unified health dashboard |
| GET | `/v1/analytics` | Observability analytics |

## Architecture

```
Services → [OTLP Exporter] → Observability Stack
                                   ├── Trace Store
                                   ├── Metric Store (time-series)
                                   ├── Log Store
                                   ├── SLO Engine
                                   └── Alert Manager → Notification Channels
```

## Production Notes

- **Trace backend** → Jaeger / Tempo / Zipkin
- **Metric backend** → Prometheus / Mimir / InfluxDB
- **Log backend** → Loki / Elasticsearch / ClickHouse
- **SLO engine** → Sloth / custom PromQL-based evaluator
- **Alert manager** → Prometheus Alertmanager / Grafana OnCall
- **Dashboards** → Grafana with pre-built NAIL dashboards
- **OTLP collector** → OpenTelemetry Collector as sidecar/daemonset
