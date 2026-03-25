#!/usr/bin/env python3
"""
NAIL Insurance Integration — Risk Scorer CLI

AVE-based risk quantification for AI agent insurance underwriting.

Usage:
    python risk_scorer.py score --system-config system.yaml
    python risk_scorer.py report --system-config system.yaml --output report/
    python risk_scorer.py compare --system-a sys_a.yaml --system-b sys_b.yaml
    python risk_scorer.py premium --system-config system.yaml --coverage comprehensive
"""

import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"


def load_config(name: str) -> dict:
    """Load a YAML configuration file."""
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        console.print(f"[red]Config not found: {path}[/red]")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def load_system(path: str) -> dict:
    """Load a system configuration."""
    with open(path) as f:
        return yaml.safe_load(f)


def calculate_exposure_score(system: dict, risk_model: dict) -> dict:
    """Calculate exposure score based on applicable AVE categories."""
    arch = system.get("architecture", {})
    weights = risk_model["ave_category_weights"]

    # Determine applicable categories based on architecture
    applicable = {}

    # All systems are exposed to prompt injection
    applicable["prompt_injection"] = 10.0  # assume max exposure

    # Goal drift applies to all autonomous systems
    if arch.get("autonomy", "supervised") != "human-in-loop":
        applicable["goal_drift"] = 8.0

    # Tool misuse if tools are present
    if arch.get("tools"):
        tool_risk = 6.0
        for tool in arch.get("tools", []):
            if tool.get("access") in ("write", "read_write"):
                tool_risk = 9.0
                break
        applicable["tool_misuse"] = tool_risk

    # Memory if persistent
    if arch.get("memory") == "persistent":
        applicable["memory"] = 9.0

    # Delegation if multi-agent
    if arch.get("multi_agent"):
        delegation_type = arch.get("delegation", "controlled")
        if delegation_type == "open":
            applicable["delegation"] = 9.0
        elif delegation_type == "controlled":
            applicable["delegation"] = 5.0

    # Authority based on autonomy level
    if arch.get("autonomy") == "fully-autonomous":
        applicable["authority"] = 8.0
    elif arch.get("autonomy") == "supervised":
        applicable["authority"] = 4.0

    # Output manipulation — always present
    applicable["output_manipulation"] = 5.0

    # Information disclosure based on data sensitivity
    sensitivity = system.get("deployment", {}).get("data_sensitivity", "non-sensitive")
    if sensitivity in ("pii", "financial"):
        applicable["information_disclosure"] = 8.0
    elif sensitivity == "business-sensitive":
        applicable["information_disclosure"] = 5.0

    # Monitoring evasion if multi-agent
    if arch.get("multi_agent") and arch.get("agent_count", 1) > 3:
        applicable["monitoring_evasion"] = 6.0

    # Calculate weighted exposure
    total_weighted_avss = 0.0
    total_max = 0.0
    for cat, avss in applicable.items():
        w = weights.get(cat, 1.0)
        total_weighted_avss += w * avss
        total_max += w * 10.0

    exposure = 100 - (total_weighted_avss / total_max * 100) if total_max > 0 else 50

    return {
        "score": round(max(0, min(100, exposure)), 1),
        "applicable_categories": applicable,
        "category_count": len(applicable),
    }


def calculate_defence_score(system: dict, risk_model: dict) -> dict:
    """Calculate defence score based on certification and practices."""
    cert = system.get("certification", {})
    deploy = system.get("deployment", {})

    tier = cert.get("nail_tier", "none")
    base = risk_model["certification_scores"].get(tier, 0)

    modifiers = risk_model["defence_modifiers"]
    adjustments = []

    # Check incident response plan
    if deploy.get("incident_response_plan"):
        base += modifiers["incident_response_plan"]
        adjustments.append(("Incident response plan", modifiers["incident_response_plan"]))

    # Check continuous monitoring
    if deploy.get("monitoring"):
        base += modifiers["continuous_monitoring"]
        adjustments.append(("Continuous monitoring", modifiers["continuous_monitoring"]))

    # Check cert expiry
    expiry = cert.get("expiry")
    if expiry:
        try:
            expiry_date = date.fromisoformat(expiry)
            if expiry_date < date.today():
                base += modifiers["expired_certification"]
                adjustments.append(("Expired certification", modifiers["expired_certification"]))
        except (ValueError, TypeError):
            pass

    return {
        "score": round(max(0, min(100, base)), 1),
        "tier": tier,
        "adjustments": adjustments,
    }


