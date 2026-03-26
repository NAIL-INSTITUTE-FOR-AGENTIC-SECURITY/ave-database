"""
Cross-Framework Compatibility Layer — Core compatibility server.

Universal defence adapter enabling guardrails to work across LangChain,
CrewAI, AutoGen, LlamaIndex, and custom agent frameworks via an
Abstract Defence Language (ADL).
"""

from __future__ import annotations

import copy
import json
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
    title="NAIL Cross-Framework Compatibility Layer",
    description=(
        "Universal defence adapter with Abstract Defence Language (ADL) "
        "enabling guardrails across LangChain, CrewAI, AutoGen, LlamaIndex."
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

SUPPORTED_FRAMEWORKS = ["langchain", "crewai", "autogen", "llamaindex", "custom"]

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


class HookPoint(str, Enum):
    PRE_INPUT = "pre_input"
    POST_INPUT = "post_input"
    PRE_TOOL = "pre_tool"
    POST_TOOL = "post_tool"
    PRE_OUTPUT = "pre_output"
    POST_OUTPUT = "post_output"
    PRE_CHAIN = "pre_chain"
    POST_CHAIN = "post_chain"
    ERROR = "error"
    PRE_RETRIEVAL = "pre_retrieval"
    POST_RETRIEVAL = "post_retrieval"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    AGENT_INIT = "agent_init"
    AGENT_SHUTDOWN = "agent_shutdown"


class DefenceType(str, Enum):
    INPUT_FILTER = "input_filter"
    OUTPUT_VALIDATOR = "output_validator"
    TOOL_SANDBOX = "tool_sandbox"
    MEMORY_GUARD = "memory_guard"
    RATE_LIMITER = "rate_limiter"
    ROLE_LOCK = "role_lock"
    DLP = "dlp"
    ANOMALY_DETECTOR = "anomaly_detector"
    TRUST_BOUNDARY = "trust_boundary"
    CONTENT_CLASSIFIER = "content_classifier"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLBACK = "rollback"


# ---------------------------------------------------------------------------
# Framework Adapter Definitions
# ---------------------------------------------------------------------------

ADAPTER_REGISTRY: dict[str, dict[str, Any]] = {
    "langchain": {
        "name": "LangChain Adapter",
        "version": "0.2.x",
        "description": "Translates ADL into LangChain callbacks and chain middleware.",
        "hook_points": [
            HookPoint.PRE_INPUT, HookPoint.POST_OUTPUT,
            HookPoint.PRE_TOOL, HookPoint.POST_TOOL,
            HookPoint.PRE_CHAIN, HookPoint.POST_CHAIN,
            HookPoint.ERROR, HookPoint.MEMORY_READ, HookPoint.MEMORY_WRITE,
        ],
        "supported_defence_types": [
            DefenceType.INPUT_FILTER, DefenceType.OUTPUT_VALIDATOR,
            DefenceType.TOOL_SANDBOX, DefenceType.MEMORY_GUARD,
            DefenceType.RATE_LIMITER, DefenceType.DLP,
            DefenceType.ANOMALY_DETECTOR, DefenceType.CONTENT_CLASSIFIER,
        ],
        "config_format": "python_dict",
        "integration_method": "callbacks + chain.middleware",
        "example_import": "from nail_compat import LangChainAdapter",
    },
    "crewai": {
        "name": "CrewAI Adapter",
        "version": "0.30.x",
        "description": "Translates ADL into CrewAI task/agent lifecycle hooks.",
        "hook_points": [
            HookPoint.PRE_INPUT, HookPoint.POST_OUTPUT,
            HookPoint.PRE_TOOL, HookPoint.POST_TOOL,
            HookPoint.AGENT_INIT, HookPoint.AGENT_SHUTDOWN,
            HookPoint.ERROR,
        ],
        "supported_defence_types": [
            DefenceType.INPUT_FILTER, DefenceType.OUTPUT_VALIDATOR,
            DefenceType.TOOL_SANDBOX, DefenceType.ROLE_LOCK,
            DefenceType.RATE_LIMITER, DefenceType.TRUST_BOUNDARY,
        ],
        "config_format": "python_dict",
        "integration_method": "task.pre_hook + agent.before_execution",
        "example_import": "from nail_compat import CrewAIAdapter",
    },
    "autogen": {
        "name": "AutoGen Adapter",
        "version": "0.2.x",
        "description": "Translates ADL into AutoGen message filters and reply hooks.",
        "hook_points": [
            HookPoint.PRE_INPUT, HookPoint.POST_OUTPUT,
            HookPoint.PRE_TOOL, HookPoint.POST_TOOL,
            HookPoint.ERROR, HookPoint.MEMORY_READ,
        ],
        "supported_defence_types": [
            DefenceType.INPUT_FILTER, DefenceType.OUTPUT_VALIDATOR,
            DefenceType.TOOL_SANDBOX, DefenceType.MEMORY_GUARD,
            DefenceType.RATE_LIMITER, DefenceType.DLP,
            DefenceType.ANOMALY_DETECTOR,
        ],
        "config_format": "python_dict",
        "integration_method": "register_reply + message_filter",
        "example_import": "from nail_compat import AutoGenAdapter",
    },
    "llamaindex": {
        "name": "LlamaIndex Adapter",
        "version": "0.10.x",
        "description": "Translates ADL into LlamaIndex query/retrieval/synthesis hooks.",
        "hook_points": [
            HookPoint.PRE_INPUT, HookPoint.POST_OUTPUT,
            HookPoint.PRE_RETRIEVAL, HookPoint.POST_RETRIEVAL,
            HookPoint.PRE_TOOL, HookPoint.POST_TOOL,
            HookPoint.ERROR,
        ],
        "supported_defence_types": [
            DefenceType.INPUT_FILTER, DefenceType.OUTPUT_VALIDATOR,
            DefenceType.MEMORY_GUARD, DefenceType.DLP,
            DefenceType.CONTENT_CLASSIFIER, DefenceType.RATE_LIMITER,
        ],
        "config_format": "python_dict",
        "integration_method": "callback_manager + query_transform",
        "example_import": "from nail_compat import LlamaIndexAdapter",
    },
    "custom": {
        "name": "Custom Framework Adapter",
        "version": "1.0.0",
        "description": "User-defined hook points via ADL schema for any framework.",
        "hook_points": list(HookPoint),
        "supported_defence_types": list(DefenceType),
        "config_format": "json",
        "integration_method": "user_defined",
        "example_import": "from nail_compat import CustomAdapter",
    },
}

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ADLDefence(BaseModel):
    """Abstract Defence Language definition — framework-agnostic."""
    id: str = Field(default_factory=lambda: f"DEF-{uuid.uuid4().hex[:8].upper()}")
    name: str
    defence_type: DefenceType
    description: str = ""
    hook_points: list[HookPoint]
    ave_categories: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    severity_threshold: str = "medium"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ADLDefenceCreate(BaseModel):
    name: str
    defence_type: DefenceType
    description: str = ""
    hook_points: list[HookPoint]
    ave_categories: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    severity_threshold: str = "medium"


class DefenceProfile(BaseModel):
    id: str = Field(default_factory=lambda: f"PROF-{uuid.uuid4().hex[:8].upper()}")
    name: str
    description: str = ""
    defence_ids: list[str] = Field(default_factory=list)
    target_frameworks: list[str] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ProfileCreate(BaseModel):
    name: str
    description: str = ""
    defence_ids: list[str] = Field(default_factory=list)
    target_frameworks: list[str] = Field(default_factory=list)


class DeployRequest(BaseModel):
    framework: str
    dry_run: bool = False


class TranslationResult(BaseModel):
    defence_id: str
    target_framework: str
    native_config: dict[str, Any]
    hook_mappings: list[dict[str, str]]
    warnings: list[str]
    compatible: bool


class DeployResult(BaseModel):
    profile_id: str
    framework: str
    status: DeploymentStatus
    deployed_defences: list[str]
    skipped_defences: list[str]
    warnings: list[str]
    native_config: dict[str, Any]
    timestamp: str


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    compatible_frameworks: list[str]
    incompatible_frameworks: list[str]


class TelemetryEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework: str
    defence_id: str
    hook_point: str
    action: str  # allow / block / warn / log
    latency_ms: float
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → PostgreSQL + Redis)
# ---------------------------------------------------------------------------

