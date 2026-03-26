"""
Universal Defence SDK — Core SDK gateway server.

Single unified interface for agent security across any language,
framework, and deployment model.  Exposes four high-level operations
(scan / protect / report / govern), dispatches to appropriate
back-end services, supports language adapters (Python, TypeScript,
Go, Rust), framework adapters (LangChain, CrewAI, AutoGen,
LlamaIndex, Custom), plugin registry, config profiles, batch
operations, and telemetry aggregation.
"""

from __future__ import annotations

import hashlib
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
    title="NAIL Universal Defence SDK",
    description=(
        "Unified scan / protect / report / govern interface for "
        "agent security — any language, framework, or deployment."
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
# Constants
# ---------------------------------------------------------------------------

AVE_CATEGORIES = [
    "prompt_injection", "tool_misuse", "memory_poisoning", "goal_hijacking",
    "identity_spoofing", "privilege_escalation", "data_exfiltration",
    "resource_exhaustion", "multi_agent_manipulation", "context_overflow",
    "guardrail_bypass", "output_manipulation", "supply_chain_compromise",
    "model_extraction", "reward_hacking", "capability_elicitation",
    "alignment_subversion", "delegation_abuse",
]


class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"


class Framework(str, Enum):
    LANGCHAIN = "langchain"
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    LLAMAINDEX = "llamaindex"
    CUSTOM = "custom"


class Operation(str, Enum):
    SCAN = "scan"
    PROTECT = "protect"
    REPORT = "report"
    GOVERN = "govern"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PluginStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


class ProfileMode(str, Enum):
    CHAT = "chat"
    RAG = "rag"
    MULTI_AGENT = "multi_agent"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Language Adapter Definitions
# ---------------------------------------------------------------------------

LANGUAGE_ADAPTERS: dict[str, dict[str, Any]] = {
    "python": {
        "language": "python",
        "sdk_name": "nail-sdk-python",
        "min_version": "3.9",
        "install": "pip install nail-defence-sdk",
        "import_path": "from nail_sdk import NailDefence",
        "features": ["async_support", "type_hints", "pydantic_models", "streaming"],
        "status": "stable",
    },
    "typescript": {
        "language": "typescript",
        "sdk_name": "nail-sdk-ts",
        "min_version": "5.0",
        "install": "npm install @nail/defence-sdk",
        "import_path": "import { NailDefence } from '@nail/defence-sdk'",
        "features": ["async_await", "type_safety", "streaming", "tree_shaking"],
        "status": "stable",
    },
    "go": {
        "language": "go",
        "sdk_name": "nail-sdk-go",
        "min_version": "1.21",
        "install": "go get github.com/nail-institute/defence-sdk-go",
        "import_path": 'import nail "github.com/nail-institute/defence-sdk-go"',
        "features": ["goroutine_safe", "context_propagation", "streaming"],
        "status": "stable",
    },
    "rust": {
        "language": "rust",
        "sdk_name": "nail-sdk-rust",
        "min_version": "1.70",
        "install": 'cargo add nail-defence-sdk',
        "import_path": "use nail_defence_sdk::NailDefence;",
        "features": ["async_tokio", "zero_copy", "wasm_target", "no_std_optional"],
        "status": "beta",
    },
}

# ---------------------------------------------------------------------------
# Framework Adapter Definitions
# ---------------------------------------------------------------------------

FRAMEWORK_ADAPTERS: dict[str, dict[str, Any]] = {
    "langchain": {
        "framework": "langchain",
        "adapter_name": "nail-langchain",
        "hooks": ["on_llm_start", "on_llm_end", "on_tool_start", "on_tool_end", "on_chain_start"],
        "guard_points": ["input_guard", "output_guard", "tool_guard", "retrieval_guard"],
        "description": "Full LangChain callback + guard integration",
    },
    "crewai": {
        "framework": "crewai",
        "adapter_name": "nail-crewai",
        "hooks": ["on_task_start", "on_task_end", "on_agent_start", "on_delegation"],
        "guard_points": ["task_guard", "delegation_guard", "output_guard"],
        "description": "CrewAI task & delegation security hooks",
    },
    "autogen": {
        "framework": "autogen",
        "adapter_name": "nail-autogen",
        "hooks": ["on_message", "on_code_exec", "on_tool_call", "on_termination"],
        "guard_points": ["message_guard", "code_guard", "tool_guard"],
        "description": "AutoGen conversation & code execution guards",
    },
    "llamaindex": {
        "framework": "llamaindex",
        "adapter_name": "nail-llamaindex",
        "hooks": ["on_query", "on_retrieve", "on_synthesize", "on_tool_call"],
        "guard_points": ["query_guard", "retrieval_guard", "synthesis_guard"],
        "description": "LlamaIndex query & retrieval pipeline guards",
    },
    "custom": {
        "framework": "custom",
        "adapter_name": "nail-custom",
        "hooks": ["before_action", "after_action", "on_error"],
        "guard_points": ["input_guard", "output_guard", "action_guard"],
        "description": "Generic adapter for custom agent frameworks",
    },
}

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ScanFinding(BaseModel):
    id: str = Field(default_factory=lambda: f"FIND-{uuid.uuid4().hex[:8].upper()}")
    category: str
    severity: Severity
    description: str
    vector: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    remediation: str = ""


class ScanRequest(BaseModel):
    content: str
    language: Language = Language.PYTHON
    framework: Framework = Framework.CUSTOM
    categories: list[str] = Field(default_factory=lambda: AVE_CATEGORIES[:])
    profile: ProfileMode = ProfileMode.CHAT


class ScanResult(BaseModel):
    id: str = Field(default_factory=lambda: f"SCAN-{uuid.uuid4().hex[:8].upper()}")
    content_hash: str = ""
    language: str
    framework: str
    profile: str
    findings: list[ScanFinding] = Field(default_factory=list)
    risk_score: float = 0.0
    scanned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProtectRequest(BaseModel):
    content: str
    language: Language = Language.PYTHON
    framework: Framework = Framework.CUSTOM
    mode: str = "block"  # block | sanitise | log_only
    profile: ProfileMode = ProfileMode.CHAT


class ProtectResult(BaseModel):
    id: str = Field(default_factory=lambda: f"PROT-{uuid.uuid4().hex[:8].upper()}")
    original_hash: str = ""
    sanitised_content: str = ""
    blocked: bool = False
    threats_neutralised: int = 0
    mode: str = "block"
    applied_guards: list[str] = Field(default_factory=list)
    protected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReportRequest(BaseModel):
    target_id: str = ""
    scope: str = "full"  # full | summary | category
    categories: list[str] = Field(default_factory=lambda: AVE_CATEGORIES[:])
    format: str = "json"  # json | markdown


class GovernRequest(BaseModel):
    policy_id: str = ""
    action: str = "evaluate"  # evaluate | enforce | audit
    context: dict[str, Any] = Field(default_factory=dict)


class Plugin(BaseModel):
    id: str = Field(default_factory=lambda: f"PLG-{uuid.uuid4().hex[:8].upper()}")
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    operations: list[Operation] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    frameworks: list[Framework] = Field(default_factory=list)
    status: PluginStatus = PluginStatus.ACTIVE
    config: dict[str, Any] = Field(default_factory=dict)
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PluginCreate(BaseModel):
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    operations: list[Operation] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    frameworks: list[Framework] = Field(default_factory=list)


class ConfigProfile(BaseModel):
    id: str = Field(default_factory=lambda: f"PROF-{uuid.uuid4().hex[:8].upper()}")
    name: str
    mode: ProfileMode
    description: str = ""
    scan_categories: list[str] = Field(default_factory=lambda: AVE_CATEGORIES[:])
    protect_mode: str = "block"
    guard_points: list[str] = Field(default_factory=list)
    thresholds: dict[str, float] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BatchItem(BaseModel):
    operation: Operation
    content: str = ""
    language: Language = Language.PYTHON
    framework: Framework = Framework.CUSTOM


class BatchRequest(BaseModel):
    items: list[BatchItem] = Field(default_factory=list)
    profile: ProfileMode = ProfileMode.CHAT


class TelemetryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation: Operation
    language: str
    framework: str
    duration_ms: float = 0.0
    findings_count: int = 0
    risk_score: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → PostgreSQL + Redis + TimescaleDB)
