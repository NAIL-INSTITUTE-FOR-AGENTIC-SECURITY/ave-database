"""
Real-Time Global Threat Map — Core map server.

Live geospatial visualisation of agentic AI threats worldwide with
heat maps, attack flow tracking, regional intelligence overlays,
configurable alert zones, and time-series replay.
"""

from __future__ import annotations

import math
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
    title="NAIL Real-Time Global Threat Map",
    description=(
        "Live geospatial visualisation of agentic AI threats worldwide "
        "with heat maps, attack flows, and regional intelligence."
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
# Constants — Regions & Geo Data
# ---------------------------------------------------------------------------

REGIONS: dict[str, dict[str, Any]] = {
    "NA": {"name": "North America", "lat": 40.0, "lon": -100.0},
    "EU": {"name": "Europe", "lat": 50.0, "lon": 10.0},
    "APAC": {"name": "Asia-Pacific", "lat": 30.0, "lon": 120.0},
    "LATAM": {"name": "Latin America", "lat": -15.0, "lon": -60.0},
    "MEA": {"name": "Middle East & Africa", "lat": 25.0, "lon": 45.0},
    "CIS": {"name": "CIS / Eastern Europe", "lat": 55.0, "lon": 60.0},
}

# City lookup for geo resolution
CITIES: dict[str, dict[str, Any]] = {
    "new_york": {"name": "New York", "country": "US", "region": "NA", "lat": 40.7128, "lon": -74.0060},
    "san_francisco": {"name": "San Francisco", "country": "US", "region": "NA", "lat": 37.7749, "lon": -122.4194},
    "washington_dc": {"name": "Washington DC", "country": "US", "region": "NA", "lat": 38.9072, "lon": -77.0369},
    "toronto": {"name": "Toronto", "country": "CA", "region": "NA", "lat": 43.6532, "lon": -79.3832},
    "london": {"name": "London", "country": "GB", "region": "EU", "lat": 51.5074, "lon": -0.1278},
    "berlin": {"name": "Berlin", "country": "DE", "region": "EU", "lat": 52.5200, "lon": 13.4050},
    "paris": {"name": "Paris", "country": "FR", "region": "EU", "lat": 48.8566, "lon": 2.3522},
    "amsterdam": {"name": "Amsterdam", "country": "NL", "region": "EU", "lat": 52.3676, "lon": 4.9041},
    "tokyo": {"name": "Tokyo", "country": "JP", "region": "APAC", "lat": 35.6762, "lon": 139.6503},
    "singapore": {"name": "Singapore", "country": "SG", "region": "APAC", "lat": 1.3521, "lon": 103.8198},
    "sydney": {"name": "Sydney", "country": "AU", "region": "APAC", "lat": -33.8688, "lon": 151.2093},
    "beijing": {"name": "Beijing", "country": "CN", "region": "APAC", "lat": 39.9042, "lon": 116.4074},
    "seoul": {"name": "Seoul", "country": "KR", "region": "APAC", "lat": 37.5665, "lon": 126.9780},
    "mumbai": {"name": "Mumbai", "country": "IN", "region": "APAC", "lat": 19.0760, "lon": 72.8777},
    "sao_paulo": {"name": "São Paulo", "country": "BR", "region": "LATAM", "lat": -23.5505, "lon": -46.6333},
    "dubai": {"name": "Dubai", "country": "AE", "region": "MEA", "lat": 25.2048, "lon": 55.2708},
    "tel_aviv": {"name": "Tel Aviv", "country": "IL", "region": "MEA", "lat": 32.0853, "lon": 34.7818},
    "moscow": {"name": "Moscow", "country": "RU", "region": "CIS", "lat": 55.7558, "lon": 37.6173},
}

AVE_CATEGORIES = [
    "prompt_injection", "tool_misuse", "memory_poisoning", "goal_hijacking",
    "identity_spoofing", "privilege_escalation", "data_exfiltration",
    "resource_exhaustion", "multi_agent_manipulation", "context_overflow",
    "guardrail_bypass", "output_manipulation", "supply_chain_compromise",
    "model_extraction", "reward_hacking", "capability_elicitation",
    "alignment_subversion", "delegation_abuse",
]

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ThreatSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertLevel(str, Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class GeoPoint(BaseModel):
    lat: float
    lon: float
    city: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None


class ThreatEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"THREAT-{uuid.uuid4().hex[:10].upper()}")
    title: str
    category: str
    severity: ThreatSeverity
    source_location: GeoPoint
    target_location: Optional[GeoPoint] = None
    description: str = ""
    ave_ids: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    indicators: list[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    active: bool = True


class ThreatCreate(BaseModel):
    title: str
    category: str
    severity: ThreatSeverity
    source_city: str
    target_city: Optional[str] = None
    description: str = ""
    ave_ids: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    indicators: list[str] = Field(default_factory=list)


class AlertZone(BaseModel):
    id: str = Field(default_factory=lambda: f"ZONE-{uuid.uuid4().hex[:8].upper()}")
    name: str
    region: str
    threshold_count: int = 5
    threshold_severity: ThreatSeverity = ThreatSeverity.MEDIUM
    window_minutes: int = 60
    active: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AlertZoneCreate(BaseModel):
    name: str
    region: str
    threshold_count: int = 5
    threshold_severity: ThreatSeverity = ThreatSeverity.MEDIUM
    window_minutes: int = 60


class TriggeredAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    zone_id: str
    zone_name: str
    level: AlertLevel
    threat_count: int
    message: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RegionSummary(BaseModel):
    code: str
    name: str
    lat: float
    lon: float
    total_threats: int
    by_severity: dict[str, int]
    by_category: dict[str, int]
    top_categories: list[str]
    alert_level: AlertLevel
    trend: str  # rising / falling / stable


class HeatmapPoint(BaseModel):
    lat: float
    lon: float
    intensity: float
    threat_count: int


class AttackFlow(BaseModel):
    source: GeoPoint
    target: GeoPoint
    threat_id: str
    category: str
    severity: str
    timestamp: str


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → TimescaleDB + Redis)
# ---------------------------------------------------------------------------

THREATS: dict[str, ThreatEvent] = {}
ALERT_ZONES: dict[str, AlertZone] = {}
TRIGGERED_ALERTS: list[TriggeredAlert] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


def _resolve_city(city_key: str) -> GeoPoint:
    city_key = city_key.lower().replace(" ", "_").replace("-", "_")
    if city_key in CITIES:
        c = CITIES[city_key]
        return GeoPoint(
            lat=c["lat"], lon=c["lon"],
            city=c["name"], country=c["country"], region=c["region"],
        )
    # Fallback: random jitter around region center
    region = random.choice(list(REGIONS.values()))
    return GeoPoint(
        lat=region["lat"] + random.uniform(-5, 5),
        lon=region["lon"] + random.uniform(-5, 5),
        city=city_key,
        country="UNKNOWN",
        region="UNKNOWN",
    )


def _severity_weight(sev: ThreatSeverity) -> float:
    return {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25, "info": 0.1}[sev.value]


def _region_alert_level(threats: list[ThreatEvent]) -> AlertLevel:
    if not threats:
        return AlertLevel.GREEN
    weighted = sum(_severity_weight(t.severity) for t in threats)
    if weighted >= 10:
        return AlertLevel.RED
    elif weighted >= 5:
        return AlertLevel.ORANGE
    elif weighted >= 2:
        return AlertLevel.YELLOW
    return AlertLevel.GREEN


def _check_alert_zones(new_threat: ThreatEvent) -> None:
    """Evaluate all active zones against the new threat."""
    now = _now()
    for zone in ALERT_ZONES.values():
        if not zone.active:
            continue
        if new_threat.source_location.region != zone.region:
            continue

        window_start = (now - timedelta(minutes=zone.window_minutes)).isoformat()
        recent = [
            t for t in THREATS.values()
            if t.source_location.region == zone.region
            and t.timestamp >= window_start
            and _severity_weight(t.severity) >= _severity_weight(zone.threshold_severity)
        ]

        if len(recent) >= zone.threshold_count:
            # Determine alert level
            total_weight = sum(_severity_weight(t.severity) for t in recent)
            if total_weight >= zone.threshold_count * 0.75:
                level = AlertLevel.RED
            elif total_weight >= zone.threshold_count * 0.5:
                level = AlertLevel.ORANGE
            else:
                level = AlertLevel.YELLOW

            alert = TriggeredAlert(
                zone_id=zone.id,
                zone_name=zone.name,
                level=level,
                threat_count=len(recent),
                message=f"Zone '{zone.name}' threshold breached: {len(recent)} threats in {zone.window_minutes}min",
            )
            TRIGGERED_ALERTS.append(alert)


# ---------------------------------------------------------------------------
# Seed Data — 20 threats across all regions
# ---------------------------------------------------------------------------

def _seed() -> None:
    city_keys = list(CITIES.keys())
    now = _now()

    seed_threats = [
        ("Prompt relay attack on LangChain cluster", "prompt_injection", ThreatSeverity.CRITICAL, "new_york", "london", ["LangChain"]),
        ("Tool misuse in production CrewAI agent", "tool_misuse", ThreatSeverity.HIGH, "san_francisco", "tokyo", ["CrewAI"]),
        ("Memory poisoning via context overflow", "memory_poisoning", ThreatSeverity.HIGH, "berlin", None, ["AutoGen"]),
        ("Goal hijacking in multi-agent system", "goal_hijacking", ThreatSeverity.CRITICAL, "singapore", "sydney", ["LlamaIndex"]),
        ("Identity spoofing across federated agents", "identity_spoofing", ThreatSeverity.MEDIUM, "london", "paris", ["LangChain"]),
        ("Privilege escalation via tool schema confusion", "privilege_escalation", ThreatSeverity.HIGH, "tokyo", "seoul", ["CrewAI"]),
        ("Data exfiltration through retrieval pipeline", "data_exfiltration", ThreatSeverity.CRITICAL, "toronto", "new_york", ["LlamaIndex"]),
        ("Resource exhaustion DDoS on agent endpoints", "resource_exhaustion", ThreatSeverity.MEDIUM, "sao_paulo", None, []),
        ("Multi-agent coordination exploit", "multi_agent_manipulation", ThreatSeverity.HIGH, "mumbai", "singapore", ["AutoGen"]),
        ("Context window overflow attack", "context_overflow", ThreatSeverity.MEDIUM, "dubai", None, ["LangChain"]),
        ("Guardrail bypass via encoding tricks", "guardrail_bypass", ThreatSeverity.CRITICAL, "amsterdam", "berlin", ["LangChain", "CrewAI"]),
        ("Output manipulation in code generation", "output_manipulation", ThreatSeverity.HIGH, "moscow", None, ["AutoGen"]),
        ("Supply chain package compromise", "supply_chain_compromise", ThreatSeverity.CRITICAL, "beijing", "san_francisco", []),
        ("Model extraction via API probing", "model_extraction", ThreatSeverity.MEDIUM, "tel_aviv", None, []),
        ("Reward hacking in RLHF pipeline", "reward_hacking", ThreatSeverity.HIGH, "washington_dc", None, []),
        ("Capability elicitation via jailbreak", "capability_elicitation", ThreatSeverity.HIGH, "paris", "london", ["LangChain"]),
        ("Alignment subversion in fine-tuned model", "alignment_subversion", ThreatSeverity.CRITICAL, "seoul", "tokyo", []),
        ("Delegation abuse across agent hierarchy", "delegation_abuse", ThreatSeverity.MEDIUM, "sydney", "mumbai", ["CrewAI"]),
        ("Prompt injection via PDF upload", "prompt_injection", ThreatSeverity.HIGH, "london", "amsterdam", ["LlamaIndex"]),
        ("Tool sandbox escape in CI pipeline", "tool_misuse", ThreatSeverity.CRITICAL, "san_francisco", "toronto", ["AutoGen"]),
    ]

    for i, (title, cat, sev, src, tgt, fws) in enumerate(seed_threats):
        t_offset = timedelta(hours=random.randint(0, 72))
        ts = (now - t_offset).isoformat()
        source = _resolve_city(src)
        target = _resolve_city(tgt) if tgt else None

        threat = ThreatEvent(
            title=title,
            category=cat,
            severity=sev,
            source_location=source,
            target_location=target,
            frameworks=fws,
            timestamp=ts,
        )
        THREATS[threat.id] = threat

    # Default alert zones
    for code, info in REGIONS.items():
        zone = AlertZone(name=f"{info['name']} Watch Zone", region=code)
        ALERT_ZONES[zone.id] = zone


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "global-threat-map",
        "version": "1.0.0",
        "threats": len(THREATS),
        "alert_zones": len(ALERT_ZONES),
        "triggered_alerts": len(TRIGGERED_ALERTS),
    }