DEFENCES: dict[str, ADLDefence] = {}
PROFILES: dict[str, DefenceProfile] = {}
DEPLOYMENTS: list[DeployResult] = []
TELEMETRY: list[TelemetryEvent] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


# Hook-point mapping per framework
HOOK_MAP: dict[str, dict[HookPoint, str]] = {
    "langchain": {
        HookPoint.PRE_INPUT: "on_chain_start",
        HookPoint.POST_OUTPUT: "on_chain_end",
        HookPoint.PRE_TOOL: "on_tool_start",
        HookPoint.POST_TOOL: "on_tool_end",
        HookPoint.PRE_CHAIN: "on_chain_start",
        HookPoint.POST_CHAIN: "on_chain_end",
        HookPoint.ERROR: "on_chain_error",
        HookPoint.MEMORY_READ: "on_chat_model_start",
        HookPoint.MEMORY_WRITE: "on_chain_end",
    },
    "crewai": {
        HookPoint.PRE_INPUT: "task.before_execution",
        HookPoint.POST_OUTPUT: "task.after_execution",
        HookPoint.PRE_TOOL: "tool.before_call",
        HookPoint.POST_TOOL: "tool.after_call",
        HookPoint.AGENT_INIT: "agent.on_init",
        HookPoint.AGENT_SHUTDOWN: "agent.on_shutdown",
        HookPoint.ERROR: "task.on_error",
    },
    "autogen": {
        HookPoint.PRE_INPUT: "register_reply.before",
        HookPoint.POST_OUTPUT: "register_reply.after",
        HookPoint.PRE_TOOL: "function_map.before",
        HookPoint.POST_TOOL: "function_map.after",
        HookPoint.ERROR: "on_error",
        HookPoint.MEMORY_READ: "message_filter.read",
    },
    "llamaindex": {
        HookPoint.PRE_INPUT: "on_query_start",
        HookPoint.POST_OUTPUT: "on_query_end",
        HookPoint.PRE_RETRIEVAL: "on_retrieval_start",
        HookPoint.POST_RETRIEVAL: "on_retrieval_end",
        HookPoint.PRE_TOOL: "on_tool_start",
        HookPoint.POST_TOOL: "on_tool_end",
        HookPoint.ERROR: "on_event_error",
    },
    "custom": {hp: hp.value for hp in HookPoint},
}


