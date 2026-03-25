#!/usr/bin/env python3
"""
NAIL Regulatory Compliance — CLI Tool

Maps AVE vulnerabilities to regulatory requirements and generates compliance reports.

Usage:
    python compliance.py report --regulation eu-ai-act --system-config system.yaml
    python compliance.py check --regulation nist-ai-rmf --tier silver
    python compliance.py map --category prompt_injection
    python compliance.py matrix --system-config system.yaml
    python compliance.py list
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box

console = Console()

BASE_DIR = Path(__file__).parent
MAPPINGS_DIR = BASE_DIR / "mappings"
TEMPLATES_DIR = BASE_DIR / "templates"

REGULATION_FILES = {
    "eu-ai-act": "eu_ai_act.yaml",
    "nist-ai-rmf": "nist_ai_rmf.yaml",
    "iso-42001": "iso_42001.yaml",
    "eo-14110": "eo_14110.yaml",
}

AVE_CATEGORIES = [
    "prompt_injection", "goal_drift", "tool_misuse", "memory",
    "delegation", "authority", "output_manipulation", "model_extraction",
    "supply_chain", "denial_of_service", "information_disclosure",
    "consensus", "monitoring_evasion",
]


def load_mapping(regulation: str) -> dict:
    """Load a regulatory mapping file."""
    filename = REGULATION_FILES.get(regulation)
    if not filename:
        console.print(f"[red]Unknown regulation: {regulation}[/red]")
        console.print(f"Available: {', '.join(REGULATION_FILES.keys())}")
        sys.exit(1)
    path = MAPPINGS_DIR / filename
    if not path.exists():
        console.print(f"[red]Mapping file not found: {path}[/red]")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def load_all_mappings() -> dict:
    """Load all regulatory mappings."""
    all_mappings = {}
    for reg_key, filename in REGULATION_FILES.items():
        path = MAPPINGS_DIR / filename
        if path.exists():
            with open(path) as f:
                all_mappings[reg_key] = yaml.safe_load(f)
    return all_mappings


def get_categories_for_regulation(mapping: dict) -> set:
    """Extract all AVE categories referenced in a regulatory mapping."""
    categories = set()

    # EU AI Act style
    for level_data in mapping.get("risk_levels", {}).values():
        cats = level_data.get("ave_categories", [])
        if cats == "all":
            return set(AVE_CATEGORIES)
        categories.update(cats)

    for article in mapping.get("article_mappings", []):
        cats = article.get("ave_categories", [])
        if cats == "all":
            return set(AVE_CATEGORIES)
        categories.update(cats)

    # NIST style
    for func_data in mapping.get("functions", {}).values():
        for sub in func_data.get("subcategories", []):
            # NIST doesn't directly reference categories
            pass

    # ISO style
    for clause in mapping.get("clause_mappings", []):
        for sub in clause.get("subclauses", []):
            pass

    # EO style
    for section in mapping.get("section_mappings", []):
        cats = section.get("ave_categories", [])
        categories.update(cats)

    return categories


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="NAIL Compliance Checker")
def cli():
    """NAIL Regulatory Compliance — AVE-to-Regulation Mapping"""
    pass


@cli.command(name="list")
def list_regulations():
    """List all supported regulatory frameworks."""

    console.print(Panel.fit(
        "[bold]Supported Regulatory Frameworks[/bold]",
        border_style="cyan",
    ))

    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Jurisdiction")
    table.add_column("Type")
    table.add_column("AVE Categories")

    for reg_key, filename in REGULATION_FILES.items():
        path = MAPPINGS_DIR / filename
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f)
            reg = data.get("regulation", {})
            cats = get_categories_for_regulation(data)
            table.add_row(
                reg_key,
                reg.get("name", "?"),
                reg.get("jurisdiction", "?"),
                reg.get("type", "regulation"),
                str(len(cats)) if cats else "All",
            )

    console.print(table)


@cli.command()
@click.option("--category", "-c", type=click.Choice(AVE_CATEGORIES), required=True,
              help="AVE category to map")
def map(category: str):
    """Show all regulatory requirements that map to an AVE category."""

    console.print(Panel.fit(
        f"[bold]Regulatory Mapping: [cyan]{category}[/cyan][/bold]",
        border_style="blue",
    ))

    all_mappings = load_all_mappings()

    for reg_key, data in all_mappings.items():
        reg_name = data.get("regulation", {}).get("name", reg_key)
        matches = []

        # EU AI Act style
        for article in data.get("article_mappings", []):
            cats = article.get("ave_categories", [])
            if cats == "all" or category in cats:
                matches.append({
                    "ref": article.get("article", "?"),
                    "title": article.get("title", "?"),
                    "obligations": article.get("obligations", []),
                })

        # EO style
        for section in data.get("section_mappings", []):
            cats = section.get("ave_categories", [])
            if category in cats:
                matches.append({
                    "ref": f"§{section.get('section', '?')}",
                    "title": section.get("title", "?"),
                    "obligations": section.get("requirements", []),
                })

        if matches:
            console.print(f"\n[bold cyan]{reg_name}[/bold cyan]")
            for m in matches:
                console.print(f"  📜 {m['ref']}: {m['title']}")
                for ob in m.get("obligations", [])[:3]:
                    console.print(f"     • {ob}")


@cli.command()
@click.option("--regulation", "-r", type=click.Choice(list(REGULATION_FILES.keys())),
              required=True, help="Regulation to check against")
@click.option("--tier", "-t", type=click.Choice(["bronze", "silver", "gold", "platinum"]),
              default="silver", help="NAIL Certification tier")
@click.option("--system-config", "-c", type=click.Path(exists=True),
              help="System configuration YAML")
def check(regulation: str, tier: str, system_config: Optional[str]):
    """Check compliance status for a specific regulation."""

    mapping = load_mapping(regulation)
    reg = mapping.get("regulation", {})

    console.print(Panel.fit(
        f"[bold]Compliance Check: {reg.get('name', regulation)}[/bold]\n"
        f"Jurisdiction: {reg.get('jurisdiction', '?')}\n"
        f"NAIL Tier: {tier.title()}",
        border_style="green",
    ))

    # Determine required categories from the regulation
    required_cats = get_categories_for_regulation(mapping)
    if not required_cats:
        required_cats = set(AVE_CATEGORIES)

    # Map tier to tested categories
    tier_categories = {
        "bronze": {"prompt_injection", "goal_drift", "tool_misuse", "memory"},
        "silver": {"prompt_injection", "goal_drift", "tool_misuse", "memory",
                   "delegation", "authority", "output_manipulation"},
        "gold": set(AVE_CATEGORIES),
        "platinum": set(AVE_CATEGORIES),
    }

    tested = tier_categories.get(tier, set())
    covered = required_cats & tested
    gaps = required_cats - tested

    console.print(f"\n[bold]Coverage Analysis:[/bold]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("AVE Category", style="cyan")
    table.add_column("Required", justify="center")
    table.add_column("Tested at {tier}", justify="center")
    table.add_column("Status")

    for cat in sorted(AVE_CATEGORIES):
        required = "✅" if cat in required_cats else "—"
        tested_str = "✅" if cat in tested else "❌"
        if cat in required_cats and cat in tested:
            status = "[green]Covered[/green]"
        elif cat in required_cats and cat not in tested:
            status = "[red]GAP — upgrade tier[/red]"
        elif cat not in required_cats and cat in tested:
            status = "[dim]Extra coverage[/dim]"
        else:
            status = "[dim]Not required[/dim]"
        table.add_row(cat, required, tested_str, status)

    console.print(table)

    coverage_pct = len(covered) / len(required_cats) * 100 if required_cats else 100
    style = "green" if coverage_pct == 100 else "yellow" if coverage_pct >= 70 else "red"

    console.print(f"\n[bold]Coverage: [{style}]{coverage_pct:.0f}%[/{style}][/bold] "
                  f"({len(covered)}/{len(required_cats)} required categories tested)")

    if gaps:
        console.print(f"\n[bold red]Gaps ({len(gaps)}):[/bold red]")
        for g in sorted(gaps):
            console.print(f"  ❌ {g}")
        min_tier = "gold" if len(gaps) > 3 else "silver"
        console.print(f"\n[bold yellow]Recommendation:[/bold yellow] "
                      f"Upgrade to [bold]{min_tier.title()}[/bold] certification "
                      f"to close compliance gaps.")
    else:
        console.print(f"\n[bold green]✅ Full coverage — all regulatory "
                      f"categories tested at {tier.title()} tier[/bold green]")


@cli.command()
@click.option("--system-config", "-c", type=click.Path(exists=True),
              help="System configuration YAML")
@click.option("--regulations", "-r", type=str, default=None,
              help="Comma-separated regulation IDs (default: all)")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output file path for matrix")
def matrix(system_config: Optional[str], regulations: Optional[str], output: Optional[str]):
    """Generate multi-jurisdiction compliance matrix."""

    all_mappings = load_all_mappings()

    if regulations:
        reg_list = [r.strip() for r in regulations.split(",")]
        all_mappings = {k: v for k, v in all_mappings.items() if k in reg_list}

    console.print(Panel.fit(
        "[bold]Multi-Jurisdiction Compliance Matrix[/bold]",
        border_style="blue",
    ))

    # Build matrix: category × regulation
    table = Table(box=box.ROUNDED)
    table.add_column("AVE Category", style="cyan")

    reg_names = {}
    for reg_key, data in all_mappings.items():
        name = data.get("regulation", {}).get("name", reg_key)
        reg_names[reg_key] = name
        table.add_column(name, justify="center")

    for cat in AVE_CATEGORIES:
        row = [cat]
        for reg_key, data in all_mappings.items():
            cats = get_categories_for_regulation(data)
            if cat in cats or not cats:
                row.append("[green]✅[/green]")
            else:
                row.append("[dim]—[/dim]")
        table.add_row(*row)

    console.print(table)

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    for reg_key, data in all_mappings.items():
        cats = get_categories_for_regulation(data)
        count = len(cats) if cats else len(AVE_CATEGORIES)
        console.print(f"  {reg_names[reg_key]}: {count} AVE categories mapped")

    # Save to file if requested
    if output:
        matrix_data = {
            "generated": datetime.now().isoformat(),
            "regulations": {},
        }
        for reg_key, data in all_mappings.items():
            cats = get_categories_for_regulation(data)
            matrix_data["regulations"][reg_key] = {
                "name": data.get("regulation", {}).get("name", ""),
                "categories": sorted(cats) if cats else AVE_CATEGORIES,
            }

        with open(output, "w") as f:
            json.dump(matrix_data, f, indent=2)
        console.print(f"\n📄 Matrix saved: {output}")


@cli.command()
@click.option("--regulation", "-r", type=click.Choice(list(REGULATION_FILES.keys())),
              required=True, help="Regulation to generate report for")
@click.option("--system-config", "-c", type=click.Path(exists=True),
              help="System configuration YAML")
@click.option("--output", "-o", type=click.Path(), default="report",
              help="Output directory")
def report(regulation: str, system_config: Optional[str], output: str):
    """Generate a compliance report for a specific regulation."""

    mapping = load_mapping(regulation)
    reg = mapping.get("regulation", {})
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    system = {}
    if system_config:
        with open(system_config) as f:
            system = yaml.safe_load(f) or {}

    report_md = f"""# NAIL Compliance Report — {reg.get('name', regulation)}

