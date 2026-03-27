# Event-Driven Integration Bus

> Real-time event backbone enabling inter-service communication, event sourcing, and CQRS patterns across the NAIL AVE platform.

## Overview

The Event-Driven Integration Bus provides a pub/sub event fabric connecting all NAIL microservices. Services publish domain events (threat detected, incident created, proposal ratified, etc.) and any interested service subscribes. The bus supports event sourcing with full replay, CQRS read-model projections, dead-letter queues, and schema evolution — enabling loose coupling while maintaining strong consistency guarantees.

## Port

| Service | Port |
|---------|------|
| Event-Driven Integration Bus | **9201** |

## Key Features

### Topic Management
- **Topic registry** — create, list, describe, and archive topics with schema definitions
- **8 core topic categories** — threat_events, incident_events, defence_events, compliance_events, trust_events, standards_events, telemetry_events, system_events
- **Schema enforcement** — JSON Schema validation on publish; reject malformed events
- **Schema versioning** — backward-compatible schema evolution with version tracking
- **Topic metadata** — owner, description, retention policy, partition count

### Publishing
- **Synchronous publish** — POST event to topic, receive acknowledgement with event ID + offset
- **Batch publish** — submit multiple events in a single request for throughput
- **Idempotent publish** — client-supplied idempotency key prevents duplicate events
- **Event envelope** — standardised wrapper: event_id, topic, timestamp, source, schema_version, payload
- **Ordering guarantees** — per-partition ordering within a topic

### Subscription
- **Named consumer groups** — multiple consumers share load within a group
- **Push vs pull** — webhook-based push delivery or poll-based pull consumption
- **Offset management** — consumer tracks own offset; supports seek/replay from any position
- **At-least-once delivery** — acknowledged events are not redelivered
- **Dead-letter queue (DLQ)** — events failing processing after configurable retries (default: 3) routed to per-topic DLQ

### Event Sourcing
- **Append-only event store** — immutable log of every event published
- **Stream replay** — replay full topic or time-range for rebuilding read models
- **Snapshot support** — periodic snapshots to accelerate replay
- **Aggregate reconstruction** — rebuild entity state from event sequence
- **Compaction** — optional log compaction retaining only latest event per key

### CQRS Projections
- **Projection registry** — define read-model projections from event streams
- **Real-time materialisation** — projections update on every new event
- **Projection status** — lag, last processed offset, health
- **Rebuild trigger** — force full rebuild of a projection from source events

### Routing & Filtering
- **Content-based routing** — route events to consumers based on payload fields
- **Category filters** — subscribe to events matching specific AVE categories
- **Severity filters** — subscribe to events above a minimum severity threshold
- **Cross-topic joins** — correlate events across topics by shared entity ID

### Analytics & Monitoring
- **Throughput metrics** — events/sec publish and consume rates per topic
- **Consumer lag** — real-time lag per consumer group
- **DLQ depth** — unprocessed dead-letter events per topic
- **Event flow visualisation** — publisher → topic → consumer graph

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Bus health check |
| POST | `/v1/topics` | Create topic |
| GET | `/v1/topics` | List topics |
| GET | `/v1/topics/{topic_id}` | Topic details + schema |
| POST | `/v1/publish/{topic_id}` | Publish event(s) |
| POST | `/v1/subscribe` | Create subscription |
| GET | `/v1/subscriptions` | List subscriptions |
| POST | `/v1/consume/{subscription_id}` | Pull events (poll) |
| POST | `/v1/ack/{subscription_id}` | Acknowledge events |
| GET | `/v1/dlq/{topic_id}` | View dead-letter queue |
| POST | `/v1/dlq/{topic_id}/replay` | Replay DLQ events |
| POST | `/v1/replay/{topic_id}` | Replay topic from offset |
| POST | `/v1/projections` | Create CQRS projection |
| GET | `/v1/projections` | List projections |
| GET | `/v1/projections/{projection_id}` | Projection status |
| GET | `/v1/analytics` | Bus analytics dashboard |

## Architecture

```
Publisher → [Schema Validate] → [Topic Partition] → Event Store
                                       ↓
                              Subscription Router
                              ↙        ↓        ↘
                        Consumer A  Consumer B  Consumer C
                                       ↓ (fail)
                                   Dead-Letter Queue
```

## Production Notes

- **Event store** → Apache Kafka / Amazon Kinesis / NATS JetStream
- **Schema registry** → Confluent Schema Registry / custom JSON Schema store
- **Consumer state** → Redis / PostgreSQL for offset tracking
- **DLQ** → Separate Kafka topic or SQS queue
- **Projections** → Kafka Streams / Flink / custom materialiser
- **Observability** → Kafka metrics via JMX → Prometheus → Grafana