# ---------------------------------------------------------------------------

SCAN_RESULTS: dict[str, ScanResult] = {}
PROTECT_RESULTS: dict[str, ProtectResult] = {}
PLUGINS: dict[str, Plugin] = {}
PROFILES: dict[str, ConfigProfile] = {}
TELEMETRY: list[TelemetryEntry] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


def _record_telemetry(op: Operation, lang: str, fw: str, duration: float, findings: int, risk: float):
    entry = TelemetryEntry(
        operation=op,
        language=lang,
        framework=fw,
        duration_ms=duration,
        findings_count=findings,
        risk_score=risk,
    )
    TELEMETRY.append(entry)
    return entry


def _scan_content(content: str, categories: list[str], profile: ProfileMode) -> list[ScanFinding]:
    """Simulate multi-category content scanning."""
    findings: list[ScanFinding] = []
    content_lower = content.lower()

    # Heuristic detection patterns (demo — production uses ML classifiers)
    patterns: dict[str, list[tuple[str, Severity, str]]] = {
        "prompt_injection": [
            ("ignore previous", Severity.HIGH, "Direct instruction override attempt"),
            ("you are now", Severity.HIGH, "Persona jailbreak attempt"),
            ("repeat after me", Severity.MEDIUM, "Reflection attack"),
            ("system prompt", Severity.MEDIUM, "System prompt extraction attempt"),
        ],
        "tool_misuse": [
            ("os.system", Severity.CRITICAL, "Direct OS command execution"),
            ("subprocess", Severity.HIGH, "Subprocess invocation"),
            ("exec(", Severity.CRITICAL, "Dynamic code execution"),
            ("eval(", Severity.HIGH, "Dynamic expression evaluation"),
        ],
        "data_exfiltration": [
            ("send to", Severity.MEDIUM, "Potential data exfiltration instruction"),
            ("upload", Severity.LOW, "Upload instruction detected"),
            ("webhook", Severity.MEDIUM, "Webhook exfiltration vector"),
        ],
        "memory_poisoning": [
            ("remember that", Severity.MEDIUM, "Memory injection attempt"),
            ("update your knowledge", Severity.HIGH, "Knowledge base manipulation"),
            ("forget everything", Severity.HIGH, "Memory wipe attempt"),
        ],
        "guardrail_bypass": [
            ("hypothetically", Severity.LOW, "Hypothetical framing bypass"),
            ("in a fictional", Severity.LOW, "Fiction framing bypass"),
            ("as a researcher", Severity.MEDIUM, "Authority framing bypass"),
        ],
    }

    for cat in categories:
        if cat not in patterns:
            # Random low-probability finding for categories without patterns
            if random.random() < 0.1:
                findings.append(ScanFinding(
                    category=cat,
                    severity=Severity.LOW,
                    description=f"Heuristic anomaly detected for {cat.replace('_', ' ')}",
                    vector="heuristic",
                    confidence=round(random.uniform(0.3, 0.6), 2),
                    remediation=f"Review content for {cat.replace('_', ' ')} patterns",
                ))
            continue

        for keyword, severity, desc in patterns[cat]:
            if keyword in content_lower:
                # Profile-based severity adjustment
                if profile == ProfileMode.MULTI_AGENT and severity == Severity.MEDIUM:
                    severity = Severity.HIGH  # Stricter in multi-agent

                findings.append(ScanFinding(
                    category=cat,
                    severity=severity,
                    description=desc,
                    vector=keyword,
                    confidence=round(random.uniform(0.7, 0.98), 2),
                    remediation=f"Sanitise or block content matching '{keyword}' pattern",
                ))

    return findings