def calculate_operational_score(system: dict, risk_model: dict) -> dict:
    """Calculate operational risk score."""
    deploy = system.get("deployment", {})
    arch = system.get("architecture", {})
    factors = risk_model["operational_factors"]

    scores = {}

    # Scope
    scope = deploy.get("scope", "public-facing")
    scores["scope"] = factors["scope"].get(scope, 30)

    # Data sensitivity
    sensitivity = deploy.get("data_sensitivity", "business-sensitive")
    scores["data_sensitivity"] = factors["data_sensitivity"].get(sensitivity, 50)

    # Autonomy
    autonomy = deploy.get("autonomy", arch.get("autonomy", "supervised"))
    scores["autonomy"] = factors["autonomy"].get(autonomy, 60)

    # Tool access (worst case across tools)
    tool_score = 90
    for tool in arch.get("tools", []):
        access = tool.get("access", "read")
        if access in ("write", "read_write"):
            tool_score = min(tool_score, factors["tool_access"].get("limited-write", 50))
        elif access == "unrestricted":
            tool_score = min(tool_score, factors["tool_access"].get("unrestricted", 10))
    scores["tool_access"] = tool_score

    # Multi-agent
    if arch.get("multi_agent"):
        delegation = arch.get("delegation", "coordinated")
        if delegation == "open":
            scores["multi_agent"] = factors["multi_agent"].get("open-delegation", 20)
        else:
            scores["multi_agent"] = factors["multi_agent"].get("coordinated", 50)
    else:
        scores["multi_agent"] = factors["multi_agent"].get("single", 80)

    avg = sum(scores.values()) / len(scores) if scores else 50

    return {
        "score": round(avg, 1),
        "factors": scores,
    }


def calculate_track_record(system: dict, risk_model: dict) -> dict:
    """Calculate track record score."""
    history = system.get("history", {})
    tr_config = risk_model["track_record"]

    base = tr_config["base_score"]
    adjustments = []

    # Incident penalty
    incidents = history.get("incidents_12m", 0)
    if incidents > 0:
        penalty = incidents * tr_config["incident_penalty"]
        base += penalty
        adjustments.append((f"{incidents} incidents", penalty))

    # Claim penalty
    claims = history.get("claims_12m", 0)
    if claims > 0:
        penalty = claims * tr_config["claim_penalty"]
        base += penalty
        adjustments.append((f"{claims} claims", penalty))

    # Longevity bonus
    months = history.get("operational_months", 0)
    bonus = min(months * tr_config["longevity_bonus"], tr_config["longevity_cap"])
    if bonus > 0:
        base += bonus
        adjustments.append((f"{months} months operational", bonus))

    return {
        "score": round(max(0, min(100, base)), 1),
        "adjustments": adjustments,
    }


def calculate_composite(exposure, defence, operational, track_record, risk_model):
    """Calculate composite risk score."""
    weights = risk_model["weights"]

    composite = (
        weights["exposure"] * exposure["score"]
        + weights["defence"] * defence["score"]
        + weights["operational"] * operational["score"]
        + weights["track_record"] * track_record["score"]
    )

    # Determine risk tier
    tier_name = "critical"
    tier_data = {}
    for name, data in risk_model["risk_tiers"].items():
        if data["min_score"] <= composite <= data["max_score"]:
            tier_name = name
            tier_data = data
            break

    return {
        "score": round(composite, 1),
        "tier": tier_name,
        "tier_data": tier_data,
        "multiplier": tier_data.get("multiplier", 4.0),
        "decision": tier_data.get("decision", "review_required"),
    }