**Regulation:** {reg.get('full_title', reg.get('name', ''))}
**Jurisdiction:** {reg.get('jurisdiction', '?')}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**System:** {system.get('name', 'Not specified')}
**Tool Version:** NAIL Compliance Checker v1.0.0

---

## Executive Summary

This report maps the requirements of {reg.get('name', regulation)} to the
NAIL AVE Database and associated tools, identifying:

- Which requirements are addressable via AVE-based testing
- Which AVE categories are relevant to compliance
- Recommended certification tier for full coverage
- Gap analysis and remediation recommendations

## Regulatory Overview

| Field | Value |
|-------|-------|
| **Name** | {reg.get('name', '')} |
| **Jurisdiction** | {reg.get('jurisdiction', '')} |
| **Type** | {reg.get('type', 'regulation')} |
| **URL** | {reg.get('url', '')} |

"""

    # Add article mappings (EU AI Act style)
    if "article_mappings" in mapping:
        report_md += "## Article-to-AVE Mapping\n\n"
        for article in mapping["article_mappings"]:
            report_md += f"### {article.get('article', '?')}: {article.get('title', '?')}\n\n"
            if article.get("obligations"):
                report_md += "**Obligations:**\n"
                for ob in article["obligations"]:
                    report_md += f"- {ob}\n"
            cats = article.get("ave_categories", [])
            if cats:
                cat_str = "All 13 categories" if cats == "all" else ", ".join(cats)
                report_md += f"\n**AVE Categories:** {cat_str}\n"
            if article.get("ave_test_cases"):
                report_md += "\n**AVE Test Cases:**\n"
                for tc in article["ave_test_cases"]:
                    report_md += f"- {tc}\n"
            report_md += "\n"

    # Add section mappings (EO style)
    if "section_mappings" in mapping:
        report_md += "## Section-to-AVE Mapping\n\n"
        for section in mapping["section_mappings"]:
            report_md += f"### §{section.get('section', '?')}: {section.get('title', '?')}\n\n"
            if section.get("requirements"):
                for req in section["requirements"]:
                    report_md += f"- {req}\n"
            if section.get("ave_mapping"):
                report_md += "\n**AVE Mapping:**\n"
                for m in section["ave_mapping"]:
                    report_md += f"- {m}\n"
            report_md += "\n"

    report_md += f"""---

## Recommendations

1. Achieve NAIL Gold certification to cover all AVE categories
2. Maintain up-to-date AVE vulnerability assessments
3. Document all defences using the AVE card defence format
4. Implement longitudinal monitoring for ongoing compliance evidence
5. Subscribe to AVE feeds for real-time vulnerability updates

---

*Generated by NAIL Compliance Checker v1.0.0*
*NAIL Institute — Neuravant AI Limited*
"""

    report_path = output_dir / f"compliance_{regulation}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, "w") as f:
        f.write(report_md)

    console.print(f"[bold green]Compliance report generated:[/bold green] {report_path}")


if __name__ == "__main__":
    cli()