def _sanitise(content: str, findings: list[ScanFinding]) -> str:
    """Sanitise content based on scan findings."""
    sanitised = content
    for finding in findings:
        if finding.vector and finding.vector in sanitised.lower():
            # Replace with safe marker
            idx = sanitised.lower().find(finding.vector)
            sanitised = sanitised[:idx] + f"[REDACTED:{finding.category}]" + sanitised[idx + len(finding.vector):]
    return sanitised


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    # Seed plugins
    seed_plugins = [
        ("NAIL Core Scanner", "1.0.0", "NAIL Institute", "Core vulnerability scanner across all 18 AVE categories",
         [Operation.SCAN], list(Language), list(Framework)),
        ("PII Detector", "2.1.0", "NAIL Institute", "Detects and redacts PII in agent I/O",
         [Operation.SCAN, Operation.PROTECT], [Language.PYTHON, Language.TYPESCRIPT], list(Framework)),
        ("Prompt Firewall", "1.5.0", "NAIL Institute", "Real-time prompt injection blocking",
         [Operation.PROTECT], list(Language), list(Framework)),
        ("Compliance Reporter", "1.0.0", "NAIL Institute", "Generates compliance reports per jurisdiction",
         [Operation.REPORT, Operation.GOVERN], [Language.PYTHON], [Framework.CUSTOM]),
        ("LangChain Guard", "1.2.0", "NAIL Institute", "Deep LangChain integration with chain-level guards",
         [Operation.SCAN, Operation.PROTECT], [Language.PYTHON, Language.TYPESCRIPT], [Framework.LANGCHAIN]),
        ("CrewAI Monitor", "1.0.0", "NAIL Institute", "CrewAI delegation and task security",
         [Operation.SCAN, Operation.PROTECT], [Language.PYTHON], [Framework.CREWAI]),
    ]

    for name, ver, author, desc, ops, langs, fws in seed_plugins:
        plugin = Plugin(
            name=name, version=ver, author=author, description=desc,
            operations=ops, languages=langs, frameworks=fws,
        )
        PLUGINS[plugin.id] = plugin

    # Seed profiles
    seed_profiles = [
        ("Chat Safety", ProfileMode.CHAT, "Standard chatbot protection profile",
         AVE_CATEGORIES[:], "block",
         ["input_guard", "output_guard"],
         {"risk_threshold": 0.5, "max_tokens": 4096}),
        ("RAG Secure", ProfileMode.RAG, "RAG pipeline protection with retrieval guards",
         AVE_CATEGORIES[:], "sanitise",
         ["input_guard", "retrieval_guard", "synthesis_guard", "output_guard"],
         {"risk_threshold": 0.4, "max_chunks": 20, "similarity_threshold": 0.85}),
        ("Multi-Agent Fortress", ProfileMode.MULTI_AGENT, "Maximum security for multi-agent orchestration",
         AVE_CATEGORIES[:], "block",
         ["input_guard", "output_guard", "delegation_guard", "tool_guard", "message_guard"],
         {"risk_threshold": 0.3, "max_agents": 10, "require_consensus": True}),
    ]

    for name, mode, desc, cats, prot_mode, guards, thresholds in seed_profiles:
        profile = ConfigProfile(
            name=name, mode=mode, description=desc,
            scan_categories=cats, protect_mode=prot_mode,
            guard_points=guards, thresholds=thresholds,
        )
        PROFILES[profile.id] = profile


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "universal-defence-sdk",
        "version": "1.0.0",
        "languages_supported": len(LANGUAGE_ADAPTERS),
        "frameworks_supported": len(FRAMEWORK_ADAPTERS),
        "plugins": len(PLUGINS),
        "profiles": len(PROFILES),
        "scans_completed": len(SCAN_RESULTS),
        "protections_applied": len(PROTECT_RESULTS),
    }