def full_risk_assessment(system: dict) -> dict:
    """Run a full risk assessment for a system."""
    risk_model = load_config("risk_model")

    exposure = calculate_exposure_score(system, risk_model)
    defence = calculate_defence_score(system, risk_model)
    operational = calculate_operational_score(system, risk_model)
    track_record = calculate_track_record(system, risk_model)
    composite = calculate_composite(exposure, defence, operational, track_record, risk_model)

    return {
        "system": system.get("name", "Unknown"),
        "timestamp": datetime.now().isoformat(),
        "exposure": exposure,
        "defence": defence,
        "operational": operational,
        "track_record": track_record,
        "composite": composite,
    }


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="NAIL Risk Scorer")
def cli():
    """NAIL Insurance Integration — AVE Risk Scorer"""
    pass


@cli.command()
@click.option("--system-config", "-c", type=click.Path(exists=True), required=True,
              help="Path to system configuration YAML")
def score(system_config: str):
    """Calculate risk score for an agent system."""

    system = load_system(system_config)
    result = full_risk_assessment(system)
    comp = result["composite"]

    tier_style = {
        "excellent": "green",
        "good": "cyan",
        "moderate": "yellow",
        "elevated": "red",
        "critical": "red bold",
    }.get(comp["tier"], "white")

    console.print(Panel.fit(
        f"[bold]NAIL Risk Assessment[/bold]\n\n"
        f"System: [bold]{result['system']}[/bold]\n"
        f"Date: {result['timestamp'][:10]}\n\n"
        f"Composite Score: [bold {tier_style}]{comp['score']:.1f}/100[/bold {tier_style}]\n"
        f"Risk Tier: [{tier_style}]{comp['tier_data'].get('label', comp['tier']).upper()}[/{tier_style}]\n"
        f"Premium Multiplier: {comp['multiplier']}×\n"
        f"Decision: {comp['decision'].replace('_', ' ').title()}",
        border_style="blue",
    ))

    # Component breakdown
    console.print("\n[bold]Component Scores:[/bold]\n")
    table = Table(box=box.ROUNDED)
    table.add_column("Component", style="cyan")
    table.add_column("Score", justify="center")
    table.add_column("Weight", justify="center")
    table.add_column("Weighted", justify="center")

    risk_model = load_config("risk_model")
    weights = risk_model["weights"]

    components = [
        ("Exposure", result["exposure"]["score"], weights["exposure"]),
        ("Defence", result["defence"]["score"], weights["defence"]),
        ("Operational", result["operational"]["score"], weights["operational"]),
        ("Track Record", result["track_record"]["score"], weights["track_record"]),
    ]

    for name, s, w in components:
        style = "green" if s >= 70 else "yellow" if s >= 40 else "red"
        table.add_row(name, f"[{style}]{s:.1f}[/{style}]", f"{w:.0%}", f"{s * w:.1f}")

    console.print(table)

    # Exposure details
    exp = result["exposure"]
    console.print(f"\n[bold]Exposure Analysis ({exp['category_count']} applicable categories):[/bold]")
    for cat, avss in exp["applicable_categories"].items():
        bar_len = int(avss)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        style = "red" if avss >= 7 else "yellow" if avss >= 4 else "green"
        console.print(f"  [{style}]{bar}[/{style}] {avss:.1f}/10  {cat}")


@cli.command()
@click.option("--system-config", "-c", type=click.Path(exists=True), required=True,
              help="Path to system configuration YAML")
@click.option("--coverage", "-v", type=click.Choice([
    "agent_malfunction", "data_breach", "third_party_harm",
    "business_interruption", "comprehensive"
]), default="comprehensive", help="Coverage type")
@click.option("--industry", "-i", type=str, default="technology",
              help="Industry sector")