def _translate_defence(defence: ADLDefence, framework: str) -> TranslationResult:
    """Translate an ADL defence into framework-native configuration."""
    adapter = ADAPTER_REGISTRY.get(framework)
    if not adapter:
        return TranslationResult(
            defence_id=defence.id,
            target_framework=framework,
            native_config={},
            hook_mappings=[],
            warnings=[f"Unknown framework: {framework}"],
            compatible=False,
        )

    # Check defence type support
    supported_types = adapter["supported_defence_types"]
    if defence.defence_type not in supported_types:
        return TranslationResult(
            defence_id=defence.id,
            target_framework=framework,
            native_config={},
            hook_mappings=[],
            warnings=[f"Defence type '{defence.defence_type.value}' not supported by {framework}"],
            compatible=False,
        )

    # Map hook points
    fw_hooks = HOOK_MAP.get(framework, {})
    adapter_hooks = adapter["hook_points"]
    hook_mappings: list[dict[str, str]] = []
    warnings: list[str] = []

    for hp in defence.hook_points:
        if hp in adapter_hooks:
            native = fw_hooks.get(hp, hp.value)
            hook_mappings.append({"adl": hp.value, "native": native})
        else:
            warnings.append(f"Hook point '{hp.value}' not available in {framework} — skipped")

    if not hook_mappings:
        return TranslationResult(
            defence_id=defence.id,
            target_framework=framework,
            native_config={},
            hook_mappings=[],
            warnings=warnings + ["No compatible hook points found"],
            compatible=False,
        )

    # Build native config
    native_config: dict[str, Any] = {
        "nail_defence_id": defence.id,
        "defence_type": defence.defence_type.value,
        "name": defence.name,
        "enabled": defence.enabled,
        "severity_threshold": defence.severity_threshold,
        "framework": framework,
        "integration_method": adapter["integration_method"],
        "hooks": {m["native"]: m["adl"] for m in hook_mappings},
        "config": defence.config,
    }

    # Framework-specific additions
    if framework == "langchain":
        native_config["callback_class"] = f"NAIL{defence.defence_type.value.title().replace('_','')}Callback"
        native_config["import"] = adapter["example_import"]
    elif framework == "crewai":
        native_config["task_hook_class"] = f"NAIL{defence.defence_type.value.title().replace('_','')}Hook"
        native_config["import"] = adapter["example_import"]
    elif framework == "autogen":
        native_config["reply_func_name"] = f"nail_{defence.defence_type.value}_filter"
        native_config["import"] = adapter["example_import"]
    elif framework == "llamaindex":
        native_config["event_handler_class"] = f"NAIL{defence.defence_type.value.title().replace('_','')}Handler"
        native_config["import"] = adapter["example_import"]

    return TranslationResult(
        defence_id=defence.id,
        target_framework=framework,
        native_config=native_config,
        hook_mappings=hook_mappings,
        warnings=warnings,
        compatible=True,
    )


