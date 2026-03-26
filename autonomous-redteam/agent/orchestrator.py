"""
ARTA Orchestrator — LangGraph-based campaign coordinator.

Manages the autonomous red team agent lifecycle: plan → recon → exploit →
validate → report.  Built on LangGraph for stateful, human-in-the-loop
workflows with full audit logging.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class CampaignType(str, Enum):
    FRAMEWORK_AUDIT = "framework_audit"
    CATEGORY_SWEEP = "category_sweep"
    MULTI_AGENT = "multi_agent"
    REGRESSION = "regression"
    CONTINUOUS_MONITORING = "continuous_monitoring"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, Enum):
    RAW = "raw"
    VALIDATED = "validated"
    FALSE_POSITIVE = "false_positive"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"


class AgentTarget(BaseModel):
    """Describes an authorized target agent/system."""

    name: str
    framework: str
    version: str
    endpoint: str
    authorized: bool = True
    scope: dict[str, Any] = Field(default_factory=dict)


class AttackSurface(BaseModel):
    """Result of reconnaissance — catalogues the target's exposure."""

    target: str
    tools: list[dict[str, Any]] = Field(default_factory=list)
    trust_boundaries: list[dict[str, Any]] = Field(default_factory=list)
    guardrails: list[dict[str, Any]] = Field(default_factory=list)
    model: str = ""
    topology: str = "single_agent"
    observations: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    """A single raw vulnerability finding."""

    finding_id: str = Field(default_factory=lambda: f"finding-{uuid.uuid4().hex[:8]}")
    category: str
    technique: str
    description: str
    severity: Severity = Severity.INFO
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    payload: str = ""
    response: str = ""
    status: FindingStatus = FindingStatus.RAW
    reproductions: int = 0
    cross_model_verified: bool = False
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CampaignState(BaseModel):
    """Full state object flowing through the LangGraph pipeline."""

    campaign_id: str = Field(
        default_factory=lambda: f"camp_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    )
    campaign_type: CampaignType = CampaignType.FRAMEWORK_AUDIT
    target: AgentTarget
    categories: list[str] = Field(default_factory=list)
    depth: str = "comprehensive"

    # Populated during execution
    attack_surface: Optional[AttackSurface] = None
    raw_findings: list[Finding] = Field(default_factory=list)
    validated_findings: list[Finding] = Field(default_factory=list)
    false_positives: list[Finding] = Field(default_factory=list)
    ave_cards: list[dict[str, Any]] = Field(default_factory=list)

    # Metadata
    started: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed: Optional[str] = None
    probes_executed: int = 0
    guardrail_violations: int = 0
    human_approvals_requested: int = 0
    audit_log: list[dict[str, Any]] = Field(default_factory=list)

    # Control
    halted: bool = False
    halt_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Logging & audit
# ---------------------------------------------------------------------------

logger = logging.getLogger("arta.orchestrator")


def _audit(state: CampaignState, action: str, detail: str = "") -> CampaignState:
    """Append an audit entry to the campaign state."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "detail": detail,
        "campaign_id": state.campaign_id,
    }
    state.audit_log.append(entry)
    logger.info("[AUDIT] %s — %s", action, detail)
    return state


# ---------------------------------------------------------------------------
# Safety guardrails
# ---------------------------------------------------------------------------

ALL_AVE_CATEGORIES = [
    "prompt_injection",
    "tool_abuse",
    "memory_poisoning",
    "identity_spoofing",
    "goal_hijacking",
    "knowledge_poisoning",
    "resource_exhaustion",
    "output_manipulation",
    "privilege_escalation",
    "trust_exploitation",
    "context_overflow",
    "model_denial_of_service",
    "data_exfiltration",
    "supply_chain",
    "model_poisoning",
    "multi_agent_coordination",
    "reward_hacking",
    "emergent_behavior",
]


class SafetyGuardrails:
    """Enforce ethical and operational safety constraints."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.kill_switch = self.config.get("kill_switch_enabled", True)
        self.max_severity = Severity(
            self.config.get("max_finding_severity", "critical")
        )
        self.human_approval_threshold = Severity(
            self.config.get("require_human_approval_above", "high")
        )

    def check_target_authorized(self, target: AgentTarget) -> bool:
        if not target.authorized:
            raise PermissionError(f"Target {target.name!r} is NOT authorized.")
        return True

    def check_scope(self, target: AgentTarget, category: str) -> bool:
        scope_cats = target.scope.get("categories", "all")
        if scope_cats != "all" and category not in scope_cats:
            raise PermissionError(
                f"Category {category!r} not in scope for {target.name!r}."
            )
        return True

    def check_rate_limit(self, target: AgentTarget, current_rate: float) -> bool:
        max_rate = target.scope.get("max_probe_rate", 10)
        if current_rate > max_rate:
            raise RuntimeError(
                f"Rate {current_rate}/min exceeds limit {max_rate}/min for {target.name!r}."
            )
        return True

    def requires_human_approval(self, severity: Severity) -> bool:
        order = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return order.index(severity) > order.index(self.human_approval_threshold)

    def trigger_kill_switch(self, state: CampaignState, reason: str) -> CampaignState:
        logger.critical("[KILL SWITCH] %s", reason)
        state.halted = True
        state.halt_reason = reason
        state.guardrail_violations += 1
        return _audit(state, "KILL_SWITCH", reason)


# ---------------------------------------------------------------------------
# LangGraph node functions
# ---------------------------------------------------------------------------
# Each node takes CampaignState → CampaignState.
# In a full implementation these would call LLM chains; here we define the
# structure and contracts.


async def plan_campaign(state: CampaignState) -> CampaignState:
    """Plan the campaign based on type, target, and scope."""
    state = _audit(state, "PLAN_START", f"type={state.campaign_type.value}")

    # Determine categories to test
    if not state.categories:
        if state.campaign_type == CampaignType.FRAMEWORK_AUDIT:
            state.categories = list(ALL_AVE_CATEGORIES)
        elif state.campaign_type == CampaignType.CATEGORY_SWEEP:
            state.categories = state.categories or ["prompt_injection"]
        elif state.campaign_type == CampaignType.MULTI_AGENT:
            state.categories = [
                "trust_exploitation",
                "multi_agent_coordination",
                "goal_hijacking",
                "identity_spoofing",
                "emergent_behavior",
            ]
        elif state.campaign_type == CampaignType.REGRESSION:
            state.categories = list(ALL_AVE_CATEGORIES)
        else:
            state.categories = list(ALL_AVE_CATEGORIES)

    state = _audit(
        state,
        "PLAN_COMPLETE",
        f"categories={len(state.categories)}, depth={state.depth}",
    )
    return state


async def run_reconnaissance(state: CampaignState) -> CampaignState:
    """Execute reconnaissance against the target."""
    if state.halted:
        return state

    state = _audit(state, "RECON_START", f"target={state.target.name}")

    # In production, this invokes ReconModule LLM chains
    state.attack_surface = AttackSurface(
        target=state.target.name,
        model="unknown",
        topology="single_agent",
        observations=["Recon module would probe target here"],
    )

    state = _audit(state, "RECON_COMPLETE", "Attack surface mapped")
    return state


async def run_exploitation(state: CampaignState) -> CampaignState:
    """Execute exploitation probes across all in-scope categories."""
    if state.halted:
        return state

    state = _audit(
        state,
        "EXPLOIT_START",
        f"categories={len(state.categories)}",
    )

    guardrails = SafetyGuardrails()
    guardrails.check_target_authorized(state.target)

    for category in state.categories:
        if state.halted:
            break

        guardrails.check_scope(state.target, category)
        state = _audit(state, "EXPLOIT_CATEGORY", category)

        # In production, this calls ExploitationEngine per category
        state.probes_executed += 1  # placeholder

    state = _audit(
        state,
        "EXPLOIT_COMPLETE",
        f"probes={state.probes_executed}, raw_findings={len(state.raw_findings)}",
    )
    return state


async def run_validation(state: CampaignState) -> CampaignState:
    """Validate raw findings to eliminate false positives."""
    if state.halted:
        return state

    state = _audit(state, "VALIDATE_START", f"raw_findings={len(state.raw_findings)}")

    for finding in state.raw_findings:
        # In production: ValidationModule.reproduce(), cross_model_verify()
        if finding.reproductions >= 3:
            finding.status = FindingStatus.VALIDATED
            state.validated_findings.append(finding)
        else:
            finding.status = FindingStatus.FALSE_POSITIVE
            state.false_positives.append(finding)

    state = _audit(
        state,
        "VALIDATE_COMPLETE",
        f"validated={len(state.validated_findings)}, "
        f"false_positives={len(state.false_positives)}",
    )
    return state


async def generate_ave_cards(state: CampaignState) -> CampaignState:
    """Generate AVE cards for all validated findings."""
    if state.halted:
        return state

    state = _audit(
        state,
        "CARD_GEN_START",
        f"validated_findings={len(state.validated_findings)}",
    )

    for finding in state.validated_findings:
        card = {
            "ave_id": f"AVE-DRAFT-{uuid.uuid4().hex[:4].upper()}",
            "schema_version": "2.0.0",
            "title": finding.description[:120],
            "category": finding.category,
            "severity": finding.severity.value,
            "status": "draft",
            "finding_id": finding.finding_id,
            "evidence_count": len(finding.evidence),
            "generated_by": "ARTA",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        state.ave_cards.append(card)

    state = _audit(
        state,
        "CARD_GEN_COMPLETE",
        f"ave_cards={len(state.ave_cards)}",
    )
    return state


async def finalize_campaign(state: CampaignState) -> CampaignState:
    """Finalize campaign — write summary and audit log."""
    state.completed = datetime.now(timezone.utc).isoformat()
    state = _audit(state, "CAMPAIGN_COMPLETE", f"id={state.campaign_id}")
    return state


# ---------------------------------------------------------------------------
# Campaign runner
# ---------------------------------------------------------------------------


async def run_campaign(
    target: AgentTarget,
    campaign_type: CampaignType = CampaignType.FRAMEWORK_AUDIT,
    categories: list[str] | None = None,
    depth: str = "comprehensive",
    output_dir: str = "./findings",
) -> CampaignState:
    """Run a full ARTA campaign end-to-end."""

    state = CampaignState(
        campaign_type=campaign_type,
        target=target,
        categories=categories or [],
        depth=depth,
    )

    pipeline = [
        plan_campaign,
        run_reconnaissance,
        run_exploitation,
        run_validation,
        generate_ave_cards,
        finalize_campaign,
    ]

    for step in pipeline:
        if state.halted:
            logger.warning("Campaign halted: %s", state.halt_reason)
            break
        state = await step(state)

    # Persist results
    out = Path(output_dir) / state.campaign_id
    out.mkdir(parents=True, exist_ok=True)

    summary = {
        "campaign_id": state.campaign_id,
        "type": state.campaign_type.value,
        "target": state.target.name,
        "started": state.started,
        "completed": state.completed,
        "categories_tested": len(state.categories),
        "probes_executed": state.probes_executed,
        "findings_raw": len(state.raw_findings),
        "findings_validated": len(state.validated_findings),
        "findings_false_positive": len(state.false_positives),
        "ave_cards_generated": len(state.ave_cards),
        "guardrail_violations": state.guardrail_violations,
        "halted": state.halted,
        "halt_reason": state.halt_reason,
    }

    (out / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (out / "audit.jsonl").write_text(
        "\n".join(json.dumps(e) for e in state.audit_log) + "\n",
        encoding="utf-8",
    )

    if state.ave_cards:
        cards_dir = out / "ave-cards"
        cards_dir.mkdir(exist_ok=True)
        for card in state.ave_cards:
            (cards_dir / f"{card['ave_id']}.json").write_text(
                json.dumps(card, indent=2), encoding="utf-8"
            )

    logger.info("Campaign %s complete — output at %s", state.campaign_id, out)
    return state


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ARTA — Autonomous Red Team Agent")
    parser.add_argument("--target-name", required=True)
    parser.add_argument("--target-endpoint", required=True)
    parser.add_argument("--framework", default="generic")
    parser.add_argument("--version", default="latest")
    parser.add_argument(
        "--campaign-type",
        choices=[t.value for t in CampaignType],
        default="framework_audit",
    )
    parser.add_argument("--depth", default="comprehensive")
    parser.add_argument("--output-dir", default="./findings")
    args = parser.parse_args()

    target = AgentTarget(
        name=args.target_name,
        framework=args.framework,
        version=args.version,
        endpoint=args.target_endpoint,
    )

    asyncio.run(
        run_campaign(
            target=target,
            campaign_type=CampaignType(args.campaign_type),
            depth=args.depth,
            output_dir=args.output_dir,
        )
    )