# ---- Threat CRUD ---------------------------------------------------------

@app.post("/v1/threats", status_code=status.HTTP_201_CREATED)
async def ingest_threat(data: ThreatCreate):
    if data.category not in AVE_CATEGORIES:
        raise HTTPException(400, f"Invalid category. Must be one of: {AVE_CATEGORIES}")

    source = _resolve_city(data.source_city)
    target = _resolve_city(data.target_city) if data.target_city else None

    threat = ThreatEvent(
        title=data.title,
        category=data.category,
        severity=data.severity,
        source_location=source,
        target_location=target,
        description=data.description,
        ave_ids=data.ave_ids,
        frameworks=data.frameworks,
        indicators=data.indicators,
    )
    THREATS[threat.id] = threat
    _check_alert_zones(threat)

    return {"id": threat.id, "region": source.region, "severity": threat.severity.value}


@app.get("/v1/threats")
async def list_threats(
    severity: Optional[ThreatSeverity] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    active: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=500),
):
    threats = list(THREATS.values())
    if severity:
        threats = [t for t in threats if t.severity == severity]
    if category:
        threats = [t for t in threats if t.category == category]
    if region:
        threats = [t for t in threats if t.source_location.region == region]
    if active is not None:
        threats = [t for t in threats if t.active == active]
    threats.sort(key=lambda t: t.timestamp, reverse=True)
    return {"count": len(threats[:limit]), "threats": [t.dict() for t in threats[:limit]]}


