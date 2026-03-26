"""
NAIL TAXII 2.1 Server — Threat intelligence sharing for AVE data.

Implements OASIS TAXII 2.1 protocol (https://docs.oasis-open.org/cti/taxii/v2.1/)
translating AVE vulnerability cards into STIX 2.1 objects.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

TAXII_CONTENT_TYPE = "application/taxii+json;version=2.1"
STIX_CONTENT_TYPE = "application/stix+json;version=2.1"

app = FastAPI(
    title="NAIL TAXII 2.1 Server",
    description="TAXII 2.1 threat intelligence sharing for AVE agentic AI vulnerabilities.",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("taxii.server")

# ---------------------------------------------------------------------------
# NAIL identity (STIX)
# ---------------------------------------------------------------------------

NAIL_IDENTITY_ID = "identity--a1b2c3d4-e5f6-7890-abcd-ef1234567890"
NAIL_IDENTITY = {
    "type": "identity",
    "spec_version": "2.1",
    "id": NAIL_IDENTITY_ID,
    "created": "2025-01-01T00:00:00.000Z",
    "modified": "2025-01-01T00:00:00.000Z",
    "name": "NAIL Institute for Agentic Security",
    "description": "Open research institute cataloguing agentic AI vulnerabilities.",
    "identity_class": "organization",
    "sectors": ["technology"],
    "contact_information": "threatintel@nailinstitute.org",
}

# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------

COLLECTIONS = {
    "ave-vulnerabilities": {
        "id": "ave-vulnerabilities",
        "title": "AVE Vulnerabilities",
        "description": "Published AVE vulnerability cards as STIX Vulnerability objects.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
    "ave-attack-patterns": {
        "id": "ave-attack-patterns",
        "title": "AVE Attack Patterns",
        "description": "Attack techniques from AVE cards as STIX Attack Pattern objects.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
    "ave-defences": {
        "id": "ave-defences",
        "title": "AVE Defences",
        "description": "Recommended defences as STIX Course of Action objects.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
    "ave-indicators": {
        "id": "ave-indicators",
        "title": "AVE Indicators",
        "description": "Detection indicators derived from AVE evidence.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
    "ave-reports": {
        "id": "ave-reports",
        "title": "AVE Reports",
        "description": "Aggregated threat reports bundling related STIX objects.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
    "community-contributions": {
        "id": "community-contributions",
        "title": "Community Contributions",
        "description": "Inbound threat intelligence from partners and community.",
        "can_read": True,
        "can_write": True,
        "media_types": [STIX_CONTENT_TYPE],
    },
}

# ---------------------------------------------------------------------------
# In-memory STIX object store (production → PostgreSQL)
# ---------------------------------------------------------------------------

# collection_id → list of STIX objects
stix_store: dict[str, list[dict[str, Any]]] = {
    cid: [] for cid in COLLECTIONS
}

# API keys (production → database)
API_KEYS: dict[str, dict[str, Any]] = {
    "demo-key-001": {
        "org": "Demo Organization",
        "tier": "partner",
        "collections_read": list(COLLECTIONS.keys()),
        "collections_write": ["community-contributions"],
        "rate_limit": 300,
    },
}

# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------


def _authenticate(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if token not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    return API_KEYS[token]


def _check_read(auth: dict[str, Any], collection_id: str) -> None:
    if collection_id not in auth.get("collections_read", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Read access denied.")


def _check_write(auth: dict[str, Any], collection_id: str) -> None:
    if collection_id not in auth.get("collections_write", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access denied.")


# ---------------------------------------------------------------------------
# AVE → STIX translator
# ---------------------------------------------------------------------------


class AVEToSTIXTranslator:
    """Translate AVE vulnerability cards into STIX 2.1 objects."""

    @staticmethod
    def ave_to_vulnerability(ave_card: dict[str, Any]) -> dict[str, Any]:
        """Convert an AVE card to a STIX Vulnerability object."""
        ave_id = ave_card.get("ave_id", "UNKNOWN")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        external_refs = [
            {
                "source_name": "NAIL AVE Database",
                "external_id": ave_id,
                "url": f"https://nailinstitute.org/cards/{ave_id}",
            }
        ]

        # Add CWE reference if present
        cwe = ave_card.get("cwe_mapping", {})
        if cwe.get("cwe_id"):
            external_refs.append(
                {
                    "source_name": "cwe",
                    "external_id": cwe["cwe_id"],
                    "url": f"https://cwe.mitre.org/data/definitions/{cwe['cwe_id'].replace('CWE-', '')}.html",
                }
            )

        vuln: dict[str, Any] = {
            "type": "vulnerability",
            "spec_version": "2.1",
            "id": f"vulnerability--{uuid.uuid5(uuid.NAMESPACE_URL, ave_id)}",
            "created": ave_card.get("created_at", now),
            "modified": ave_card.get("updated_at", now),
            "name": ave_id,
            "description": ave_card.get("description", ave_card.get("title", "")),
            "external_references": external_refs,
            "created_by_ref": NAIL_IDENTITY_ID,
            "x_ave_id": ave_id,
            "x_ave_category": ave_card.get("category", ""),
            "x_ave_status": ave_card.get("status", ""),
            "x_avss_score": ave_card.get("avss", {}).get("score", 0),
            "x_avss_severity": ave_card.get("severity", ""),
        }
        return vuln

    @staticmethod
    def ave_to_attack_pattern(ave_card: dict[str, Any]) -> dict[str, Any]:
        """Convert AVE category/technique to a STIX Attack Pattern."""
        ave_id = ave_card.get("ave_id", "UNKNOWN")
        category = ave_card.get("category", "unknown")
        mitre = ave_card.get("mitre_mapping", {})
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        external_refs = []
        if mitre.get("technique_id"):
            external_refs.append(
                {
                    "source_name": "mitre-attack",
                    "external_id": mitre["technique_id"],
                    "url": f"https://attack.mitre.org/techniques/{mitre['technique_id'].replace('.', '/')}/",
                }
            )

        return {
            "type": "attack-pattern",
            "spec_version": "2.1",
            "id": f"attack-pattern--{uuid.uuid5(uuid.NAMESPACE_URL, f'{ave_id}-{category}')}",
            "created": ave_card.get("created_at", now),
            "modified": ave_card.get("updated_at", now),
            "name": f"AVE: {category.replace('_', ' ').title()}",
            "description": ave_card.get("description", ""),
            "external_references": external_refs,
            "created_by_ref": NAIL_IDENTITY_ID,
            "x_ave_category": category,
        }

    @staticmethod
    def ave_to_course_of_action(
        ave_card: dict[str, Any], defence: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert an AVE defence recommendation to a STIX Course of Action."""
        ave_id = ave_card.get("ave_id", "UNKNOWN")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        defence_name = defence.get("name", "Unknown Defence")

        return {
            "type": "course-of-action",
            "spec_version": "2.1",
            "id": f"course-of-action--{uuid.uuid5(uuid.NAMESPACE_URL, f'{ave_id}-{defence_name}')}",
            "created": ave_card.get("created_at", now),
            "modified": ave_card.get("updated_at", now),
            "name": defence_name,
            "description": defence.get("description", ""),
            "created_by_ref": NAIL_IDENTITY_ID,
            "x_implementation": defence.get("implementation", ""),
        }

    @staticmethod
    def create_relationship(
        source_id: str,
        target_id: str,
        relationship_type: str,
    ) -> dict[str, Any]:
        """Create a STIX Relationship between two objects."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        return {
            "type": "relationship",
            "spec_version": "2.1",
            "id": f"relationship--{uuid.uuid5(uuid.NAMESPACE_URL, f'{source_id}-{relationship_type}-{target_id}')}",
            "created": now,
            "modified": now,
            "relationship_type": relationship_type,
            "source_ref": source_id,
            "target_ref": target_id,
            "created_by_ref": NAIL_IDENTITY_ID,
        }

    def translate_full(self, ave_card: dict[str, Any]) -> list[dict[str, Any]]:
        """Translate a full AVE card into all related STIX objects."""
        objects: list[dict[str, Any]] = []

        vuln = self.ave_to_vulnerability(ave_card)
        objects.append(vuln)

        ap = self.ave_to_attack_pattern(ave_card)
        objects.append(ap)

        # Relationship: vulnerability uses attack-pattern
        objects.append(
            self.create_relationship(vuln["id"], ap["id"], "uses")
        )

        # Course of Action for each defence
        for defence in ave_card.get("defences", []):
            coa = self.ave_to_course_of_action(ave_card, defence)
            objects.append(coa)
            # Relationship: course-of-action mitigates vulnerability
            objects.append(
                self.create_relationship(coa["id"], vuln["id"], "mitigates")
            )

        return objects


translator = AVEToSTIXTranslator()

# ---------------------------------------------------------------------------
# TAXII 2.1 discovery endpoints
# ---------------------------------------------------------------------------


@app.get("/taxii2/")
async def taxii_discovery(authorization: str | None = Header(None)):
    """TAXII 2.1 Server Discovery."""
    _authenticate(authorization)
    return JSONResponse(
        content={
            "title": "NAIL Institute TAXII Server",
            "description": "TAXII 2.1 server for AVE agentic AI threat intelligence.",
            "contact": "threatintel@nailinstitute.org",
            "default": "https://taxii.nailinstitute.org/taxii2/api/",
            "api_roots": ["https://taxii.nailinstitute.org/taxii2/api/"],
        },
        media_type=TAXII_CONTENT_TYPE,
    )


@app.get("/taxii2/api/")
async def api_root(authorization: str | None = Header(None)):
    """TAXII 2.1 API Root information."""
    _authenticate(authorization)
    return JSONResponse(
        content={
            "title": "NAIL AVE Threat Intelligence",
            "description": "API root for AVE agentic AI vulnerability intelligence.",
            "versions": ["application/taxii+json;version=2.1"],
            "max_content_length": 10485760,
        },
        media_type=TAXII_CONTENT_TYPE,
    )


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


@app.get("/taxii2/api/collections/")
async def list_collections(authorization: str | None = Header(None)):
    """List available TAXII collections."""
    auth = _authenticate(authorization)
    readable = auth.get("collections_read", [])
    cols = [
        COLLECTIONS[cid]
        for cid in COLLECTIONS
        if cid in readable
    ]
    return JSONResponse(
        content={"collections": cols},
        media_type=TAXII_CONTENT_TYPE,
    )


@app.get("/taxii2/api/collections/{collection_id}/")
async def get_collection(
    collection_id: str,
    authorization: str | None = Header(None),
):
    """Get collection details."""
    auth = _authenticate(authorization)
    if collection_id not in COLLECTIONS:
        raise HTTPException(404, "Collection not found")
    _check_read(auth, collection_id)
    return JSONResponse(
        content=COLLECTIONS[collection_id],
        media_type=TAXII_CONTENT_TYPE,
    )


# ---------------------------------------------------------------------------
# Objects
# ---------------------------------------------------------------------------


@app.get("/taxii2/api/collections/{collection_id}/objects/")
async def get_objects(
    collection_id: str,
    authorization: str | None = Header(None),
    added_after: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=10000),
    next_cursor: Optional[str] = Query(None, alias="next"),
    match_type: Optional[str] = Query(None, alias="match[type]"),
    match_id: Optional[str] = Query(None, alias="match[id]"),
):
    """Get STIX objects from a collection with filtering and pagination."""
    auth = _authenticate(authorization)
    if collection_id not in COLLECTIONS:
        raise HTTPException(404, "Collection not found")
    _check_read(auth, collection_id)

    objects = list(stix_store.get(collection_id, []))

    # Filtering
    if added_after:
        objects = [
            o for o in objects
            if o.get("created", "") > added_after
        ]

    if match_type:
        types = set(match_type.split(","))
        objects = [o for o in objects if o.get("type") in types]

    if match_id:
        ids = set(match_id.split(","))
        objects = [o for o in objects if o.get("id") in ids]

    # Pagination
    total = len(objects)
    objects = objects[:limit]

    envelope = {
        "more": total > limit,
        "objects": objects,
    }

    if total > limit:
        envelope["next"] = f"cursor-{limit}"

    return JSONResponse(content=envelope, media_type=STIX_CONTENT_TYPE)


@app.post("/taxii2/api/collections/{collection_id}/objects/")
async def add_objects(
    collection_id: str,
    request: Request,
    authorization: str | None = Header(None),
):
    """Add STIX objects to a writable collection."""
    auth = _authenticate(authorization)
    if collection_id not in COLLECTIONS:
        raise HTTPException(404, "Collection not found")
    _check_write(auth, collection_id)

    if not COLLECTIONS[collection_id].get("can_write"):
        raise HTTPException(403, "Collection is read-only")

    body = await request.json()
    objects = body.get("objects", [])

    if not objects:
        raise HTTPException(400, "No objects provided")

    successes = []
    failures = []

    for obj in objects:
        if "type" not in obj or "id" not in obj:
            failures.append(
                {"id": obj.get("id", "unknown"), "message": "Missing type or id"}
            )
            continue
        stix_store[collection_id].append(obj)
        successes.append(obj["id"])

    status_obj = {
        "id": f"status--{uuid.uuid4()}",
        "status": "complete",
        "total_count": len(objects),
        "success_count": len(successes),
        "failure_count": len(failures),
        "successes": [{"id": s, "version": "2.1"} for s in successes],
        "failures": failures,
    }

    return JSONResponse(
        content=status_obj,
        media_type=TAXII_CONTENT_TYPE,
        status_code=status.HTTP_202_ACCEPTED,
    )


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


@app.get("/taxii2/api/collections/{collection_id}/manifest/")
async def get_manifest(
    collection_id: str,
    authorization: str | None = Header(None),
    limit: int = Query(100, ge=1, le=10000),
):
    """Get the manifest for a collection (object metadata without full content)."""
    auth = _authenticate(authorization)
    if collection_id not in COLLECTIONS:
        raise HTTPException(404, "Collection not found")
    _check_read(auth, collection_id)

    objects = stix_store.get(collection_id, [])
    manifest_entries = [
        {
            "id": obj.get("id"),
            "date_added": obj.get("created", ""),
            "version": obj.get("modified", obj.get("created", "")),
            "media_type": STIX_CONTENT_TYPE,
        }
        for obj in objects[:limit]
    ]

    return JSONResponse(
        content={
            "more": len(objects) > limit,
            "objects": manifest_entries,
        },
        media_type=TAXII_CONTENT_TYPE,
    )


# ---------------------------------------------------------------------------
# AVE ingest endpoint (internal)
# ---------------------------------------------------------------------------


@app.post("/v1/ingest/ave")
async def ingest_ave_card(
    request: Request,
    authorization: str | None = Header(None),
):
    """Ingest an AVE card and translate to STIX objects across collections."""
    _authenticate(authorization)

    ave_card = await request.json()
    stix_objects = translator.translate_full(ave_card)

    # Distribute objects to appropriate collections
    for obj in stix_objects:
        obj_type = obj.get("type", "")
        if obj_type == "vulnerability":
            stix_store["ave-vulnerabilities"].append(obj)
        elif obj_type == "attack-pattern":
            stix_store["ave-attack-patterns"].append(obj)
        elif obj_type == "course-of-action":
            stix_store["ave-defences"].append(obj)
        elif obj_type == "indicator":
            stix_store["ave-indicators"].append(obj)
        elif obj_type == "relationship":
            # Store relationships in the vulnerability collection
            stix_store["ave-vulnerabilities"].append(obj)

    return {
        "ave_id": ave_card.get("ave_id"),
        "stix_objects_created": len(stix_objects),
        "object_types": list({o["type"] for o in stix_objects}),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@app.get("/v1/stats")
async def stats(authorization: str | None = Header(None)):
    """Collection statistics."""
    _authenticate(authorization)
    return {
        "collections": {
            cid: {"object_count": len(objs)}
            for cid, objs in stix_store.items()
        },
        "total_objects": sum(len(objs) for objs in stix_store.values()),
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "nail-taxii-2.1"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8400)
