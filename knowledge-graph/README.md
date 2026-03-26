# AVE Knowledge Graph — Neo4j Graph Database

A graph database linking AVE cards, MITRE techniques, CWEs, frameworks,
defences, research papers, and real-world incidents into a navigable
knowledge network.

## Overview

The AVE Knowledge Graph transforms the flat AVE card catalogue into a
richly interconnected graph, enabling:

- **Impact analysis**: "Which frameworks are affected by this vulnerability?"
- **Defence coverage**: "What defences cover this attack chain?"
- **Attack path discovery**: "What multi-step attack chains exist?"
- **Research mapping**: "Which papers address this category?"
- **Trend analysis**: "How has this category evolved over time?"

## Graph Schema

```
                    ┌──────────────┐
                    │   AVE Card   │
                    │ (Vulnerability│
                    │  node)       │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼───────┐ ┌─────▼──────┐ ┌─────▼──────┐
    │  Category    │ │  Severity  │ │  Status    │
    │  (label)     │ │  (level)   │ │  (state)   │
    └──────────────┘ └────────────┘ └────────────┘
           │
    ┌──────▼───────┐
    │  MITRE       │─────── maps_to ──── ┌────────────┐
    │  Technique   │                      │  MITRE     │
    └──────────────┘                      │  Tactic    │
                                          └────────────┘
    ┌──────────────┐
    │  CWE         │─────── weakens ──── ┌────────────┐
    │  Weakness    │                      │  CWE       │
    └──────────────┘                      │  Category  │
                                          └────────────┘
    ┌──────────────┐
    │  Framework   │─────── version_of ── ┌────────────┐
    │  Version     │                       │  Framework │
    └──────────────┘                       └────────────┘

    ┌──────────────┐
    │  Defence     │─────── mitigates ──── AVE Card
    │  Technique   │
    └──────────────┘

    ┌──────────────┐
    │  Research    │─────── analyses ──── AVE Card
    │  Paper       │
    └──────────────┘

    ┌──────────────┐
    │  Incident    │─────── exploited ─── AVE Card
    │  Report      │
    └──────────────┘
```

## Node Types

| Node Label | Properties | Description |
|-----------|------------|-------------|
| `AVECard` | ave_id, title, description, severity, avss_score, status, created_at, updated_at | Core vulnerability card |
| `Category` | name, description | AVE category (e.g., prompt_injection) |
| `MITRETechnique` | technique_id, name, url | MITRE ATT&CK / ATLAS technique |
| `MITRETactic` | tactic_id, name | MITRE tactic (e.g., Initial Access) |
| `CWE` | cwe_id, name, url | Common Weakness Enumeration entry |
| `Framework` | name, vendor | Agent framework (e.g., LangChain) |
| `FrameworkVersion` | version, release_date | Specific framework release |
| `Defence` | name, description, effectiveness | Mitigation technique |
| `Paper` | doi, title, authors, year, url | Research publication |
| `Incident` | incident_id, title, date, description | Real-world incident |
| `Organization` | name, type | Contributing organization |

## Relationship Types

| Relationship | From → To | Description |
|-------------|-----------|-------------|
| `BELONGS_TO` | AVECard → Category | Card's vulnerability category |
| `HAS_SEVERITY` | AVECard → Severity | Card's severity level |
| `MAPS_TO_TECHNIQUE` | AVECard → MITRETechnique | MITRE mapping |
| `MAPS_TO_CWE` | AVECard → CWE | CWE mapping |
| `AFFECTS` | AVECard → FrameworkVersion | Affected framework version |
| `MITIGATED_BY` | AVECard → Defence | Defence that addresses this vuln |
| `ANALYSED_BY` | AVECard → Paper | Research paper about this vuln |
| `EXPLOITED_IN` | AVECard → Incident | Real-world exploitation |
| `DISCOVERED_BY` | AVECard → Organization | Who discovered it |
| `VERSION_OF` | FrameworkVersion → Framework | Version–framework link |
| `TECHNIQUE_OF` | MITRETechnique → MITRETactic | MITRE technique–tactic |
| `CHILD_OF` | CWE → CWE | CWE hierarchy |
| `ENABLES` | AVECard → AVECard | One vuln enables another |
| `SUPERSEDES` | AVECard → AVECard | Card supersedes another |
| `RELATED_TO` | AVECard → AVECard | General relationship |