@app.get("/v1/threats/{threat_id}")
async def get_threat(threat_id: str):
    if threat_id not in THREATS:
        raise HTTPException(404, "Threat not found")
    return THREATS[threat_id].dict()


# ---- Heat Map ------------------------------------------------------------

@app.get("/v1/map/heatmap")
async def heatmap(
    severity_min: ThreatSeverity = ThreatSeverity.LOW,
    hours: int = Query(24, ge=1, le=720),
):
    cutoff = (_now() - timedelta(hours=hours)).isoformat()
    min_weight = _severity_weight(severity_min)

    # Aggregate by rounded coordinates (grid cells)
    grid: dict[tuple[int, int], list[ThreatEvent]] = defaultdict(list)
    for t in THREATS.values():
        if t.timestamp < cutoff:
            continue
        if _severity_weight(t.severity) < min_weight:
            continue
        key = (round(t.source_location.lat), round(t.source_location.lon))
        grid[key].append(t)

    points: list[dict[str, Any]] = []
    for (lat, lon), threats in grid.items():
        intensity = sum(_severity_weight(t.severity) for t in threats)
        points.append(HeatmapPoint(
            lat=lat, lon=lon,
            intensity=round(intensity, 2),
            threat_count=len(threats),
        ).dict())

    return {
        "type": "FeatureCollection",
        "window_hours": hours,
        "point_count": len(points),
        "points": points,
    }