@click.option("--agents", "-n", type=int, default=1,
              help="Number of agents to insure")
def premium(system_config: str, coverage: str, industry: str, agents: int):
    """Estimate insurance premium for an agent system."""

    system = load_system(system_config)
    result = full_risk_assessment(system)
    risk_model = load_config("risk_model")
    industry_config = load_config("industry")

    comp = result["composite"]

    # Base premium
    premiums = risk_model["base_premiums"]
    coverage_data = premiums.get(coverage, premiums["comprehensive"])
    base = (coverage_data["min"] + coverage_data["max"]) / 2  # midpoint

    # Risk multiplier
    risk_mult = comp["multiplier"]

    # Industry multiplier
    ind_data = industry_config["industries"].get(industry, {"multiplier": 1.0})
    ind_mult = ind_data["multiplier"]

    # Volume discount
    vol_mult = 1.0
    for tier in sorted(industry_config["volume_discounts"], key=lambda x: x["agents"], reverse=True):
        if agents >= tier["agents"]:
            vol_mult = tier["discount"]
            break

    final = base * risk_mult * ind_mult * vol_mult

    console.print(Panel.fit(
        f"[bold]NAIL Insurance Premium Estimate[/bold]\n\n"
        f"System: [bold]{result['system']}[/bold]\n"
        f"Coverage: {coverage_data['description']}\n"
        f"Industry: {industry.title()} ({ind_mult}×)\n"
        f"Agents: {agents} ({vol_mult}× volume)",
        border_style="green",
    ))

    console.print(f"\n[bold]Premium Calculation:[/bold]\n")

    table = Table(box=box.SIMPLE)
    table.add_column("Item", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Base Premium (midpoint)", f"${base:,.0f}")
    table.add_row(f"Risk Multiplier ({comp['tier_data'].get('label', '')})", f"×{risk_mult}")
    table.add_row(f"Industry ({industry.title()})", f"×{ind_mult}")
    table.add_row(f"Volume ({agents} agents)", f"×{vol_mult}")
    table.add_row("", "")
    table.add_row("[bold]Estimated Annual Premium[/bold]", f"[bold green]${final:,.0f}[/bold green]")
    table.add_row("Premium Range",
                  f"${coverage_data['min'] * risk_mult * ind_mult * vol_mult:,.0f}–"
                  f"${coverage_data['max'] * risk_mult * ind_mult * vol_mult:,.0f}")

    console.print(table)

    console.print(f"\n[dim]Note: This is an estimate. Actual premiums depend on "
                  f"underwriting review and policy terms.[/dim]")


@cli.command()
@click.option("--system-a", "-a", type=click.Path(exists=True), required=True,
              help="First system configuration")
@click.option("--system-b", "-b", type=click.Path(exists=True), required=True,
              help="Second system configuration")
def compare(system_a: str, system_b: str):
    """Compare risk profiles of two agent systems."""

    sys_a = load_system(system_a)
    sys_b = load_system(system_b)
    result_a = full_risk_assessment(sys_a)
    result_b = full_risk_assessment(sys_b)

    console.print(Panel.fit(
        "[bold]NAIL Risk Comparison[/bold]",
        border_style="blue",
    ))

    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column(result_a["system"], justify="center")
    table.add_column(result_b["system"], justify="center")
    table.add_column("Δ", justify="center")

    metrics = [
        ("Composite Score", result_a["composite"]["score"], result_b["composite"]["score"]),
        ("Exposure", result_a["exposure"]["score"], result_b["exposure"]["score"]),
        ("Defence", result_a["defence"]["score"], result_b["defence"]["score"]),
        ("Operational", result_a["operational"]["score"], result_b["operational"]["score"]),
        ("Track Record", result_a["track_record"]["score"], result_b["track_record"]["score"]),
        ("Premium Multiplier", result_a["composite"]["multiplier"], result_b["composite"]["multiplier"]),
    ]

    for name, a, b in metrics:
        delta = b - a
        delta_style = "green" if delta > 0 else "red" if delta < 0 else "dim"
        delta_str = f"[{delta_style}]{delta:+.1f}[/{delta_style}]"
        table.add_row(name, f"{a:.1f}", f"{b:.1f}", delta_str)

    console.print(table)

    # Risk tier comparison
    tier_a = result_a["composite"]["tier_data"].get("label", "?")
    tier_b = result_b["composite"]["tier_data"].get("label", "?")
    console.print(f"\nRisk Tier: [bold]{result_a['system']}[/bold] = {tier_a} | "
                  f"[bold]{result_b['system']}[/bold] = {tier_b}")


@cli.command()
@click.option("--system-config", "-c", type=click.Path(exists=True), required=True,
              help="Path to system configuration YAML")
@click.option("--output", "-o", type=click.Path(), default="report",
              help="Output directory")
def report(system_config: str, output: str):
    """Generate a full risk assessment report."""

    system = load_system(system_config)
    result = full_risk_assessment(system)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    comp = result["composite"]

    # Generate markdown report
    report_md = f"""# NAIL Insurance Risk Assessment Report

**System:** {result['system']}
**Date:** {result['timestamp'][:10]}
**Risk Scorer Version:** 1.0.0

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Composite Risk Score** | {comp['score']:.1f}/100 |
| **Risk Tier** | {comp['tier_data'].get('label', comp['tier'])} |
| **Premium Multiplier** | {comp['multiplier']}× |
| **Underwriting Decision** | {comp['decision'].replace('_', ' ').title()} |

## Component Scores

| Component | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Exposure | {result['exposure']['score']:.1f} | 40% | {result['exposure']['score'] * 0.4:.1f} |
| Defence | {result['defence']['score']:.1f} | 30% | {result['defence']['score'] * 0.3:.1f} |
| Operational | {result['operational']['score']:.1f} | 20% | {result['operational']['score'] * 0.2:.1f} |
| Track Record | {result['track_record']['score']:.1f} | 10% | {result['track_record']['score'] * 0.1:.1f} |

## Exposure Analysis

Applicable AVE categories: {result['exposure']['category_count']}

| Category | AVSS Exposure |
|----------|--------------|
"""
    for cat, avss in result['exposure']['applicable_categories'].items():
        report_md += f"| {cat} | {avss:.1f}/10 |\n"

    report_md += f"""
## Defence Posture

- NAIL Certified Tier: **{result['defence']['tier'].title()}**
- Base Score: {result['defence']['score']:.1f}/100

## Recommendations

"""
    if comp['score'] < 40:
        report_md += "1. **Critical:** Obtain NAIL Bronze certification as minimum\n"
        report_md += "2. Deploy input validation and prompt boundary markers\n"
        report_md += "3. Implement continuous monitoring for all agent activities\n"
    elif comp['score'] < 60:
        report_md += "1. Upgrade NAIL certification to Silver or Gold tier\n"
        report_md += "2. Address high-exposure AVE categories\n"
        report_md += "3. Develop incident response procedures\n"
    elif comp['score'] < 80:
        report_md += "1. Consider Gold or Platinum certification for premium reduction\n"
        report_md += "2. Add longitudinal monitoring for ongoing assessment\n"
    else:
        report_md += "1. Maintain current security posture\n"
        report_md += "2. Monitor for new AVE categories\n"
        report_md += "3. Consider Platinum certification for maximum premium benefit\n"

    report_md += f"""
---

*Generated by NAIL Insurance Risk Scorer v1.0.0*
*NAIL Institute — Neuravant AI Limited*
"""

    report_path = output_dir / f"risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, "w") as f:
        f.write(report_md)

    # Also save JSON
    json_path = output_dir / f"risk_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    console.print(f"[bold green]Report generated:[/bold green]")
    console.print(f"  📄 {report_path}")
    console.print(f"  📊 {json_path}")


if __name__ == "__main__":
    cli()