def _validate_adl(defence: ADLDefenceCreate) -> ValidationResult:
    """Validate an ADL definition against all frameworks."""
    errors: list[str] = []
    warnings: list[str] = []
    compatible: list[str] = []
    incompatible: list[str] = []

    if not defence.name.strip():
        errors.append("Defence name is required")
    if not defence.hook_points:
        errors.append("At least one hook point is required")
    for cat in defence.ave_categories:
        if cat not in AVE_CATEGORIES:
            errors.append(f"Unknown AVE category: {cat}")

    for fw, adapter in ADAPTER_REGISTRY.items():
        if defence.defence_type not in adapter["supported_defence_types"]:
            incompatible.append(fw)
            continue
        matched_hooks = [hp for hp in defence.hook_points if hp in adapter["hook_points"]]
        if matched_hooks:
            compatible.append(fw)
        else:
            incompatible.append(fw)
            warnings.append(f"No matching hook points for {fw}")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        compatible_frameworks=compatible,
        incompatible_frameworks=incompatible,
    )


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    defences_data = [
        (
            "Prompt Injection Filter",
            DefenceType.INPUT_FILTER,
            "Detects and blocks prompt injection attempts across frameworks.",
            [HookPoint.PRE_INPUT, HookPoint.POST_INPUT],
            ["prompt_injection", "guardrail_bypass"],
            {"patterns": ["ignore previous", "system prompt", "jailbreak"], "mode": "block"},
        ),
        (
            "Output Toxicity Validator",
            DefenceType.OUTPUT_VALIDATOR,
            "Validates agent output for harmful, toxic, or policy-violating content.",
            [HookPoint.PRE_OUTPUT, HookPoint.POST_OUTPUT],
            ["output_manipulation", "alignment_subversion"],
            {"threshold": 0.7, "categories": ["harmful", "toxic", "pii"]},
        ),
        (
            "Tool Execution Sandbox",
            DefenceType.TOOL_SANDBOX,
            "Restricts tool access to whitelisted functions and rate-limits execution.",
            [HookPoint.PRE_TOOL, HookPoint.POST_TOOL],
            ["tool_misuse", "privilege_escalation"],
            {"whitelist": ["search", "calculator", "read_file"], "max_calls_per_minute": 10},
        ),
        (
            "Memory Integrity Guard",
            DefenceType.MEMORY_GUARD,
            "Validates memory reads/writes for poisoning and injection.",
            [HookPoint.MEMORY_READ, HookPoint.MEMORY_WRITE],
            ["memory_poisoning", "context_overflow"],
            {"max_memory_size_kb": 512, "scan_for_injection": True},
        ),
        (
            "API Rate Limiter",
            DefenceType.RATE_LIMITER,
            "Global rate limiter for agent API calls.",
            [HookPoint.PRE_INPUT],
            ["resource_exhaustion"],
            {"requests_per_minute": 60, "burst": 10},
        ),
        (
            "Data Loss Prevention",
            DefenceType.DLP,
            "Prevents sensitive data from being emitted by agents.",
            [HookPoint.POST_OUTPUT, HookPoint.POST_TOOL],
            ["data_exfiltration"],
            {"scan_patterns": ["ssn", "credit_card", "api_key", "password"], "action": "redact"},
        ),
    ]

    for name, dtype, desc, hooks, cats, cfg in defences_data:
        d = ADLDefence(
            name=name,
            defence_type=dtype,
            description=desc,
            hook_points=hooks,
            ave_categories=cats,
            config=cfg,
        )
        DEFENCES[d.id] = d

    # Default profile
    profile = DefenceProfile(
        name="Standard Agent Security Profile",
        description="Balanced defence profile covering common AVE categories.",
        defence_ids=list(DEFENCES.keys()),
        target_frameworks=["langchain", "crewai", "autogen", "llamaindex"],
    )
    PROFILES[profile.id] = profile

    # Generate some telemetry
    import random

    fws = SUPPORTED_FRAMEWORKS[:4]
    actions = ["allow", "allow", "allow", "block", "warn", "log"]
    for _ in range(50):
        d = random.choice(list(DEFENCES.values()))
        te = TelemetryEvent(
            framework=random.choice(fws),
            defence_id=d.id,
            hook_point=random.choice(d.hook_points).value,
            action=random.choice(actions),
            latency_ms=round(random.uniform(0.5, 25.0), 2),
            timestamp=(_now() - timedelta(hours=random.randint(0, 168))).isoformat(),
        )
        TELEMETRY.append(te)


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "cross-framework-compatibility-layer",
        "version": "1.0.0",
        "defences": len(DEFENCES),
        "profiles": len(PROFILES),
        "frameworks": len(SUPPORTED_FRAMEWORKS),
    }