# ---- Attack Flows --------------------------------------------------------

@app.get("/v1/map/flows")
async def attack_flows(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=1000),
):
    cutoff = (_now() - timedelta(hours=hours)).isoformat()
    flows: list[dict[str, Any]] = []
    for t in THREATS.values():
        if t.timestamp < cutoff or t.target_location is None:
            continue
        flows.append(AttackFlow(
            source=t.source_location,
            target=t.target_location,
            threat_id=t.id,
            category=t.category,
            severity=t.severity.value,
            timestamp=t.timestamp,
        ).dict())

    flows.sort(key=lambda f: f["timestamp"], reverse=True)
    return {"count": len(flows[:limit]), "flows": flows[:limit]}


# ---- Regional Intelligence -----------------------------------------------

@app.get("/v1/map/regions")
async def region_summaries():
    summaries: list[dict[str, Any]] = []
    for code, info in REGIONS.items():
        region_threats = [
            t for t in THREATS.values()
            if t.source_location.region == code
        ]
        by_sev = Counter(t.severity.value for t in region_threats)
        by_cat = Counter(t.category for t in region_threats)
        top_cats = [c for c, _ in by_cat.most_common(5)]

        # Trend: compare last 24h vs previous 24h
        now = _now()
        last_24 = sum(
            1 for t in region_threats
            if t.timestamp >= (now - timedelta(hours=24)).isoformat()
        )
        prev_24 = sum(
            1 for t in region_threats
            if (now - timedelta(hours=48)).isoformat() <= t.timestamp < (now - timedelta(hours=24)).isoformat()
        )
        if last_24 > prev_24 * 1.2:
            trend = "rising"
        elif last_24 < prev_24 * 0.8:
            trend = "falling"
        else:
            trend = "stable"

        summaries.append(RegionSummary(
            code=code,
            name=info["name"],
            lat=info["lat"],
            lon=info["lon"],
            total_threats=len(region_threats),
            by_severity=dict(by_sev),
            by_category=dict(by_cat),
            top_categories=top_cats,
            alert_level=_region_alert_level(region_threats),
            trend=trend,
        ).dict())

    return {"regions": summaries}


