"""
AVE Knowledge Graph — Neo4j-backed graph API.

Provides graph queries, impact analysis, attack chain discovery, and
defence coverage analysis over the interconnected AVE knowledge base.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NAIL AVE Knowledge Graph",
    description="Graph database API for interconnected AVE threat intelligence.",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("graph.server")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "nail-ave-graph")

# ---------------------------------------------------------------------------
# Neo4j driver (lazy init)
# ---------------------------------------------------------------------------

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        try:
            from neo4j import GraphDatabase

            _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except ImportError:
            logger.warning("neo4j driver not installed — running in mock mode")
            return None
        except Exception as exc:
            logger.warning("Cannot connect to Neo4j: %s — running in mock mode", exc)
            return None
    return _driver


def run_query(query: str, params: dict | None = None) -> list[dict[str, Any]]:
    """Execute a Cypher query and return results as list of dicts."""
    driver = get_driver()
    if driver is None:
        return []
    with driver.session() as session:
        result = session.run(query, params or {})
        return [dict(record) for record in result]


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

SCHEMA_CYPHER = """
// Constraints
CREATE CONSTRAINT ave_card_id IF NOT EXISTS
  FOR (v:AVECard) REQUIRE v.ave_id IS UNIQUE;

CREATE CONSTRAINT category_name IF NOT EXISTS
  FOR (c:Category) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT mitre_technique_id IF NOT EXISTS
  FOR (m:MITRETechnique) REQUIRE m.technique_id IS UNIQUE;

CREATE CONSTRAINT cwe_id IF NOT EXISTS
  FOR (w:CWE) REQUIRE w.cwe_id IS UNIQUE;

CREATE CONSTRAINT framework_name IF NOT EXISTS
  FOR (f:Framework) REQUIRE f.name IS UNIQUE;

CREATE CONSTRAINT paper_doi IF NOT EXISTS
  FOR (p:Paper) REQUIRE p.doi IS UNIQUE;

CREATE CONSTRAINT incident_id IF NOT EXISTS
  FOR (i:Incident) REQUIRE i.incident_id IS UNIQUE;

// Indexes
CREATE INDEX ave_card_category IF NOT EXISTS
  FOR (v:AVECard) ON (v.category);

CREATE INDEX ave_card_severity IF NOT EXISTS
  FOR (v:AVECard) ON (v.severity);

CREATE INDEX ave_card_status IF NOT EXISTS
  FOR (v:AVECard) ON (v.status);

CREATE FULLTEXT INDEX ave_search IF NOT EXISTS
  FOR (v:AVECard) ON EACH [v.title, v.description, v.ave_id];
