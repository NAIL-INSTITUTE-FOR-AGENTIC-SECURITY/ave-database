"""
Event-Driven Integration Bus — Core event backbone server.

Pub/sub event fabric connecting all NAIL microservices.  Services
publish domain events and subscribers consume them with at-least-once
delivery.  Supports topic management, schema validation, consumer
groups, dead-letter queues, event sourcing with replay, and CQRS
read-model projections.
"""

from __future__ import annotations

import hashlib
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
    title="NAIL Event-Driven Integration Bus",
    description=(
        "Pub/sub event fabric — topics, schema validation, consumer "
        "groups, DLQ, event sourcing, replay, and CQRS projections."
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

TOPIC_CATEGORIES = [
    "threat_events", "incident_events", "defence_events",
    "compliance_events", "trust_events", "standards_events",
    "telemetry_events", "system_events",
]

AVE_CATEGORIES = [
    "prompt_injection", "tool_misuse", "memory_poisoning", "goal_hijacking",
    "identity_spoofing", "privilege_escalation", "data_exfiltration",
    "resource_exhaustion", "multi_agent_manipulation", "context_overflow",
    "guardrail_bypass", "output_manipulation", "supply_chain_compromise",
    "model_extraction", "reward_hacking", "capability_elicitation",
    "alignment_subversion", "delegation_abuse",
]


class TopicStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class SubscriptionMode(str, Enum):
    PULL = "pull"
    PUSH = "push"


class ProjectionStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    REBUILDING = "rebuilding"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:12].upper()}")
    topic_id: str = ""
    source: str = ""
    schema_version: str = "1.0"
    category: str = ""
    severity: float = Field(0.5, ge=0.0, le=1.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = ""
    offset: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventPublish(BaseModel):
    source: str = ""
    schema_version: str = "1.0"
    category: str = ""
    severity: float = Field(0.5, ge=0.0, le=1.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = ""


class Topic(BaseModel):
    id: str = Field(default_factory=lambda: f"TOPIC-{uuid.uuid4().hex[:8].upper()}")
    name: str
    category: str = ""
    description: str = ""
    schema_definition: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"
    status: TopicStatus = TopicStatus.ACTIVE
    partition_count: int = 1
    retention_hours: int = 168  # 7 days
    event_count: int = 0
    next_offset: int = 0
    owner: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TopicCreate(BaseModel):
    name: str
    category: str = ""
    description: str = ""
    schema_definition: dict[str, Any] = Field(default_factory=dict)
    partition_count: int = 1
    retention_hours: int = 168
    owner: str = ""


class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: f"SUB-{uuid.uuid4().hex[:8].upper()}")
    topic_id: str
    consumer_group: str = ""
    mode: SubscriptionMode = SubscriptionMode.PULL
    webhook_url: str = ""  # For push mode
    filter_categories: list[str] = Field(default_factory=list)
    filter_min_severity: float = 0.0
    current_offset: int = 0
    acked_offset: int = 0
    max_retries: int = 3
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SubscriptionCreate(BaseModel):
    topic_id: str
    consumer_group: str = ""
    mode: SubscriptionMode = SubscriptionMode.PULL
    webhook_url: str = ""
    filter_categories: list[str] = Field(default_factory=list)
    filter_min_severity: float = 0.0
    max_retries: int = 3


class DeadLetterEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    topic_id: str
    subscription_id: str
    retry_count: int = 0
    error_message: str = ""
    dead_lettered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Projection(BaseModel):
    id: str = Field(default_factory=lambda: f"PROJ-{uuid.uuid4().hex[:8].upper()}")
    name: str
    source_topic_id: str
    description: str = ""
    status: ProjectionStatus = ProjectionStatus.RUNNING
    last_processed_offset: int = 0
    lag: int = 0
    projection_logic: str = ""  # Description of projection transform
    materialised_data: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProjectionCreate(BaseModel):
    name: str
    source_topic_id: str
    description: str = ""
    projection_logic: str = ""


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → Apache Kafka + Schema Registry + PostgreSQL)
# ---------------------------------------------------------------------------