@app.get("/v1/map/regions/{code}")
async def region_detail(code: str):
    code = code.upper()
    if code not in REGIONS:
        raise HTTPException(404, f"Region not found. Valid: {list(REGIONS.keys())}")

    info = REGIONS[code]
    region_threats = [
        t for t in THREATS.values()
        if t.source_location.region == code
    ]
    by_sev = Counter(t.severity.value for t in region_threats)
    by_cat = Counter(t.category for t in region_threats)
    by_fw = Counter(
        fw for t in region_threats for fw in t.frameworks
    )

    # Daily counts for last 7 days
    now = _now()
    daily: list[dict[str, Any]] = []
    for d in range(7):
        day_start = (now - timedelta(days=d + 1)).isoformat()
        day_end = (now - timedelta(days=d)).isoformat()
        count = sum(
            1 for t in region_threats
            if day_start <= t.timestamp < day_end
        )
        daily.append({
            "date": (now - timedelta(days=d)).strftime("%Y-%m-%d"),
            "count": count,
        })

    return {
        "code": code,
        "name": info["name"],
        "total_threats": len(region_threats),
        "by_severity": dict(by_sev),
        "by_category": dict(by_cat),
        "by_framework": dict(by_fw),
        "daily_counts": list(reversed(daily)),
        "alert_level": _region_alert_level(region_threats).value,
        "recent_threats": [t.dict() for t in sorted(region_threats, key=lambda t: t.timestamp, reverse=True)[:10]],
    }


# ---- Alert Zones ---------------------------------------------------------

@app.post("/v1/map/alert-zones", status_code=status.HTTP_201_CREATED)
async def create_alert_zone(data: AlertZoneCreate):
    if data.region.upper() not in REGIONS:
        raise HTTPException(400, f"Invalid region. Valid: {list(REGIONS.keys())}")
    zone = AlertZone(
        name=data.name,
        region=data.region.upper(),
        threshold_count=data.threshold_count,
        threshold_severity=data.threshold_severity,
        window_minutes=data.window_minutes,
    )
    ALERT_ZONES[zone.id] = zone
    return {"id": zone.id, "name": zone.name}