# ---- Adapters ------------------------------------------------------------

@app.get("/v1/adapters")
async def list_adapters():
    return {
        "count": len(ADAPTER_REGISTRY),
        "adapters": {
            fw: {
                "name": a["name"],
                "version": a["version"],
                "description": a["description"],
                "hook_points": [hp.value for hp in a["hook_points"]],
                "supported_defence_types": [dt.value for dt in a["supported_defence_types"]],
                "integration_method": a["integration_method"],
            }
            for fw, a in ADAPTER_REGISTRY.items()
        },
    }


@app.get("/v1/adapters/{framework}")
async def get_adapter(framework: str):
    fw = framework.lower()
    if fw not in ADAPTER_REGISTRY:
        raise HTTPException(404, f"Framework not found. Supported: {SUPPORTED_FRAMEWORKS}")
    a = ADAPTER_REGISTRY[fw]
    return {
        "framework": fw,
        "name": a["name"],
        "version": a["version"],
        "description": a["description"],
        "hook_points": [hp.value for hp in a["hook_points"]],
        "supported_defence_types": [dt.value for dt in a["supported_defence_types"]],
        "config_format": a["config_format"],
        "integration_method": a["integration_method"],
        "example_import": a["example_import"],
    }


# ---- Defences (ADL) -----------------------------------------------------