## API

### Graph Queries

```
GET  /v1/graph/node/{id}                    Get node with relationships
GET  /v1/graph/search?q={text}              Full-text search across nodes
GET  /v1/graph/path?from={id}&to={id}       Shortest path between nodes
GET  /v1/graph/neighbours/{id}?depth={n}    N-hop neighbours
GET  /v1/graph/subgraph?category={cat}      Category subgraph
```

### Impact Analysis

```
GET  /v1/analysis/impact/{ave_id}           Impact analysis for a card
GET  /v1/analysis/attack-chains             Multi-step attack chains
GET  /v1/analysis/defence-coverage          Defence coverage matrix
GET  /v1/analysis/framework-risk/{name}     Risk profile for a framework
```

### Statistics

```
GET  /v1/stats/overview                     Graph-wide statistics
GET  /v1/stats/categories                   Per-category breakdown
GET  /v1/stats/trends?period={period}       Temporal trends
```

### Data Management

```
POST /v1/ingest/ave                         Ingest AVE card into graph
POST /v1/ingest/batch                       Batch ingest
POST /v1/ingest/paper                       Add research paper
POST /v1/ingest/incident                    Add incident report
```

## Example Queries

### Cypher — All critical vulns with no defence

```cypher
MATCH (v:AVECard {severity: 'critical'})
WHERE NOT (v)-[:MITIGATED_BY]->(:Defence)
RETURN v.ave_id, v.title, v.category
ORDER BY v.avss_score DESC
```

### Cypher — Attack chain discovery

```cypher
MATCH path = (v1:AVECard)-[:ENABLES*1..3]->(v2:AVECard)
WHERE v1.category = 'prompt_injection'
  AND v2.severity IN ['critical', 'high']
RETURN path
LIMIT 20
```

### Cypher — Framework risk profile

```cypher
MATCH (fw:Framework {name: 'LangChain'})<-[:VERSION_OF]-(fv:FrameworkVersion)<-[:AFFECTS]-(v:AVECard)
RETURN fv.version, count(v) AS vuln_count,
       collect(DISTINCT v.severity) AS severities,
       collect(DISTINCT v.category) AS categories
ORDER BY fv.version DESC
```

### Cypher — Defence coverage gaps

```cypher
MATCH (c:Category)<-[:BELONGS_TO]-(v:AVECard)
OPTIONAL MATCH (v)-[:MITIGATED_BY]->(d:Defence)
WITH c.name AS category,
     count(v) AS total_vulns,
     count(d) AS defended_vulns
RETURN category,
       total_vulns,
       defended_vulns,
       total_vulns - defended_vulns AS undefended,
       round(toFloat(defended_vulns) / total_vulns * 100, 1) AS coverage_pct
ORDER BY undefended DESC
```

### Cypher — Research coverage

```cypher
MATCH (c:Category)
OPTIONAL MATCH (c)<-[:BELONGS_TO]-(v:AVECard)-[:ANALYSED_BY]->(p:Paper)
WITH c.name AS category,
     count(DISTINCT p) AS paper_count
RETURN category, paper_count
ORDER BY paper_count ASC
```

## Requirements

- Python 3.11+
- Neo4j 5.x (graph database)
- FastAPI (API server)
- neo4j Python driver

## Setup

```bash
# Start Neo4j (Docker)
docker run -d \
  --name neo4j-ave \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/nail-ave-graph \
  neo4j:5

# Initialize schema
python graph_server.py --init-schema

# Ingest existing AVE cards
python graph_server.py --ingest-all

# Start API server
uvicorn graph_server:app --host 0.0.0.0 --port 8500
```

## Contact

- **Email**: knowledge-graph@nailinstitute.org
- **Neo4j Browser**: `bolt://graph.nailinstitute.org:7687`
- **Slack**: `#knowledge-graph`