# ---- Scan -----------------------------------------------------------------

@app.post("/v1/scan", status_code=status.HTTP_201_CREATED)
async def scan(req: ScanRequest):
    for cat in req.categories:
        if cat not in AVE_CATEGORIES:
            raise HTTPException(400, f"Invalid AVE category: {cat}")

    findings = _scan_content(req.content, req.categories, req.profile)
    content_hash = hashlib.sha256(req.content.encode()).hexdigest()[:16]

    # Risk score: weighted by severity
    sev_weights = {Severity.INFO: 0.1, Severity.LOW: 0.2, Severity.MEDIUM: 0.5, Severity.HIGH: 0.8, Severity.CRITICAL: 1.0}
    if findings:
        risk = sum(sev_weights.get(f.severity, 0.5) * f.confidence for f in findings) / len(findings)
    else:
        risk = 0.0

    result = ScanResult(
        content_hash=content_hash,
        language=req.language.value,
        framework=req.framework.value,
        profile=req.profile.value,
        findings=findings,
        risk_score=round(risk, 4),
    )
    SCAN_RESULTS[result.id] = result

    _record_telemetry(Operation.SCAN, req.language.value, req.framework.value,
                      round(random.uniform(5, 100), 1), len(findings), result.risk_score)

    return {
        "id": result.id,
        "findings": len(findings),
        "risk_score": result.risk_score,
        "critical": sum(1 for f in findings if f.severity == Severity.CRITICAL),
        "high": sum(1 for f in findings if f.severity == Severity.HIGH),
        "medium": sum(1 for f in findings if f.severity == Severity.MEDIUM),
        "low": sum(1 for f in findings if f.severity == Severity.LOW),
        "details": [f.dict() for f in findings],
    }