@app.post("/v1/defences", status_code=status.HTTP_201_CREATED)
async def create_defence(data: ADLDefenceCreate):
    validation = _validate_adl(data)
    if not validation.valid:
        raise HTTPException(400, {"errors": validation.errors})

    d = ADLDefence(
        name=data.name,
        defence_type=data.defence_type,
        description=data.description,
        hook_points=data.hook_points,
        ave_categories=data.ave_categories,
        config=data.config,
        severity_threshold=data.severity_threshold,
    )
    DEFENCES[d.id] = d
    return {
        "id": d.id,
        "compatible_frameworks": validation.compatible_frameworks,
        "warnings": validation.warnings,
    }


@app.get("/v1/defences")
async def list_defences(
    defence_type: Optional[DefenceType] = None,
    framework: Optional[str] = None,
):
    defs = list(DEFENCES.values())
    if defence_type:
        defs = [d for d in defs if d.defence_type == defence_type]
    if framework:
        fw = framework.lower()
        adapter = ADAPTER_REGISTRY.get(fw)
        if adapter:
            defs = [
                d for d in defs
                if d.defence_type in adapter["supported_defence_types"]
            ]
    return {"count": len(defs), "defences": [d.dict() for d in defs]}


@app.get("/v1/defences/{def_id}")
async def get_defence(def_id: str):
    if def_id not in DEFENCES:
        raise HTTPException(404, "Defence not found")
    return DEFENCES[def_id].dict()


@app.post("/v1/defences/{def_id}/translate")
async def translate_defence(def_id: str, framework: str = Query(...)):
    if def_id not in DEFENCES:
        raise HTTPException(404, "Defence not found")
    fw = framework.lower()
    if fw not in ADAPTER_REGISTRY:
        raise HTTPException(400, f"Unknown framework. Supported: {SUPPORTED_FRAMEWORKS}")

    result = _translate_defence(DEFENCES[def_id], fw)
    return result


# ---- Profiles ------------------------------------------------------------

@app.post("/v1/profiles", status_code=status.HTTP_201_CREATED)
async def create_profile(data: ProfileCreate):
    for did in data.defence_ids:
        if did not in DEFENCES:
            raise HTTPException(404, f"Defence {did} not found")
    for fw in data.target_frameworks:
        if fw.lower() not in ADAPTER_REGISTRY:
            raise HTTPException(400, f"Unknown framework: {fw}")

    profile = DefenceProfile(
        name=data.name,
        description=data.description,
        defence_ids=data.defence_ids,
        target_frameworks=[f.lower() for f in data.target_frameworks],
    )
    PROFILES[profile.id] = profile
    return {"id": profile.id, "name": profile.name}


@app.get("/v1/profiles")
async def list_profiles():
    return {
        "count": len(PROFILES),
        "profiles": [p.dict() for p in PROFILES.values()],
    }


@app.get("/v1/profiles/{prof_id}")
async def get_profile(prof_id: str):
    if prof_id not in PROFILES:
        raise HTTPException(404, "Profile not found")
    return PROFILES[prof_id].dict()