TOPICS: dict[str, Topic] = {}
EVENT_STORE: dict[str, list[EventEnvelope]] = {}  # topic_id → events
SUBSCRIPTIONS: dict[str, Subscription] = {}
DLQ: dict[str, list[DeadLetterEntry]] = {}  # topic_id → dead letters
PROJECTIONS: dict[str, Projection] = {}
IDEMPOTENCY_CACHE: set[str] = set()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731
_rng = random.Random(42)


def _publish_event(topic_id: str, event: EventPublish) -> EventEnvelope:
    """Publish a single event to a topic."""
    if topic_id not in TOPICS:
        raise ValueError(f"Topic '{topic_id}' not found")

    topic = TOPICS[topic_id]
    if topic.status != TopicStatus.ACTIVE:
        raise ValueError(f"Topic '{topic_id}' is archived")

    # Idempotency check
    if event.idempotency_key:
        idem_key = f"{topic_id}:{event.idempotency_key}"
        if idem_key in IDEMPOTENCY_CACHE:
            # Return existing event
            for e in reversed(EVENT_STORE.get(topic_id, [])):
                if e.idempotency_key == event.idempotency_key:
                    return e
        IDEMPOTENCY_CACHE.add(idem_key)

    # Create envelope
    envelope = EventEnvelope(
        topic_id=topic_id,
        source=event.source,
        schema_version=event.schema_version,
        category=event.category,
        severity=event.severity,
        payload=event.payload,
        idempotency_key=event.idempotency_key,
        offset=topic.next_offset,
    )

    # Append to store
    if topic_id not in EVENT_STORE:
        EVENT_STORE[topic_id] = []
    EVENT_STORE[topic_id].append(envelope)

    topic.next_offset += 1
    topic.event_count += 1

    # Update projections
    for proj in PROJECTIONS.values():
        if proj.source_topic_id == topic_id and proj.status == ProjectionStatus.RUNNING:
            proj.lag = topic.next_offset - proj.last_processed_offset - 1
            # Simulate materialisation
            cat = envelope.category or "uncategorised"
            if cat not in proj.materialised_data:
                proj.materialised_data[cat] = 0
            proj.materialised_data[cat] += 1
            proj.last_processed_offset = envelope.offset
            proj.lag = max(0, topic.next_offset - proj.last_processed_offset - 1)

    return envelope