# ---- Protect --------------------------------------------------------------

@app.post("/v1/protect", status_code=status.HTTP_201_CREATED)
async def protect(req: ProtectRequest):
    # First scan
    findings = _scan_content(req.content, AVE_CATEGORIES, req.profile)

    blocked = False
    sanitised = req.content
    guards_applied: list[str] = []

    if findings:
        has_critical = any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings)

        if req.mode == "block" and has_critical:
            blocked = True
            sanitised = "[BLOCKED — threat detected]"
            guards_applied.append("block_gate")
        elif req.mode == "sanitise" or (req.mode == "block" and not has_critical):
            sanitised = _sanitise(req.content, findings)
            guards_applied.append("sanitiser")
        else:  # log_only
            guards_applied.append("log_only")

        # Framework-specific guards
        fw_adapter = FRAMEWORK_ADAPTERS.get(req.framework.value, {})
        guards_applied.extend(fw_adapter.get("guard_points", []))

    result = ProtectResult(
        original_hash=hashlib.sha256(req.content.encode()).hexdigest()[:16],
        sanitised_content=sanitised,
        blocked=blocked,
        threats_neutralised=len(findings),
        mode=req.mode,
        applied_guards=guards_applied,
    )
    PROTECT_RESULTS[result.id] = result

    _record_telemetry(Operation.PROTECT, req.language.value, req.framework.value,
                      round(random.uniform(5, 50), 1), len(findings), 0.0)

    return {
        "id": result.id,
        "blocked": blocked,
        "threats_neutralised": len(findings),
        "sanitised_content": sanitised,
        "guards_applied": guards_applied,
    }


# ---- Report ---------------------------------------------------------------

@app.post("/v1/report")
async def report(req: ReportRequest):
    """Generate a security posture report."""
    scans = list(SCAN_RESULTS.values())

    if not scans:
        return {"report": "No scan data available. Run scans first.", "scans": 0}

    # Category breakdown
    cat_findings: dict[str, int] = defaultdict(int)
    sev_breakdown: dict[str, int] = defaultdict(int)
    total_findings = 0

    for scan in scans:
        for finding in scan.findings:
            if req.scope == "category" and finding.category not in req.categories:
                continue
            cat_findings[finding.category] += 1
            sev_breakdown[finding.severity.value] += 1
            total_findings += 1

    avg_risk = round(statistics.mean(s.risk_score for s in scans), 4) if scans else 0.0

    # Top threats
    top_threats = sorted(cat_findings.items(), key=lambda x: x[1], reverse=True)[:5]

    report_data = {
        "report_id": f"RPT-{uuid.uuid4().hex[:8].upper()}",
        "scope": req.scope,
        "generated_at": _now().isoformat(),
        "total_scans": len(scans),
        "total_findings": total_findings,
        "avg_risk_score": avg_risk,
        "by_severity": dict(sev_breakdown),
        "by_category": dict(cat_findings),
        "top_threats": [{"category": c, "count": n} for c, n in top_threats],
        "protections_applied": len(PROTECT_RESULTS),
        "blocked_count": sum(1 for p in PROTECT_RESULTS.values() if p.blocked),
    }

    _record_telemetry(Operation.REPORT, "all", "all", round(random.uniform(10, 200), 1), 0, avg_risk)

    return report_data