@app.post("/v1/profiles/{prof_id}/deploy")
async def deploy_profile(prof_id: str, req: DeployRequest):
    if prof_id not in PROFILES:
        raise HTTPException(404, "Profile not found")
    fw = req.framework.lower()
    if fw not in ADAPTER_REGISTRY:
        raise HTTPException(400, f"Unknown framework: {fw}")

    profile = PROFILES[prof_id]
    deployed: list[str] = []
    skipped: list[str] = []
    warnings: list[str] = []
    combined_config: dict[str, Any] = {
        "framework": fw,
        "profile_id": prof_id,
        "defences": [],
    }

    for did in profile.defence_ids:
        if did not in DEFENCES:
            skipped.append(did)
            warnings.append(f"Defence {did} not found — skipped")
            continue
        result = _translate_defence(DEFENCES[did], fw)
        if result.compatible:
            deployed.append(did)
            combined_config["defences"].append(result.native_config)
        else:
            skipped.append(did)
            warnings.extend(result.warnings)

    deploy_status = DeploymentStatus.DEPLOYED if deployed else DeploymentStatus.FAILED

    deploy_result = DeployResult(
        profile_id=prof_id,
        framework=fw,
        status=deploy_status,
        deployed_defences=deployed,
        skipped_defences=skipped,
        warnings=warnings,
        native_config=combined_config if not req.dry_run else {},
        timestamp=_now().isoformat(),
    )

    if not req.dry_run:
        DEPLOYMENTS.append(deploy_result)

    return deploy_result


# ---- Hooks ---------------------------------------------------------------

@app.get("/v1/hooks/{framework}")
async def list_hooks(framework: str):
    fw = framework.lower()
    if fw not in ADAPTER_REGISTRY:
        raise HTTPException(404, f"Framework not found. Supported: {SUPPORTED_FRAMEWORKS}")

    adapter = ADAPTER_REGISTRY[fw]
    fw_hook_map = HOOK_MAP.get(fw, {})

    hooks: list[dict[str, str]] = []
    for hp in adapter["hook_points"]:
        hooks.append({
            "adl_hook": hp.value,
            "native_hook": fw_hook_map.get(hp, hp.value),
        })

    return {"framework": fw, "hook_count": len(hooks), "hooks": hooks}


# ---- Validation ----------------------------------------------------------

@app.post("/v1/validate")
async def validate_defence(data: ADLDefenceCreate):
    return _validate_adl(data)


# ---- Telemetry -----------------------------------------------------------

@app.get("/v1/telemetry")
async def aggregated_telemetry(
    framework: Optional[str] = None,
    hours: int = Query(24, ge=1, le=720),
):
    cutoff = (_now() - timedelta(hours=hours)).isoformat()
    events = [e for e in TELEMETRY if e.timestamp >= cutoff]
    if framework:
        events = [e for e in events if e.framework == framework.lower()]

    by_fw = Counter(e.framework for e in events)
    by_action = Counter(e.action for e in events)
    by_defence = Counter(e.defence_id for e in events)

    latencies = [e.latency_ms for e in events]
    avg_latency = round(statistics.mean(latencies), 2) if latencies else 0.0
    p95_latency = round(
        sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0, 2
    )

    block_rate = by_action.get("block", 0) / len(events) if events else 0.0

    return {
        "window_hours": hours,
        "total_events": len(events),
        "by_framework": dict(by_fw),
        "by_action": dict(by_action),
        "by_defence": dict(by_defence),
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "block_rate": round(block_rate, 4),
    }


# ---- Compatibility Matrix ------------------------------------------------

@app.get("/v1/compatibility-matrix")
async def compatibility_matrix():
    matrix: dict[str, dict[str, Any]] = {}
    for fw, adapter in ADAPTER_REGISTRY.items():
        row: dict[str, Any] = {}
        for dtype in DefenceType:
            supported = dtype in adapter["supported_defence_types"]
            row[dtype.value] = {
                "supported": supported,
                "hook_count": (
                    len([hp for hp in adapter["hook_points"]])
                    if supported else 0
                ),
            }
        matrix[fw] = row

    return {
        "frameworks": list(ADAPTER_REGISTRY.keys()),
        "defence_types": [dt.value for dt in DefenceType],
        "matrix": matrix,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8703)