"""


def init_schema() -> None:
    """Create constraints and indexes."""
    driver = get_driver()
    if driver is None:
        logger.warning("Cannot initialise schema — no Neo4j connection")
        return
    for statement in SCHEMA_CYPHER.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            try:
                run_query(stmt + ";")
            except Exception as exc:
                logger.warning("Schema statement skipped: %s", exc)
    logger.info("Graph schema initialised")


# ---------------------------------------------------------------------------
# Ingest models
# ---------------------------------------------------------------------------


class IngestAVECard(BaseModel):
    ave_id: str
    title: str
    description: str = ""
    category: str = ""
    severity: str = "medium"
    avss_score: float = 0.0
    status: str = "published"
    mitre_technique_id: str = ""
    mitre_technique_name: str = ""
    mitre_tactic: str = ""
    cwe_id: str = ""
    cwe_name: str = ""
    affected_frameworks: list[dict[str, str]] = Field(default_factory=list)
    defences: list[dict[str, str]] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class IngestPaper(BaseModel):
    doi: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int = 2025
    url: str = ""
    ave_ids: list[str] = Field(default_factory=list)


class IngestIncident(BaseModel):
    incident_id: str
    title: str
    description: str = ""
    date: str = ""
    ave_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Ingest endpoints
# ---------------------------------------------------------------------------


@app.post("/v1/ingest/ave", status_code=status.HTTP_201_CREATED)
async def ingest_ave_card(card: IngestAVECard) -> dict[str, Any]:
    """Ingest an AVE card into the knowledge graph."""
    now = datetime.now(timezone.utc).isoformat()

    # Create AVECard node
    run_query(
        """
        MERGE (v:AVECard {ave_id: $ave_id})
        SET v.title = $title,
            v.description = $description,
            v.category = $category,
            v.severity = $severity,
            v.avss_score = $avss_score,
            v.status = $status,
            v.created_at = $created_at,
            v.updated_at = $updated_at
        """,
        {
            "ave_id": card.ave_id,
            "title": card.title,
            "description": card.description,
            "category": card.category,
            "severity": card.severity,
            "avss_score": card.avss_score,
            "status": card.status,
            "created_at": card.created_at or now,
            "updated_at": card.updated_at or now,
        },
    )

    # Link to Category
    if card.category:
        run_query(
            """
            MERGE (c:Category {name: $category})
            WITH c
            MATCH (v:AVECard {ave_id: $ave_id})
            MERGE (v)-[:BELONGS_TO]->(c)
            """,
            {"category": card.category, "ave_id": card.ave_id},
        )

    # Link to MITRE
    if card.mitre_technique_id:
        run_query(
            """
            MERGE (m:MITRETechnique {technique_id: $technique_id})
            SET m.name = $technique_name
            WITH m
            MATCH (v:AVECard {ave_id: $ave_id})
            MERGE (v)-[:MAPS_TO_TECHNIQUE]->(m)
            """,
            {
                "technique_id": card.mitre_technique_id,
                "technique_name": card.mitre_technique_name,
                "ave_id": card.ave_id,
            },
        )
        # Link technique to tactic
        if card.mitre_tactic:
            run_query(
                """
                MERGE (t:MITRETactic {name: $tactic})
                WITH t
                MATCH (m:MITRETechnique {technique_id: $technique_id})
                MERGE (m)-[:TECHNIQUE_OF]->(t)
                """,
                {"tactic": card.mitre_tactic, "technique_id": card.mitre_technique_id},
            )

    # Link to CWE
    if card.cwe_id:
        run_query(
            """
            MERGE (w:CWE {cwe_id: $cwe_id})
            SET w.name = $cwe_name
            WITH w
            MATCH (v:AVECard {ave_id: $ave_id})
            MERGE (v)-[:MAPS_TO_CWE]->(w)
            """,
            {"cwe_id": card.cwe_id, "cwe_name": card.cwe_name, "ave_id": card.ave_id},
        )

    # Link to frameworks
    for fw in card.affected_frameworks:
        run_query(
            """
            MERGE (f:Framework {name: $name})
            MERGE (fv:FrameworkVersion {name: $name, version: $version})
            MERGE (fv)-[:VERSION_OF]->(f)
            WITH fv
            MATCH (v:AVECard {ave_id: $ave_id})
            MERGE (v)-[:AFFECTS]->(fv)
            """,
            {
                "name": fw.get("name", "unknown"),
                "version": fw.get("version", "unknown"),
                "ave_id": card.ave_id,
            },
        )

    # Link to defences
    for defence in card.defences:
        run_query(
            """
            MERGE (d:Defence {name: $name})
            SET d.description = $description
            WITH d
            MATCH (v:AVECard {ave_id: $ave_id})
            MERGE (v)-[:MITIGATED_BY]->(d)
            """,
            {
                "name": defence.get("name", "Unknown"),
                "description": defence.get("description", ""),
                "ave_id": card.ave_id,
            },
        )

    return {"ave_id": card.ave_id, "status": "ingested", "ingested_at": now}


@app.post("/v1/ingest/paper", status_code=status.HTTP_201_CREATED)
async def ingest_paper(paper: IngestPaper) -> dict[str, Any]:
    """Add a research paper and link to relevant AVE cards."""
    run_query(
        """
        MERGE (p:Paper {doi: $doi})
        SET p.title = $title,
            p.authors = $authors,
            p.year = $year,
            p.url = $url
        """,
        {
            "doi": paper.doi,
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.year,
            "url": paper.url,
        },
    )
    for ave_id in paper.ave_ids:
        run_query(
            """
            MATCH (v:AVECard {ave_id: $ave_id})
            MATCH (p:Paper {doi: $doi})
            MERGE (v)-[:ANALYSED_BY]->(p)
            """,
            {"ave_id": ave_id, "doi": paper.doi},
        )
    return {"doi": paper.doi, "linked_ave_cards": len(paper.ave_ids)}


@app.post("/v1/ingest/incident", status_code=status.HTTP_201_CREATED)
async def ingest_incident(incident: IngestIncident) -> dict[str, Any]:
    """Add an incident report and link to relevant AVE cards."""
    run_query(
        """
        MERGE (i:Incident {incident_id: $incident_id})
        SET i.title = $title,
            i.description = $description,
            i.date = $date
        """,
        {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "description": incident.description,
            "date": incident.date,
        },
    )
    for ave_id in incident.ave_ids:
        run_query(
            """
            MATCH (v:AVECard {ave_id: $ave_id})
            MATCH (i:Incident {incident_id: $incident_id})
            MERGE (v)-[:EXPLOITED_IN]->(i)
            """,
            {"ave_id": ave_id, "incident_id": incident.incident_id},
        )
    return {"incident_id": incident.incident_id, "linked_ave_cards": len(incident.ave_ids)}


# ---------------------------------------------------------------------------
# Graph query endpoints
# ---------------------------------------------------------------------------


@app.get("/v1/graph/node/{node_id}")
async def get_node(node_id: str) -> dict[str, Any]:
    """Get a node and its direct relationships."""
    results = run_query(
        """
        MATCH (n {ave_id: $id})
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, collect({type: type(r), target: properties(m)}) AS outgoing
        """,
        {"id": node_id},
    )
    if not results:
        raise HTTPException(404, "Node not found")
    return results[0]


@app.get("/v1/graph/search")
async def search_graph(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Full-text search across AVE cards."""
    results = run_query(
        """
        CALL db.index.fulltext.queryNodes('ave_search', $query)
        YIELD node, score
        RETURN node.ave_id AS ave_id, node.title AS title,
               node.category AS category, node.severity AS severity,
               score
        ORDER BY score DESC
        LIMIT $limit
        """,
        {"query": q, "limit": limit},
    )
    return results


