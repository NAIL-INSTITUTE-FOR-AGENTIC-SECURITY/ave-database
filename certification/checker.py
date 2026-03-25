#!/usr/bin/env python3
"""
NAIL Certified — Compliance Checker CLI

Automated certification testing for agentic AI systems.
Evaluates systems against the AVE Database vulnerability categories.

Usage:
    python checker.py assess --system-config config.yaml --tier bronze
    python checker.py test --system-url http://agent:8080 --tier silver
    python checker.py report --results results/
    python checker.py badge --cert-id NAIL-CERT-2026-001 --tier gold
    python checker.py validate --card AVE-2025-0001.json
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()

# Paths
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
TESTS_DIR = BASE_DIR / "tests"
BADGES_DIR = BASE_DIR / "badges"
REGISTRY_DIR = BASE_DIR / "registry"


def load_config(name: str) -> dict:
    """Load a YAML configuration file."""
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        console.print(f"[red]Configuration file not found: {path}[/red]")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def load_tier_config(tier: str) -> dict:
    """Load configuration for a specific certification tier."""
    config = load_config("tiers")
    if tier not in config["tiers"]:
        console.print(f"[red]Unknown tier: {tier}[/red]")
        console.print(f"Available tiers: {', '.join(config['tiers'].keys())}")
        sys.exit(1)
    return config["tiers"][tier]


def load_test_definitions() -> dict:
    """Load test definitions for all categories."""
    return load_config("tests")


def calculate_score(results: dict, tier_config: dict) -> dict:
    """Calculate certification score from test results."""
    config = load_config("tiers")
    weights = config.get("category_weights", {})
    required_categories = tier_config["categories_required"]

    total_weighted = 0.0
    max_weighted = 0.0
    category_scores = {}

    for category in required_categories:
        if category in results:
            score = results[category].get("score", 0)
            weight = weights.get(category, 1.0)
            total_weighted += weight * score
            max_weighted += weight * 4  # max score per category is 4
            category_scores[category] = {
                "score": score,
                "weight": weight,
                "weighted": weight * score,
                "max_weighted": weight * 4,
                "label": config["score_labels"].get(score, "Unknown"),
            }
        else:
            weight = weights.get(category, 1.0)
            max_weighted += weight * 4
            category_scores[category] = {
                "score": 0,
                "weight": weight,
                "weighted": 0,
                "max_weighted": weight * 4,
                "label": config["score_labels"].get(0, "Not tested"),
            }

    percentage = (total_weighted / max_weighted * 100) if max_weighted > 0 else 0

    return {
        "total_weighted": total_weighted,
        "max_weighted": max_weighted,
        "percentage": round(percentage, 1),
        "category_scores": category_scores,
        "pass": percentage >= tier_config["min_score"],
        "min_required": tier_config["min_score"],
    }


def generate_cert_id(tier: str) -> str:
    """Generate a unique certification ID."""
    year = datetime.now().year
    # In production, this would check the registry for uniqueness
    seq = 1
    registry = REGISTRY_DIR / f"{year}"
    if registry.exists():
        existing = list(registry.glob("*.json"))
        seq = len(existing) + 1
    return f"NAIL-CERT-{year}-{seq:04d}"


# ─────────────────────────────────────────
# CLI Commands
# ─────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="NAIL Certified Checker")
def cli():
    """NAIL Certified — Agentic AI Security Compliance Checker"""
    pass


@cli.command()
@click.option("--system-config", "-c", type=click.Path(exists=True),
              help="Path to system configuration YAML")
@click.option("--tier", "-t", type=click.Choice(["bronze", "silver", "gold", "platinum"]),
              default="bronze", help="Certification tier to assess")
def assess(system_config: Optional[str], tier: str):
    """Run a self-assessment against certification requirements."""

    tier_config = load_tier_config(tier)
    tests = load_test_definitions()

    console.print(Panel.fit(
        f"[bold cyan]NAIL Certified Self-Assessment[/bold cyan]\n"
        f"Tier: [bold]{tier_config['name']}[/bold] | "
        f"Min Score: {tier_config['min_score']}% | "
        f"Categories: {len(tier_config['categories_required'])}",
        border_style="cyan",
    ))

    # Load system config if provided
    system = {}
    if system_config:
        with open(system_config) as f:
            system = yaml.safe_load(f) or {}
        console.print(f"\n📋 System: [bold]{system.get('name', 'Unknown')}[/bold]")
        console.print(f"   Framework: {system.get('framework', 'Not specified')}")
        console.print(f"   Model: {system.get('model', 'Not specified')}")

    # Display required tests
    console.print(f"\n[bold]Required Test Categories ({len(tier_config['categories_required'])}):[/bold]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("#", style="dim", width=3)
    table.add_column("Category", style="cyan")
    table.add_column("Tests", justify="center")
    table.add_column("Description")

    for i, category in enumerate(tier_config["categories_required"], 1):
        cat_tests = tests.get("tests", {}).get(category, {})
        test_count = len(cat_tests.get("test_cases", []))
        table.add_row(
            str(i),
            category,
            str(test_count),
            cat_tests.get("description", "—"),
        )

    console.print(table)

    # Requirements checklist
    console.print("\n[bold]Additional Requirements:[/bold]\n")
    reqs = tier_config["requirements"]
    for req, needed in reqs.items():
        if isinstance(needed, bool):
            icon = "✅" if needed else "—"
            console.print(f"  {icon} {req.replace('_', ' ').title()}")
        elif isinstance(needed, int):
            console.print(f"  📊 {req.replace('_', ' ').title()}: {needed}")

    console.print(f"\n[bold yellow]Assessment mode:[/bold yellow] No live testing performed.")
    console.print("Run [bold]checker.py test[/bold] to execute automated tests against a live system.")


@cli.command()
@click.option("--system-url", "-u", type=str, required=True,
              help="URL of the agent system to test")
@click.option("--tier", "-t", type=click.Choice(["bronze", "silver", "gold", "platinum"]),
              default="bronze", help="Certification tier to test for")
@click.option("--output", "-o", type=click.Path(), default="results",
              help="Output directory for results")
@click.option("--category", "-c", type=str, multiple=True,
              help="Test specific categories only")
@click.option("--timeout", type=int, default=30,
              help="Timeout per test case (seconds)")
@click.option("--dry-run", is_flag=True,
              help="Show what would be tested without executing")
def test(system_url: str, tier: str, output: str, category: tuple,
         timeout: int, dry_run: bool):
    """Run automated certification tests against a live system."""

    tier_config = load_tier_config(tier)
    tests = load_test_definitions()
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        f"[bold green]NAIL Certified Test Runner[/bold green]\n"
        f"Target: [bold]{system_url}[/bold]\n"
        f"Tier: [bold]{tier_config['name']}[/bold] | "
        f"Min Score: {tier_config['min_score']}%",
        border_style="green",
    ))

    # Determine categories to test
    categories = list(category) if category else tier_config["categories_required"]

    if dry_run:
        console.print("\n[bold yellow]DRY RUN — No tests will be executed[/bold yellow]\n")

    results = {}
    total_tests = 0
    total_passed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for cat in categories:
            cat_tests = tests.get("tests", {}).get(cat, {})
            test_cases = cat_tests.get("test_cases", [])

            if not test_cases:
                console.print(f"  [dim]⏭  {cat}: No test cases defined[/dim]")
                continue

            task = progress.add_task(f"Testing {cat}...", total=len(test_cases))

            cat_results = []
            for tc in test_cases:
                total_tests += 1

                if dry_run:
                    result = {"id": tc["id"], "name": tc["name"], "status": "dry-run"}
                else:
                    # In production, this would make HTTP calls to the system
                    # and evaluate responses against expected behaviour
                    result = {
                        "id": tc["id"],
                        "name": tc["name"],
                        "severity": tc["severity"],
                        "attack_type": tc["attack_type"],
                        "status": "pending",
                        "score": 0,
                        "details": f"Test {tc['id']} requires live system at {system_url}",
                        "timestamp": datetime.now().isoformat(),
                    }

                cat_results.append(result)
                progress.advance(task)

            # Calculate category score (average of test scores)
            if cat_results and not dry_run:
                avg_score = sum(r.get("score", 0) for r in cat_results) / len(cat_results)
                results[cat] = {
                    "score": round(avg_score),
                    "tests": cat_results,
                    "total": len(cat_results),
                    "tested_at": datetime.now().isoformat(),
                }

    # Calculate overall score
    if not dry_run and results:
        scoring = calculate_score(results, tier_config)

        # Display results
        console.print(f"\n[bold]Test Results:[/bold]\n")

        table = Table(box=box.ROUNDED)
        table.add_column("Category", style="cyan")
        table.add_column("Score", justify="center")
        table.add_column("Weight", justify="center")
        table.add_column("Weighted", justify="center")
        table.add_column("Status")

        for cat, data in scoring["category_scores"].items():
            score_style = "green" if data["score"] >= 3 else "yellow" if data["score"] >= 2 else "red"
            table.add_row(
                cat,
                f"[{score_style}]{data['score']}/4[/{score_style}]",
                f"{data['weight']:.1f}×",
                f"{data['weighted']:.1f}/{data['max_weighted']:.1f}",
                data["label"],
            )

        console.print(table)

        pass_style = "green" if scoring["pass"] else "red"
        console.print(f"\n[bold]Overall Score: [{pass_style}]{scoring['percentage']}%[/{pass_style}][/bold]"
                      f" (minimum: {scoring['min_required']}%)")

        if scoring["pass"]:
            console.print(f"\n[bold green]✅ PASSED — Eligible for {tier_config['name']} certification[/bold green]")
        else:
            console.print(f"\n[bold red]❌ FAILED — Below minimum for {tier_config['name']}[/bold red]")
            deficit = scoring["min_required"] - scoring["percentage"]
            console.print(f"   Improvement needed: +{deficit:.1f}%")

        # Save results
        results_file = output_dir / f"certification_{tier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump({
                "tier": tier,
                "system_url": system_url,
                "scoring": scoring,
                "results": results,
                "timestamp": datetime.now().isoformat(),
                "checker_version": "1.0.0",
            }, f, indent=2, default=str)
        console.print(f"\n📄 Results saved: {results_file}")

    elif dry_run:
        console.print(f"\n[bold]Dry run complete.[/bold] {total_tests} tests would be executed across {len(categories)} categories.")


@cli.command()
@click.option("--results", "-r", type=click.Path(exists=True), required=True,
              help="Path to results JSON file or directory")
def report(results: str):
    """Generate a human-readable certification report."""

    results_path = Path(results)

    if results_path.is_dir():
        files = sorted(results_path.glob("certification_*.json"), reverse=True)
        if not files:
            console.print("[red]No certification results found in directory.[/red]")
            sys.exit(1)
        results_path = files[0]
        console.print(f"Using latest results: {results_path.name}")

    with open(results_path) as f:
        data = json.load(f)

    scoring = data.get("scoring", {})
    tier = data.get("tier", "unknown")

    console.print(Panel.fit(
        f"[bold]NAIL Certified — Certification Report[/bold]\n\n"
        f"Tier: [bold cyan]{tier.title()}[/bold cyan]\n"
        f"System: {data.get('system_url', 'N/A')}\n"
        f"Date: {data.get('timestamp', 'N/A')}\n"
        f"Score: [bold]{scoring.get('percentage', 0)}%[/bold] "
        f"({'PASS' if scoring.get('pass') else 'FAIL'})",
        border_style="blue",
    ))

    # Category breakdown
    console.print("\n[bold]Category Breakdown:[/bold]\n")

    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Category", style="cyan")
    table.add_column("Score", justify="center")
    table.add_column("Label")
    table.add_column("Recommendation")

    for cat, data_cat in scoring.get("category_scores", {}).items():
        score = data_cat.get("score", 0)
        if score >= 3:
            rec = "[green]Meets standard[/green]"
        elif score >= 2:
            rec = "[yellow]Improve defence coverage[/yellow]"
        elif score >= 1:
            rec = "[red]Significant improvement needed[/red]"
        else:
            rec = "[red bold]Critical — no defence detected[/red bold]"

        table.add_row(cat, f"{score}/4", data_cat.get("label", ""), rec)

    console.print(table)


@cli.command()
@click.option("--cert-id", "-i", type=str, help="Certification ID")
@click.option("--tier", "-t", type=click.Choice(["bronze", "silver", "gold", "platinum"]),
              required=True, help="Badge tier")
@click.option("--output", "-o", type=click.Path(), default="badges",
              help="Output directory for badge files")
def badge(cert_id: Optional[str], tier: str, output: str):
    """Generate certification badge files."""

    tier_config = load_tier_config(tier)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not cert_id:
        cert_id = generate_cert_id(tier)

    color = tier_config["badge_color"]
    name = tier_config["name"]

    # Generate SVG badge
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="36">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="a">
    <rect width="200" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#a)">
    <path fill="#555" d="M0 0h110v20H0z"/>
    <path fill="{color}" d="M110 0h90v20H110z"/>
    <path fill="url(#b)" d="M0 0h200v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="55" y="15" fill="#010101" fill-opacity=".3">NAIL Certified</text>
    <text x="55" y="14">NAIL Certified</text>
    <text x="155" y="15" fill="#010101" fill-opacity=".3">{name}</text>
    <text x="155" y="14">{name}</text>
  </g>
  <text x="100" y="33" text-anchor="middle" font-family="monospace" font-size="8" fill="#666">{cert_id}</text>
</svg>'''

    svg_path = output_dir / f"certified-{tier}.svg"
    with open(svg_path, "w") as f:
        f.write(svg)

    console.print(f"[bold green]Badge generated:[/bold green] {svg_path}")
    console.print(f"\n[bold]Markdown:[/bold]")
    console.print(f'[![NAIL Certified {name}](https://nailinstitute.org/badges/certified-{tier}.svg)]'
                  f'(https://nailinstitute.org/certified/{cert_id})')
    console.print(f"\n[bold]HTML:[/bold]")
    console.print(f'<a href="https://nailinstitute.org/certified/{cert_id}">')
    console.print(f'  <img src="https://nailinstitute.org/badges/certified-{tier}.svg" '
                  f'alt="NAIL Certified {name}" />')
    console.print(f'</a>')


@cli.command()
@click.option("--card", "-c", type=click.Path(exists=True), required=True,
              help="Path to AVE card JSON file")
def validate(card: str):
    """Validate an AVE card against the formal specification."""

    with open(card) as f:
        data = json.load(f)

    console.print(f"[bold]Validating:[/bold] {card}\n")

    errors = []
    warnings = []

    # Required fields
    required = [
        "ave_id", "name", "category", "severity", "status",
        "summary", "mechanism", "blast_radius", "prerequisite",
        "environment", "evidence", "defences", "date_discovered",
        "avss_score", "_meta", "contributor"
    ]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None:
            errors.append(f"Required field is null: {field}")

    # AVE ID format
    ave_id = data.get("ave_id", "")
    import re
    if not re.match(r"^AVE-\d{4}-\d{4}$", ave_id):
        errors.append(f"Invalid AVE ID format: {ave_id} (expected AVE-YYYY-NNNN)")

    # Check filename matches ave_id
    filename = Path(card).stem
    if filename != ave_id:
        warnings.append(f"Filename '{filename}' does not match ave_id '{ave_id}'")

    # Category validation
    valid_categories = [
        "prompt_injection", "goal_drift", "tool_misuse", "memory",
        "delegation", "authority", "output_manipulation", "model_extraction",
        "supply_chain", "denial_of_service", "information_disclosure",
        "consensus", "monitoring_evasion"
    ]
    if data.get("category") not in valid_categories:
        errors.append(f"Invalid category: {data.get('category')}")

    # Severity validation
    valid_severities = ["critical", "high", "medium", "low", "informational"]
    if data.get("severity") not in valid_severities:
        errors.append(f"Invalid severity: {data.get('severity')}")

    # Status validation
    valid_statuses = [
        "published", "draft", "deprecated", "under-review",
        "proven", "proven_mitigated", "not_proven", "theoretical"
    ]
    if data.get("status") not in valid_statuses:
        errors.append(f"Invalid status: {data.get('status')}")

    # AVSS score checks
    avss = data.get("avss_score", {})
    if avss:
        score = avss.get("overall_score")
        if score is not None and (score < 0 or score > 10):
            errors.append(f"AVSS score out of range: {score} (must be 0.0-10.0)")
        if avss.get("severity_label") != data.get("severity"):
            warnings.append(f"avss_score.severity_label '{avss.get('severity_label')}' "
                          f"does not match severity '{data.get('severity')}'")

    # Environment checks
    env = data.get("environment", {})
    if env:
        for field in ["frameworks", "models_tested", "multi_agent", "tools_required", "memory_required"]:
            if field not in env:
                errors.append(f"Missing environment field: {field}")

    # Summary length advisory
    summary = data.get("summary", "")
    if len(summary) > 500:
        warnings.append(f"Summary exceeds recommended 500 chars ({len(summary)} chars)")

    # Evidence checks
    if data.get("status") == "proven" and not data.get("evidence"):
        warnings.append("Status is 'proven' but evidence array is empty")

    # Meta checks
    meta = data.get("_meta", {})
    if meta:
        if "schema_version" not in meta:
            errors.append("Missing _meta.schema_version")
        if "generated_at" not in meta:
            errors.append("Missing _meta.generated_at")

    # Related AVEs format
    for related in data.get("related_aves", []):
        if not re.match(r"^AVE-\d{4}-\d{4}$", related):
            errors.append(f"Invalid related AVE ID: {related}")

    # Display results
    if errors:
        console.print(f"[bold red]❌ {len(errors)} Error(s):[/bold red]")
        for e in errors:
            console.print(f"   [red]• {e}[/red]")

    if warnings:
        console.print(f"\n[bold yellow]⚠️  {len(warnings)} Warning(s):[/bold yellow]")
        for w in warnings:
            console.print(f"   [yellow]• {w}[/yellow]")

    if not errors and not warnings:
        console.print("[bold green]✅ Card is valid — no errors or warnings[/bold green]")
    elif not errors:
        console.print(f"\n[bold green]✅ Card is valid ({len(warnings)} warnings)[/bold green]")
    else:
        console.print(f"\n[bold red]Card validation failed[/bold red]")
        sys.exit(1)


@cli.command(name="list")
def list_tiers():
    """List available certification tiers and requirements."""

    config = load_config("tiers")

    console.print(Panel.fit(
        "[bold]NAIL Certified — Certification Tiers[/bold]",
        border_style="cyan",
    ))

    for tier_name, tier_data in config["tiers"].items():
        reqs = tier_data["requirements"]
        req_list = []
        for r, v in reqs.items():
            if isinstance(v, bool) and v:
                req_list.append(r.replace("_", " ").title())
            elif isinstance(v, int):
                req_list.append(f"{r.replace('_', ' ').title()}: {v}")

        fee = tier_data["fee"]
        fee_str = "Free" if fee["full_certification"] == 0 else f"${fee['full_certification']:,}/year"

        console.print(f"\n[bold]{tier_data['name']}[/bold] ({tier_name})")
        console.print(f"  Min Score: {tier_data['min_score']}% | "
                      f"Validity: {tier_data['validity_months']} months | "
                      f"Fee: {fee_str}")
        console.print(f"  Categories: {len(tier_data['categories_required'])}")
        console.print(f"  Requirements: {', '.join(req_list)}")


if __name__ == "__main__":
    cli()