@app.get("/v1/map/alert-zones")
async def list_alert_zones():
    return {
        "count": len(ALERT_ZONES),
        "zones": [z.dict() for z in ALERT_ZONES.values()],
    }


@app.get("/v1/map/alerts")
async def list_alerts(
    level: Optional[AlertLevel] = None,
    limit: int = Query(50, ge=1, le=500),
):
    alerts = TRIGGERED_ALERTS[:]
    if level:
        alerts = [a for a in alerts if a.level == level]
    alerts.sort(key=lambda a: a.timestamp, reverse=True)
    return {"count": len(alerts[:limit]), "alerts": [a.dict() for a in alerts[:limit]]}


# ---- Timeline & Replay ---------------------------------------------------

@app.get("/v1/map/timeline")
async def timeline(
    interval: str = Query("1h", regex="^(1h|6h|1d|7d)$"),
    hours: int = Query(168, ge=1, le=8760),
):
    interval_map = {"1h": 1, "6h": 6, "1d": 24, "7d": 168}
    step = interval_map[interval]
    now = _now()
    buckets: list[dict[str, Any]] = []

    for i in range(0, hours, step):
        bucket_start = (now - timedelta(hours=i + step)).isoformat()
        bucket_end = (now - timedelta(hours=i)).isoformat()
        count = sum(
            1 for t in THREATS.values()
            if bucket_start <= t.timestamp < bucket_end
        )
        sev_counts = Counter(
            t.severity.value
            for t in THREATS.values()
            if bucket_start <= t.timestamp < bucket_end
        )
        buckets.append({
            "start": bucket_start,
            "end": bucket_end,
            "total": count,
            "by_severity": dict(sev_counts),
        })

    return {"interval": interval, "buckets": list(reversed(buckets))}


@app.get("/v1/map/replay")
async def replay(
    at: str = Query(..., description="ISO timestamp to replay map state at"),
    window_hours: int = Query(24, ge=1, le=720),
):
    try:
        target = datetime.fromisoformat(at)
    except ValueError:
        raise HTTPException(400, "Invalid ISO timestamp")

    window_start = (target - timedelta(hours=window_hours)).isoformat()
    target_iso = target.isoformat()

    active = [
        t for t in THREATS.values()
        if window_start <= t.timestamp <= target_iso
    ]

    return {
        "replay_at": target_iso,
        "window_hours": window_hours,
        "threats_visible": len(active),
        "threats": [t.dict() for t in active],
    }


# ---- Analytics -----------------------------------------------------------

@app.get("/v1/map/analytics")
async def global_analytics():
    threats = list(THREATS.values())
    by_sev = Counter(t.severity.value for t in threats)
    by_cat = Counter(t.category for t in threats)
    by_region = Counter(t.source_location.region for t in threats)
    by_fw = Counter(fw for t in threats for fw in t.frameworks)

    # Active flows
    flows = sum(1 for t in threats if t.target_location is not None)

    # Average severity weight
    avg_weight = statistics.mean(
        [_severity_weight(t.severity) for t in threats]
    ) if threats else 0.0

    # Top source cities
    city_counts = Counter(
        t.source_location.city for t in threats if t.source_location.city
    )

    return {
        "total_threats": len(threats),
        "active_threats": sum(1 for t in threats if t.active),
        "attack_flows": flows,
        "by_severity": dict(by_sev),
        "by_category": dict(by_cat),
        "by_region": dict(by_region),
        "by_framework": dict(by_fw),
        "top_source_cities": dict(city_counts.most_common(10)),
        "avg_severity_weight": round(avg_weight, 4),
        "alert_zones": len(ALERT_ZONES),
        "triggered_alerts": len(TRIGGERED_ALERTS),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8702)
