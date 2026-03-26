# STIX/TAXII Threat Intelligence Sharing

Native TAXII 2.1 server for bidirectional exchange of agentic AI threat
intelligence with ISACs, CERTs, and the wider security community.

## Overview

The NAIL TAXII 2.1 server translates AVE vulnerability cards into STIX 2.1
Structured Threat Information eXpression bundles and serves them over the
OASIS TAXII 2.1 protocol.  This enables interoperability with existing
threat intelligence platforms (TIPs), SIEMs, and SOARs.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    NAIL TAXII 2.1 Server                          │
│                                                                    │
│  ┌──────────────┐   ┌───────────────┐   ┌──────────────────┐    │
│  │ AVE → STIX   │   │ TAXII 2.1     │   │ Auth & Rate      │    │
│  │ Translator   │   │ API           │   │ Limiter          │    │
│  │              │   │               │   │                  │    │
│  │ • AVE card   │   │ • Discovery   │   │ • API key auth   │    │
│  │   → STIX     │   │ • Collection  │   │ • OAuth2 (opt)   │    │
│  │   objects     │   │ • Objects     │   │ • Rate limiting  │    │
│  │ • Category   │   │ • Manifest    │   │ • Audit logging  │    │
│  │   → TTP      │   │ • Filtering   │   │                  │    │
│  │ • Defence    │   │ • Paging      │   │                  │    │
│  │   → CoA      │   │               │   │                  │    │
│  └──────────────┘   └───────────────┘   └──────────────────┘    │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    STIX Object Store                         │ │
│  │  • Vulnerability   • Attack Pattern   • Course of Action    │ │
│  │  • Indicator       • Relationship     • Identity             │ │
│  │  • Malware         • Tool             • Report               │ │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
         │                    │                     │
    ┌────▼────┐       ┌──────▼──────┐       ┌──────▼──────┐
    │  SIEMs  │       │  ISACs /    │       │  Custom     │
    │ Splunk  │       │  CERTs      │       │  TIP        │
    │ Elastic │       │  US-CERT    │       │ Integrations│
    └─────────┘       │  AI-ISAC    │       └─────────────┘
                      └─────────────┘
```

## TAXII 2.1 Endpoints

### Discovery

```
GET  /taxii2/               Server discovery document
GET  /taxii2/api/           API root information
```

### Collections

```
GET  /taxii2/api/collections/                   List all collections
GET  /taxii2/api/collections/{id}/              Collection details
GET  /taxii2/api/collections/{id}/objects/      Get STIX objects
POST /taxii2/api/collections/{id}/objects/      Add STIX objects (write)
GET  /taxii2/api/collections/{id}/manifest/     Object manifest
DELETE /taxii2/api/collections/{id}/objects/{id}/ Delete object
```

### Filtering

Objects support TAXII 2.1 filtering:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `added_after` | Objects added after timestamp | `2025-01-01T00:00:00Z` |
| `match[type]` | Filter by STIX type | `vulnerability,attack-pattern` |
| `match[id]` | Filter by STIX ID | `vulnerability--uuid` |
| `match[spec_version]` | STIX spec version | `2.1` |
| `limit` | Max results per page | `100` |
| `next` | Pagination cursor | `cursor-token` |

## Collections

### 1. `ave-vulnerabilities`

All published AVE vulnerability cards as STIX Vulnerability objects.

### 2. `ave-attack-patterns`

Attack techniques from AVE cards as STIX Attack Pattern objects,
cross-referenced with MITRE ATT&CK / ATLAS.

### 3. `ave-defences`

Recommended defences as STIX Course of Action objects linked to
the vulnerabilities they mitigate.

### 4. `ave-indicators`

Detection indicators derived from AVE evidence (IoCs, behavioural
signatures) as STIX Indicator objects.

### 5. `ave-reports`

Aggregated threat reports (monthly digests, category deep-dives)
as STIX Report objects bundling related objects.

## AVE → STIX Mapping

| AVE Field | STIX Object Type | STIX Property |
|-----------|------------------|---------------|
| `ave_id` | Vulnerability | `name` |
| `title` | Vulnerability | `description` |
| `description` | Vulnerability | `description` |
| `category` | Attack Pattern | `name` |
| `severity` | Vulnerability | `x_avss_severity` |
| `avss_score` | Vulnerability | `x_avss_score` |
| `mitre_mapping` | Attack Pattern | `external_references` |
| `cwe_mapping` | Vulnerability | `external_references` |
| `defences` | Course of Action | Linked via Relationship |
| `status` | Vulnerability | `x_ave_status` |
| `affected_systems` | Vulnerability | `x_affected_systems` |
| `created_at` | Vulnerability | `created` |
| `updated_at` | Vulnerability | `modified` |

## Authentication

### API Key

```
Authorization: Bearer <api-key>
```

### OAuth 2.0 (Optional)

```
Authorization: Bearer <oauth-token>
```

API keys are issued per organization with configurable collection
access (read/write) and rate limits.

## Rate Limits

| Tier | Requests/min | Objects/request |
|------|-------------|-----------------|
| **Free** | 60 | 100 |
| **Partner** | 300 | 1,000 |
| **ISAC** | 1,000 | 10,000 |

## Requirements

- Python 3.11+
- FastAPI (TAXII server)
- PostgreSQL (STIX object store)
- Redis (rate limiting, caching)

## Usage

```bash
# Start TAXII server
uvicorn taxii_server:app --host 0.0.0.0 --port 8400

# Test discovery
curl -H "Authorization: Bearer <key>" https://taxii.nailinstitute.org/taxii2/

# List collections
curl -H "Accept: application/taxii+json;version=2.1" \
     -H "Authorization: Bearer <key>" \
     https://taxii.nailinstitute.org/taxii2/api/collections/

# Get vulnerabilities
curl -H "Accept: application/stix+json;version=2.1" \
     -H "Authorization: Bearer <key>" \
     "https://taxii.nailinstitute.org/taxii2/api/collections/ave-vulnerabilities/objects/?match[type]=vulnerability"
```

## Contact

- **Email**: threatintel@nailinstitute.org
- **TAXII Server**: `taxii.nailinstitute.org`
- **Slack**: `#threat-intelligence`