def _consume_events(subscription: Subscription, max_events: int = 10) -> list[EventEnvelope]:
    """Pull events from a topic for a subscription."""
    events = EVENT_STORE.get(subscription.topic_id, [])
    start = subscription.current_offset
    batch = events[start:start + max_events]

    # Apply filters
    if subscription.filter_categories:
        batch = [e for e in batch if e.category in subscription.filter_categories]
    if subscription.filter_min_severity > 0:
        batch = [e for e in batch if e.severity >= subscription.filter_min_severity]

    return batch


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    rng = random.Random(42)

    # Create core topics
    topic_defs = [
        ("threat.detected", "threat_events", "Emitted when a new threat is detected by any subsystem"),
        ("incident.created", "incident_events", "Emitted when a new incident is created"),
        ("incident.resolved", "incident_events", "Emitted when an incident is resolved"),
        ("defence.activated", "defence_events", "Emitted when a defence mechanism is activated"),
        ("defence.deactivated", "defence_events", "Emitted when a defence mechanism is deactivated"),
        ("compliance.violation", "compliance_events", "Emitted when a compliance violation is detected"),
        ("trust.updated", "trust_events", "Emitted when trust score is updated for an agent"),
        ("standards.proposal", "standards_events", "Emitted when a new standards proposal is created"),
        ("telemetry.metric", "telemetry_events", "Emitted with subsystem performance telemetry"),
        ("system.health", "system_events", "Periodic system health heartbeat"),
    ]

    for name, category, desc in topic_defs:
        topic = Topic(
            name=name, category=category, description=desc,
            schema_definition={"type": "object", "required": ["source", "payload"]},
            owner="nail-platform",
        )
        TOPICS[topic.id] = topic
        EVENT_STORE[topic.id] = []
        DLQ[topic.id] = []

    topic_ids = list(TOPICS.keys())

    # Publish seed events
    sources = ["threat-intel", "incident-commander", "defence-mesh",
               "autonomous-redteam", "ethical-reasoning", "civilisational-risk"]

    for i in range(200):
        tid = rng.choice(topic_ids)
        topic = TOPICS[tid]
        evt = EventPublish(
            source=rng.choice(sources),
            category=rng.choice(AVE_CATEGORIES) if "threat" in topic.name or "incident" in topic.name else "",
            severity=round(rng.uniform(0.1, 0.95), 4),
            payload={"detail": f"Seed event #{i + 1}", "value": round(rng.uniform(0, 100), 2)},
        )
        _publish_event(tid, evt)

    # Create subscriptions
    sub_defs = [
        (topic_ids[0], "incident-response", ["prompt_injection", "data_exfiltration"], 0.5),
        (topic_ids[0], "analytics-pipeline", [], 0.0),
        (topic_ids[1], "notification-service", [], 0.0),
        (topic_ids[3], "compliance-monitor", [], 0.7),
        (topic_ids[8], "self-improvement", [], 0.0),
    ]

    for tid, group, cats, min_sev in sub_defs:
        sub = Subscription(
            topic_id=tid,
            consumer_group=group,
            filter_categories=cats,
            filter_min_severity=min_sev,
            current_offset=0,
        )
        SUBSCRIPTIONS[sub.id] = sub

    # Create a projection
    proj = Projection(
        name="threat_category_counts",
        source_topic_id=topic_ids[0],
        description="Materialised view counting threat events by AVE category",
        projection_logic="GROUP BY category → COUNT(*)",
        last_processed_offset=TOPICS[topic_ids[0]].next_offset - 1,
    )
    # Materialise from existing events
    for evt in EVENT_STORE.get(topic_ids[0], []):
        cat = evt.category or "uncategorised"
        if cat not in proj.materialised_data:
            proj.materialised_data[cat] = 0
        proj.materialised_data[cat] += 1
    PROJECTIONS[proj.id] = proj

    # Seed some DLQ entries
    for i in range(5):
        tid = rng.choice(topic_ids)
        events = EVENT_STORE.get(tid, [])
        if events:
            evt = rng.choice(events)
            sub_id = rng.choice(list(SUBSCRIPTIONS.keys())) if SUBSCRIPTIONS else "unknown"
            dle = DeadLetterEntry(
                event_id=evt.event_id,
                topic_id=tid,
                subscription_id=sub_id,
                retry_count=3,
                error_message=f"Processing failed after 3 retries: simulated error #{i + 1}",
            )
            DLQ[tid].append(dle)


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    total_events = sum(len(events) for events in EVENT_STORE.values())
    total_dlq = sum(len(entries) for entries in DLQ.values())

    return {
        "status": "healthy",
        "service": "event-driven-integration-bus",
        "version": "1.0.0",
        "topics": len(TOPICS),
        "total_events": total_events,
        "subscriptions": len(SUBSCRIPTIONS),
        "projections": len(PROJECTIONS),
        "dlq_depth": total_dlq,
    }


# ---- Topics -----------------------------------------------------------------