# ---- Govern ---------------------------------------------------------------

@app.post("/v1/govern")
async def govern(req: GovernRequest):
    """Evaluate or enforce governance policies."""
    # Check all active plugins with govern capability
    govern_plugins = [p for p in PLUGINS.values() if Operation.GOVERN in p.operations and p.status == PluginStatus.ACTIVE]

    evaluations: list[dict[str, Any]] = []
    overall_compliant = True

    for plugin in govern_plugins:
        # Simulate policy evaluation
        compliant = random.random() > 0.2
        if not compliant:
            overall_compliant = False

        evaluations.append({
            "plugin_id": plugin.id,
            "plugin_name": plugin.name,
            "compliant": compliant,
            "action": req.action,
            "details": f"Policy evaluation by {plugin.name}",
        })

    result = {
        "evaluation_id": f"GOV-{uuid.uuid4().hex[:8].upper()}",
        "action": req.action,
        "overall_compliant": overall_compliant,
        "evaluations": evaluations,
        "policy_id": req.policy_id or "default",
        "evaluated_at": _now().isoformat(),
    }

    _record_telemetry(Operation.GOVERN, "all", "all", round(random.uniform(20, 300), 1), 0, 0.0)

    return result


# ---- Language Adapters -----------------------------------------------------

@app.get("/v1/languages")
async def list_languages():
    return {
        "count": len(LANGUAGE_ADAPTERS),
        "languages": list(LANGUAGE_ADAPTERS.values()),
    }


# ---- Framework Adapters ----------------------------------------------------

@app.get("/v1/frameworks")
async def list_frameworks():
    return {
        "count": len(FRAMEWORK_ADAPTERS),
        "frameworks": list(FRAMEWORK_ADAPTERS.values()),
    }


# ---- Plugins ---------------------------------------------------------------

@app.post("/v1/plugins", status_code=status.HTTP_201_CREATED)
async def register_plugin(data: PluginCreate):
    plugin = Plugin(
        name=data.name,
        version=data.version,
        author=data.author,
        description=data.description,
        operations=data.operations,
        languages=data.languages,
        frameworks=data.frameworks,
    )
    PLUGINS[plugin.id] = plugin
    return {"id": plugin.id, "name": plugin.name, "status": plugin.status.value}


@app.get("/v1/plugins")
async def list_plugins(
    operation: Optional[Operation] = None,
    language: Optional[Language] = None,
    framework: Optional[Framework] = None,
    plugin_status: Optional[PluginStatus] = Query(None, alias="status"),
):
    plugins = list(PLUGINS.values())
    if operation:
        plugins = [p for p in plugins if operation in p.operations]
    if language:
        plugins = [p for p in plugins if language in p.languages]
    if framework:
        plugins = [p for p in plugins if framework in p.frameworks]
    if plugin_status:
        plugins = [p for p in plugins if p.status == plugin_status]
    return {
        "count": len(plugins),
        "plugins": [
            {
                "id": p.id,
                "name": p.name,
                "version": p.version,
                "author": p.author,
                "operations": [o.value for o in p.operations],
                "languages": [l.value for l in p.languages],
                "frameworks": [f.value for f in p.frameworks],
                "status": p.status.value,
            }
            for p in plugins
        ],
    }