@app.get("/v1/graph/path")
async def shortest_path(
    from_id: str = Query(..., alias="from"),
    to_id: str = Query(..., alias="to"),
) -> dict[str, Any]:
    """Find shortest path between two nodes."""
    results = run_query(
        """
        MATCH (a {ave_id: $from}), (b {ave_id: $to})
        MATCH path = shortestPath((a)-[*..6]-(b))
        RETURN [n IN nodes(path) | properties(n)] AS nodes,
               [r IN relationships(path) | type(r)] AS relationships,
               length(path) AS hops
        """,
        {"from": from_id, "to": to_id},
    )
    if not results:
        return {"path": None, "message": "No path found"}
    return results[0]


@app.get("/v1/graph/neighbours/{node_id}")
async def get_neighbours(
    node_id: str,
    depth: int = Query(1, ge=1, le=3),
) -> list[dict[str, Any]]:
    """Get N-hop neighbours of a node."""
    results = run_query(
        f"""
        MATCH (start {{ave_id: $id}})
        CALL apoc.path.subgraphNodes(start, {{maxLevel: {depth}}})
        YIELD node
        RETURN properties(node) AS node_properties, labels(node) AS labels
        """,
        {"id": node_id},
    )
    return results


@app.get("/v1/graph/subgraph")
async def category_subgraph(
    category: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """Get the subgraph for a specific AVE category."""
    nodes = run_query(
        """
        MATCH (c:Category {name: $category})<-[:BELONGS_TO]-(v:AVECard)
        OPTIONAL MATCH (v)-[:MAPS_TO_TECHNIQUE]->(m:MITRETechnique)
        OPTIONAL MATCH (v)-[:MITIGATED_BY]->(d:Defence)
        RETURN v.ave_id AS ave_id, v.title AS title,
               v.severity AS severity, v.avss_score AS avss_score,
               collect(DISTINCT m.technique_id) AS mitre_techniques,
               collect(DISTINCT d.name) AS defences
        ORDER BY v.avss_score DESC
        LIMIT $limit
        """,
        {"category": category, "limit": limit},
    )
    return {"category": category, "node_count": len(nodes), "nodes": nodes}


# ---------------------------------------------------------------------------
# Impact analysis endpoints
# ---------------------------------------------------------------------------


@app.get("/v1/analysis/impact/{ave_id}")
async def impact_analysis(ave_id: str) -> dict[str, Any]:
    """Analyse the impact of a specific AVE card."""
    # Affected frameworks
    frameworks = run_query(
        """
        MATCH (v:AVECard {ave_id: $ave_id})-[:AFFECTS]->(fv:FrameworkVersion)-[:VERSION_OF]->(f:Framework)
        RETURN f.name AS framework, collect(fv.version) AS versions
        """,
        {"ave_id": ave_id},
    )

    # Enabled attack chains
    chains = run_query(
        """
        MATCH path = (v:AVECard {ave_id: $ave_id})-[:ENABLES*1..3]->(target:AVECard)
        RETURN [n IN nodes(path) | n.ave_id] AS chain,
               target.severity AS target_severity
        LIMIT 10
        """,
        {"ave_id": ave_id},
    )

    # Available defences
    defences = run_query(
        """
        MATCH (v:AVECard {ave_id: $ave_id})-[:MITIGATED_BY]->(d:Defence)
        RETURN d.name AS defence, d.description AS description
        """,
        {"ave_id": ave_id},
    )

    # Related research
    papers = run_query(
        """
        MATCH (v:AVECard {ave_id: $ave_id})-[:ANALYSED_BY]->(p:Paper)
        RETURN p.title AS title, p.doi AS doi, p.year AS year
        """,
        {"ave_id": ave_id},
    )

    return {
        "ave_id": ave_id,
        "affected_frameworks": frameworks,
        "attack_chains": chains,
        "available_defences": defences,
        "related_research": papers,
    }


@app.get("/v1/analysis/attack-chains")
async def attack_chains(
    min_length: int = Query(2, ge=2, le=5),
    max_severity: str = Query("critical"),
) -> list[dict[str, Any]]:
    """Discover multi-step attack chains."""
    results = run_query(
        f"""
        MATCH path = (start:AVECard)-[:ENABLES*{min_length}..5]->(end:AVECard)
        WHERE end.severity IN ['critical', 'high']
        RETURN [n IN nodes(path) | {{ave_id: n.ave_id, title: n.title, severity: n.severity}}] AS chain,
               length(path) AS chain_length
        ORDER BY chain_length DESC
        LIMIT 20
        """,
    )
    return results


@app.get("/v1/analysis/defence-coverage")
async def defence_coverage() -> dict[str, Any]:
    """Compute defence coverage matrix across categories."""
    results = run_query(
        """
        MATCH (c:Category)<-[:BELONGS_TO]-(v:AVECard)
        OPTIONAL MATCH (v)-[:MITIGATED_BY]->(d:Defence)
        WITH c.name AS category,
             count(v) AS total,
             count(d) AS defended
        RETURN category, total, defended,
               total - defended AS undefended,
               CASE WHEN total > 0
                    THEN round(toFloat(defended) / total * 100, 1)
                    ELSE 0 END AS coverage_pct
        ORDER BY coverage_pct ASC
        """,
    )
    return {"categories": results}


@app.get("/v1/analysis/framework-risk/{framework_name}")
async def framework_risk(framework_name: str) -> dict[str, Any]:
    """Risk profile for a specific agent framework."""
    results = run_query(
        """
        MATCH (f:Framework {name: $name})<-[:VERSION_OF]-(fv:FrameworkVersion)<-[:AFFECTS]-(v:AVECard)
        RETURN fv.version AS version,
               count(v) AS vuln_count,
               collect(DISTINCT v.severity) AS severities,
               collect(DISTINCT v.category) AS categories
        ORDER BY fv.version DESC
        """,
        {"name": framework_name},
    )
    return {"framework": framework_name, "versions": results}


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@app.get("/v1/stats/overview")
async def stats_overview() -> dict[str, Any]:
    """Graph-wide statistics."""
    counts = run_query(
        """
        MATCH (v:AVECard) WITH count(v) AS cards
        MATCH (c:Category) WITH cards, count(c) AS categories
        MATCH (m:MITRETechnique) WITH cards, categories, count(m) AS techniques
        MATCH (d:Defence) WITH cards, categories, techniques, count(d) AS defences
        RETURN cards, categories, techniques, defences
        """,
    )
    return counts[0] if counts else {"cards": 0, "categories": 0, "techniques": 0, "defences": 0}


@app.get("/v1/stats/categories")
async def stats_categories() -> list[dict[str, Any]]:
    """Per-category breakdown."""
    return run_query(
        """
        MATCH (c:Category)<-[:BELONGS_TO]-(v:AVECard)
        RETURN c.name AS category,
               count(v) AS card_count,
               collect(DISTINCT v.severity) AS severities
        ORDER BY card_count DESC
        """,
    )


@app.get("/v1/stats/trends")
async def stats_trends(period: str = Query("monthly")) -> list[dict[str, Any]]:
    """Temporal trend analysis."""
    return run_query(
        """
        MATCH (v:AVECard)
        WHERE v.created_at IS NOT NULL
        WITH date(left(v.created_at, 10)) AS created_date, v
        RETURN toString(created_date.year) + '-' + 
               CASE WHEN created_date.month < 10 
                    THEN '0' + toString(created_date.month)
                    ELSE toString(created_date.month) END AS month,
               count(v) AS new_cards,
               collect(DISTINCT v.category) AS categories
        ORDER BY month DESC
        LIMIT 24
        """,
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    driver = get_driver()
    if driver:
        try:
            driver.verify_connectivity()
            return {"status": "healthy", "neo4j": "connected"}
        except Exception:
            return {"status": "degraded", "neo4j": "disconnected"}
    return {"status": "degraded", "neo4j": "not_configured"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--init-schema", action="store_true")
    parser.add_argument("--ingest-all", action="store_true")
    args = parser.parse_args()

    if args.init_schema:
        init_schema()

    uvicorn.run(app, host="0.0.0.0", port=8500)
