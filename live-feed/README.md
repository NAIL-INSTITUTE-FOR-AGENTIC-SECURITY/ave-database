# AVE Live Feed — Real-Time Streaming API

Real-time vulnerability intelligence delivery via WebSocket and Server-Sent Events (SSE).

## Overview

The AVE Live Feed provides instant notifications when AVE cards are created,
updated, or deprecated — enabling security operations centres, automated
defence systems, and monitoring tools to react in real time.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    AVE Database                           │
│  (Card created / updated / deprecated / status changed)  │
└──────────────────────┬───────────────────────────────────┘
                       │  Event Bus (Redis Pub/Sub)
                       │
              ┌────────▼────────┐
              │  Feed Broker    │
              │  (FastAPI)      │
              │                 │
              │  • Auth         │
              │  • Filtering    │
              │  • Rate Limit   │
              │  • Replay       │
              └───┬─────────┬───┘
                  │         │
         ┌────────▼──┐  ┌──▼────────┐
         │ WebSocket │  │   SSE     │
         │ /ws/feed  │  │ /sse/feed │
         └────────┬──┘  └──┬────────┘
                  │        │
          ┌───────▼────────▼───────┐
          │      Consumers         │
          │  • SIEM integrations   │
          │  • SOAR playbooks      │
          │  • Monitoring dashboards│
          │  • Custom applications │
          └────────────────────────┘
```

## Endpoints

### WebSocket

```
wss://api.nailinstitute.org/ws/feed?token=<API_KEY>
```

### Server-Sent Events (SSE)

```
GET https://api.nailinstitute.org/sse/feed
Authorization: Bearer <API_KEY>
Accept: text/event-stream
```

### REST (Polling Fallback)

```
GET https://api.nailinstitute.org/api/v2/events?since=<ISO8601>
Authorization: Bearer <API_KEY>
```

## Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `ave.created` | New AVE card published | Full card JSON |
| `ave.updated` | Existing card modified | Full card JSON + diff |
| `ave.deprecated` | Card deprecated | Card ID + reason |
| `ave.status_changed` | Status transition | Card ID + old/new status |
| `ave.severity_changed` | Severity re-assessed | Card ID + old/new severity |
| `avss.recalculated` | AVSS score updated | Card ID + old/new scores |
| `feed.heartbeat` | Every 30 seconds | Timestamp + seq |

## Event Schema

```json
{
  "event_id": "evt_20250701_001",
  "event_type": "ave.created",
  "timestamp": "2025-07-01T14:30:00Z",
  "sequence": 1042,
  "data": {
    "ave_id": "AVE-2025-0052",
    "name": "...",
    "category": "prompt_injection",
    "severity": "critical",
    "avss_base": 9.2
  },
  "metadata": {
    "schema_version": "2.0.0",
    "source": "nail-ave-database",
    "region": "global"
  }
}
```

## Filtering

Subscribe to specific event types and card attributes:

### WebSocket Filter (on connect)

```json
{
  "action": "subscribe",
  "filters": {
    "event_types": ["ave.created", "ave.severity_changed"],
    "severity": ["critical", "high"],
    "categories": ["prompt_injection", "multi_agent_collusion"],
    "frameworks": ["LangChain", "AutoGen"]
  }
}
```

### SSE Filter (query params)

```
GET /sse/feed?severity=critical,high&category=prompt_injection&event_type=ave.created
```

## Replay & Recovery

### Event Replay

Reconnect and replay missed events using the `Last-Event-ID` header (SSE)
or the `replay_from` parameter (WebSocket):

```
# SSE
Last-Event-ID: 1042

# WebSocket
{"action": "replay", "from_sequence": 1042}
```

### Event Log

The last 10,000 events (or 30 days) are retained for replay.

```
GET /api/v2/events?since=2025-07-01T00:00:00Z&limit=100
```

## Authentication

| Method | Endpoint | Header |
|--------|----------|--------|
| API Key | All | `Authorization: Bearer <key>` |
| WebSocket | `/ws/feed` | `?token=<key>` query param |

API keys are managed through the [Commercial API](../commercial-api/) dashboard.

## Rate Limits

| Tier | Connections | Events/min | Replay Depth |
|------|-------------|-----------|--------------|
| Free | 1 | 60 | 100 events |
| Professional | 5 | 600 | 1,000 events |
| Enterprise | 25 | Unlimited | 10,000 events |
| Partner | 50 | Unlimited | 30 days |

## Client Libraries

### Python

```python
from nail_ave_sdk.live import AVELiveFeed

feed = AVELiveFeed(api_key="your-key")

@feed.on("ave.created")
def handle_new_card(event):
    card = event["data"]
    print(f"NEW: {card['ave_id']} — {card['name']} [{card['severity']}]")

@feed.on("ave.severity_changed")
def handle_severity_change(event):
    print(f"SEVERITY CHANGE: {event['data']['ave_id']} "
          f"{event['data']['old_severity']} → {event['data']['new_severity']}")

feed.connect(
    filters={
        "severity": ["critical", "high"],
        "categories": ["prompt_injection"],
    }
)
```

### TypeScript / Node.js

```typescript
import { AVELiveFeed } from '@nail-institute/ave-sdk';

const feed = new AVELiveFeed({ apiKey: 'your-key' });

feed.on('ave.created', (event) => {
  console.log(`NEW: ${event.data.ave_id} — ${event.data.name}`);
});

feed.connect({
  filters: {
    severity: ['critical', 'high'],
  },
});
```

### cURL (SSE)

```bash
curl -N -H "Authorization: Bearer YOUR_KEY" \
  "https://api.nailinstitute.org/sse/feed?severity=critical"
```

## Integration Examples

### Slack Alert on Critical AVE

```python
from nail_ave_sdk.live import AVELiveFeed
import requests

feed = AVELiveFeed(api_key="your-key")

@feed.on("ave.created")
def slack_alert(event):
    card = event["data"]
    if card["severity"] == "critical":
        requests.post(SLACK_WEBHOOK, json={
            "text": f"🚨 *Critical AVE Published*\n"
                    f"*{card['ave_id']}*: {card['name']}\n"
                    f"AVSS: {card.get('avss_base', 'N/A')}\n"
                    f"<https://nailinstitute.org/ave/{card['ave_id']}|View Card>"
        })

feed.connect(filters={"severity": ["critical"]})
```

### SOAR Playbook Trigger

```python
@feed.on("ave.created")
def trigger_soar(event):
    card = event["data"]
    # Check if any of our deployed frameworks are affected
    our_frameworks = {"LangChain", "AutoGen"}
    affected = set(card.get("environment", {}).get("agent_frameworks", []))
    if affected & our_frameworks:
        soar_api.create_incident(
            title=f"AVE Alert: {card['ave_id']}",
            severity=card["severity"],
            description=card["summary"],
            playbook="agentic-ai-vulnerability-response",
        )
```

## Monitoring

### Health Check

```
GET /api/v2/feed/health
```

```json
{
  "status": "healthy",
  "connections": {
    "websocket": 142,
    "sse": 89
  },
  "events_last_hour": 12,
  "last_event_sequence": 1042,
  "uptime_seconds": 864000
}
```

### Metrics (Prometheus)

```
GET /metrics
```

Exported metrics:
- `ave_feed_connections_active{type="ws|sse"}`
- `ave_feed_events_published_total{event_type="..."}`
- `ave_feed_events_replayed_total`
- `ave_feed_connection_errors_total`

## Contact

- **Docs**: This README + [API Reference](api-reference.md)
- **Status**: status.nailinstitute.org
- **Support**: api-support@nailinstitute.org
- **Slack**: `#live-feed`