@app.post("/v1/topics", status_code=status.HTTP_201_CREATED)
async def create_topic(data: TopicCreate):
    if data.category and data.category not in TOPIC_CATEGORIES:
        raise HTTPException(400, f"Invalid topic category: {data.category}")

    # Check duplicate name
    if any(t.name == data.name for t in TOPICS.values()):
        raise HTTPException(409, f"Topic '{data.name}' already exists")

    topic = Topic(
        name=data.name,
        category=data.category,
        description=data.description,
        schema_definition=data.schema_definition,
        partition_count=data.partition_count,
        retention_hours=data.retention_hours,
        owner=data.owner,
    )
    TOPICS[topic.id] = topic
    EVENT_STORE[topic.id] = []
    DLQ[topic.id] = []

    return {"id": topic.id, "name": topic.name, "category": topic.category}


@app.get("/v1/topics")
async def list_topics(category: Optional[str] = None,
                      topic_status: Optional[TopicStatus] = Query(None, alias="status")):
    topics = list(TOPICS.values())
    if category:
        topics = [t for t in topics if t.category == category]
    if topic_status:
        topics = [t for t in topics if t.status == topic_status]

    return {
        "count": len(topics),
        "topics": [
            {"id": t.id, "name": t.name, "category": t.category,
             "status": t.status.value, "event_count": t.event_count,
             "next_offset": t.next_offset, "partitions": t.partition_count}
            for t in topics
        ],
    }


@app.get("/v1/topics/{topic_id}")
async def get_topic(topic_id: str):
    if topic_id not in TOPICS:
        raise HTTPException(404, "Topic not found")
    topic = TOPICS[topic_id]
    return {
        **topic.dict(),
        "dlq_depth": len(DLQ.get(topic_id, [])),
    }


# ---- Publishing -------------------------------------------------------------

@app.post("/v1/publish/{topic_id}", status_code=status.HTTP_201_CREATED)
async def publish_event(topic_id: str, data: EventPublish):
    if topic_id not in TOPICS:
        raise HTTPException(404, "Topic not found")

    try:
        envelope = _publish_event(topic_id, data)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "event_id": envelope.event_id,
        "topic_id": topic_id,
        "offset": envelope.offset,
        "timestamp": envelope.timestamp,
    }