@app.get("/v1/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    if plugin_id not in PLUGINS:
        raise HTTPException(404, "Plugin not found")
    return PLUGINS[plugin_id].dict()


# ---- Config Profiles -------------------------------------------------------

@app.get("/v1/profiles")
async def list_profiles():
    return {
        "count": len(PROFILES),
        "profiles": [
            {
                "id": p.id,
                "name": p.name,
                "mode": p.mode.value,
                "description": p.description,
                "guard_points": p.guard_points,
            }
            for p in PROFILES.values()
        ],
    }


@app.get("/v1/profiles/{profile_id}")
async def get_profile(profile_id: str):
    if profile_id not in PROFILES:
        raise HTTPException(404, "Profile not found")
    return PROFILES[profile_id].dict()


# ---- Batch Operations ------------------------------------------------------

@app.post("/v1/batch")
async def batch_operations(req: BatchRequest):
    results: list[dict[str, Any]] = []

    for i, item in enumerate(req.items[:50]):  # Cap at 50
        if item.operation == Operation.SCAN:
            findings = _scan_content(item.content, AVE_CATEGORIES, req.profile)
            results.append({
                "index": i,
                "operation": "scan",
                "findings": len(findings),
                "categories": list({f.category for f in findings}),
            })
        elif item.operation == Operation.PROTECT:
            findings = _scan_content(item.content, AVE_CATEGORIES, req.profile)
            sanitised = _sanitise(item.content, findings) if findings else item.content
            results.append({
                "index": i,
                "operation": "protect",
                "threats_neutralised": len(findings),
                "sanitised": sanitised != item.content,
            })
        elif item.operation == Operation.REPORT:
            results.append({
                "index": i,
                "operation": "report",
                "total_scans": len(SCAN_RESULTS),
            })
        elif item.operation == Operation.GOVERN:
            results.append({
                "index": i,
                "operation": "govern",
                "compliant": random.random() > 0.2,
            })

    return {
        "batch_id": f"BATCH-{uuid.uuid4().hex[:8].upper()}",
        "items_processed": len(results),
        "results": results,
    }


# ---- Telemetry -------------------------------------------------------------

@app.get("/v1/telemetry")
async def telemetry_feed(
    operation: Optional[Operation] = None,
    limit: int = Query(50, ge=1, le=500),
):
    entries = TELEMETRY[:]
    if operation:
        entries = [e for e in entries if e.operation == operation]
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return {"count": len(entries[:limit]), "telemetry": [e.dict() for e in entries[:limit]]}


# ---- Analytics -------------------------------------------------------------

@app.get("/v1/analytics")
async def sdk_analytics():
    scans = list(SCAN_RESULTS.values())
    protections = list(PROTECT_RESULTS.values())
    plugins = list(PLUGINS.values())

    by_language = Counter(s.language for s in scans)
    by_framework = Counter(s.framework for s in scans)
    by_profile = Counter(s.profile for s in scans)

    all_findings: list[ScanFinding] = []
    for s in scans:
        all_findings.extend(s.findings)

    by_category = Counter(f.category for f in all_findings)
    by_severity = Counter(f.severity.value for f in all_findings)

    avg_risk = round(statistics.mean(s.risk_score for s in scans), 4) if scans else 0.0

    # Telemetry aggregates
    by_op = Counter(t.operation.value for t in TELEMETRY)
    avg_duration = round(statistics.mean(t.duration_ms for t in TELEMETRY), 1) if TELEMETRY else 0.0

    return {
        "total_scans": len(scans),
        "total_protections": len(protections),
        "total_findings": len(all_findings),
        "blocked_count": sum(1 for p in protections if p.blocked),
        "avg_risk_score": avg_risk,
        "by_language": dict(by_language),
        "by_framework": dict(by_framework),
        "by_profile": dict(by_profile),
        "by_category": dict(by_category),
        "by_severity": dict(by_severity),
        "total_plugins": len(plugins),
        "active_plugins": sum(1 for p in plugins if p.status == PluginStatus.ACTIVE),
        "telemetry_entries": len(TELEMETRY),
        "by_operation": dict(by_op),
        "avg_duration_ms": avg_duration,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8904)