@app.post("/v1/publish/{topic_id}/batch", status_code=status.HTTP_201_CREATED)
async def publish_batch(topic_id: str, events: list[EventPublish]):
    if topic_id not in TOPICS:
        raise HTTPException(404, "Topic not found")

    results = []
    for evt in events:
        try:
            envelope = _publish_event(topic_id, evt)
            results.append({"event_id": envelope.event_id, "offset": envelope.offset, "status": "published"})
        except ValueError as e:
            results.append({"event_id": None, "offset": None, "status": "failed", "error": str(e)})

    return {"published": sum(1 for r in results if r["status"] == "published"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "results": results}


# ---- Subscriptions ----------------------------------------------------------

@app.post("/v1/subscribe", status_code=status.HTTP_201_CREATED)
async def create_subscription(data: SubscriptionCreate):
    if data.topic_id not in TOPICS:
        raise HTTPException(400, f"Topic '{data.topic_id}' not found")

    sub = Subscription(
        topic_id=data.topic_id,
        consumer_group=data.consumer_group,
        mode=data.mode,
        webhook_url=data.webhook_url,
        filter_categories=data.filter_categories,
        filter_min_severity=data.filter_min_severity,
        max_retries=data.max_retries,
    )
    SUBSCRIPTIONS[sub.id] = sub

    return {"id": sub.id, "topic_id": sub.topic_id, "group": sub.consumer_group, "mode": sub.mode.value}


@app.get("/v1/subscriptions")
async def list_subscriptions(topic_id: Optional[str] = None):
    subs = list(SUBSCRIPTIONS.values())
    if topic_id:
        subs = [s for s in subs if s.topic_id == topic_id]

    return {
        "count": len(subs),
        "subscriptions": [
            {"id": s.id, "topic_id": s.topic_id, "group": s.consumer_group,
             "mode": s.mode.value, "current_offset": s.current_offset,
             "acked_offset": s.acked_offset, "active": s.active,
             "lag": TOPICS[s.topic_id].next_offset - s.current_offset if s.topic_id in TOPICS else 0}
            for s in subs
        ],
    }


@app.post("/v1/consume/{subscription_id}")
async def consume_events(subscription_id: str, max_events: int = Query(10, ge=1, le=100)):
    if subscription_id not in SUBSCRIPTIONS:
        raise HTTPException(404, "Subscription not found")

    sub = SUBSCRIPTIONS[subscription_id]
    if not sub.active:
        raise HTTPException(409, "Subscription is inactive")

    events = _consume_events(sub, max_events)

    # Advance offset
    if events:
        sub.current_offset = events[-1].offset + 1

    return {
        "subscription_id": subscription_id,
        "events": [
            {"event_id": e.event_id, "offset": e.offset, "source": e.source,
             "category": e.category, "severity": e.severity,
             "payload": e.payload, "timestamp": e.timestamp}
            for e in events
        ],
        "count": len(events),
    }


@app.post("/v1/ack/{subscription_id}")
async def acknowledge_events(subscription_id: str, offset: int = 0):
    if subscription_id not in SUBSCRIPTIONS:
        raise HTTPException(404, "Subscription not found")

    sub = SUBSCRIPTIONS[subscription_id]
    sub.acked_offset = max(sub.acked_offset, offset)

    return {"subscription_id": subscription_id, "acked_offset": sub.acked_offset}


# ---- Dead-Letter Queue ------------------------------------------------------

@app.get("/v1/dlq/{topic_id}")
async def view_dlq(topic_id: str, limit: int = Query(50, ge=1, le=500)):
    if topic_id not in TOPICS:
        raise HTTPException(404, "Topic not found")

    entries = DLQ.get(topic_id, [])[:limit]

    return {
        "topic_id": topic_id,
        "count": len(entries),
        "entries": [
            {"id": e.id, "event_id": e.event_id, "subscription_id": e.subscription_id,
             "retry_count": e.retry_count, "error": e.error_message,
             "dead_lettered_at": e.dead_lettered_at}
            for e in entries
        ],
    }


@app.post("/v1/dlq/{topic_id}/replay")
async def replay_dlq(topic_id: str):
    if topic_id not in TOPICS:
        raise HTTPException(404, "Topic not found")

    entries = DLQ.get(topic_id, [])
    replayed = 0

    for entry in entries:
        # Find original event
        events = EVENT_STORE.get(topic_id, [])
        original = next((e for e in events if e.event_id == entry.event_id), None)
        if original:
            # Re-publish to topic
            _publish_event(topic_id, EventPublish(
                source=original.source,
                category=original.category,
                severity=original.severity,
                payload={**original.payload, "_replayed_from_dlq": True},
            ))
            replayed += 1

    DLQ[topic_id] = []

    return {"topic_id": topic_id, "replayed": replayed}


# ---- Replay -----------------------------------------------------------------

@app.post("/v1/replay/{topic_id}")
async def replay_topic(topic_id: str, from_offset: int = 0, to_offset: Optional[int] = None):
    if topic_id not in TOPICS:
        raise HTTPException(404, "Topic not found")

    events = EVENT_STORE.get(topic_id, [])
    if to_offset is not None:
        replayed = events[from_offset:to_offset + 1]
    else:
        replayed = events[from_offset:]

    return {
        "topic_id": topic_id,
        "from_offset": from_offset,
        "to_offset": to_offset or (len(events) - 1),
        "events": [
            {"event_id": e.event_id, "offset": e.offset, "source": e.source,
             "category": e.category, "payload": e.payload, "timestamp": e.timestamp}
            for e in replayed
        ],
        "count": len(replayed),
    }


# ---- Projections ------------------------------------------------------------

@app.post("/v1/projections", status_code=status.HTTP_201_CREATED)
async def create_projection(data: ProjectionCreate):
    if data.source_topic_id not in TOPICS:
        raise HTTPException(400, f"Topic '{data.source_topic_id}' not found")

    proj = Projection(
        name=data.name,
        source_topic_id=data.source_topic_id,
        description=data.description,
        projection_logic=data.projection_logic,
    )

    # Backfill materialised data
    events = EVENT_STORE.get(data.source_topic_id, [])
    for evt in events:
        cat = evt.category or "uncategorised"
        if cat not in proj.materialised_data:
            proj.materialised_data[cat] = 0
        proj.materialised_data[cat] += 1
        proj.last_processed_offset = evt.offset

    proj.lag = TOPICS[data.source_topic_id].next_offset - proj.last_processed_offset - 1 if events else 0

    PROJECTIONS[proj.id] = proj

    return {"id": proj.id, "name": proj.name, "source_topic": data.source_topic_id}


@app.get("/v1/projections")
async def list_projections():
    return {
        "count": len(PROJECTIONS),
        "projections": [
            {"id": p.id, "name": p.name, "source_topic": p.source_topic_id,
             "status": p.status.value, "lag": p.lag,
             "last_offset": p.last_processed_offset,
             "materialised_keys": len(p.materialised_data)}
            for p in PROJECTIONS.values()
        ],
    }


@app.get("/v1/projections/{projection_id}")
async def get_projection(projection_id: str):
    if projection_id not in PROJECTIONS:
        raise HTTPException(404, "Projection not found")
    proj = PROJECTIONS[projection_id]
    return {
        "id": proj.id,
        "name": proj.name,
        "source_topic_id": proj.source_topic_id,
        "status": proj.status.value,
        "lag": proj.lag,
        "last_processed_offset": proj.last_processed_offset,
        "projection_logic": proj.projection_logic,
        "materialised_data": proj.materialised_data,
    }


# ---- Analytics --------------------------------------------------------------

@app.get("/v1/analytics")
async def bus_analytics():
    total_events = sum(len(events) for events in EVENT_STORE.values())
    total_dlq = sum(len(entries) for entries in DLQ.values())

    events_by_topic = {
        TOPICS[tid].name: len(events)
        for tid, events in EVENT_STORE.items() if tid in TOPICS
    }

    # Consumer lag
    consumer_lag = {}
    for sub in SUBSCRIPTIONS.values():
        topic = TOPICS.get(sub.topic_id)
        if topic:
            lag = topic.next_offset - sub.current_offset
            consumer_lag[sub.id] = {"group": sub.consumer_group, "lag": lag, "topic": topic.name}

    # Events by category across all topics
    cat_counts: Counter = Counter()
    for events in EVENT_STORE.values():
        for e in events:
            if e.category:
                cat_counts[e.category] += 1

    # Events by source
    source_counts: Counter = Counter()
    for events in EVENT_STORE.values():
        for e in events:
            if e.source:
                source_counts[e.source] += 1

    return {
        "total_topics": len(TOPICS),
        "active_topics": sum(1 for t in TOPICS.values() if t.status == TopicStatus.ACTIVE),
        "total_events": total_events,
        "events_by_topic": events_by_topic,
        "events_by_category": dict(cat_counts.most_common(20)),
        "events_by_source": dict(source_counts.most_common(10)),
        "total_subscriptions": len(SUBSCRIPTIONS),
        "active_subscriptions": sum(1 for s in SUBSCRIPTIONS.values() if s.active),
        "consumer_lag": consumer_lag,
        "total_dlq_entries": total_dlq,
        "dlq_by_topic": {TOPICS[tid].name: len(entries)
                         for tid, entries in DLQ.items() if tid in TOPICS and entries},
        "total_projections": len(PROJECTIONS),
        "projections_running": sum(1 for p in PROJECTIONS.values() if p.status == ProjectionStatus.RUNNING),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9201)
