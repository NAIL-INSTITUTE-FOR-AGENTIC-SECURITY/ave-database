#!/usr/bin/env python3
"""
AI-SBOM Generator

Generates CycloneDX-compatible Software Bill of Materials with
agentic AI component extensions and AVE vulnerability mapping.

Usage:
    python ai_sbom_generator.py --project ./my-app --output sbom.json
    python ai_sbom_generator.py --scan sbom.json
    python ai_sbom_generator.py --scan sbom.json --fail-on critical
"""

import json
import glob
import os
import sys
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

# ---------------------------------------------------------------------------
# AVE Database Loader
# ---------------------------------------------------------------------------

def load_ave_database(cards_dir: str) -> dict[str, dict]:
    """Load all AVE cards indexed by ID."""
    db = {}
    for f in glob.glob(os.path.join(cards_dir, "*.json")):
        try:
            card = json.load(open(f))
            db[card["ave_id"]] = card
        except (json.JSONDecodeError, KeyError):
            pass
    return db


# Component-to-AVE mapping rules
COMPONENT_AVE_MAP = {
    "ai-model": [
        "AVE-2025-0004",  # Prompt Inbreeding
        "AVE-2025-0010",  # Clever Hans
        "AVE-2025-0012",  # Sycophantic Collapse
        "AVE-2025-0024",  # Deceptive Alignment
        "AVE-2025-0035",  # Attention Smoothing
    ],
    "ai-agent": [
        "AVE-2025-0002",  # Consensus Paralysis
        "AVE-2025-0005",  # CYA Cascade
        "AVE-2025-0007",  # Goodhart's Cartel
        "AVE-2025-0008",  # Learned Helplessness
        "AVE-2025-0015",  # Observer Effect
        "AVE-2025-0021",  # Algorithmic Bystander Effect
        "AVE-2025-0025",  # Agent Collusion
        "AVE-2025-0046",  # Emergent Collusion
        "AVE-2025-0050",  # Multi-Turn Identity Confusion
    ],
    "ai-tool": [
        "AVE-2025-0014",  # MCP Tool Registration Poisoning
        "AVE-2025-0026",  # Confused Deputy Attack
        "AVE-2025-0032",  # Multi-Hop Tool Chain Exploitation
    ],
    "ai-memory": [
        "AVE-2025-0001",  # Sleeper Payload Injection
        "AVE-2025-0009",  # Epistemic Contagion
        "AVE-2025-0022",  # Memory Laundering
        "AVE-2025-0034",  # Federated Poisoning
        "AVE-2025-0045",  # Memory Provenance Laundering
    ],
    "ai-prompt": [
        "AVE-2025-0030",  # Semantic Trojan Horse
        "AVE-2025-0033",  # Jailbreak Chaining
        "AVE-2025-0037",  # Semantic Prompt Smuggling
        "AVE-2025-0048",  # Context Window Boundary Attack
    ],
    "ai-channel": [
        "AVE-2025-0027",  # Shadow Delegation
        "AVE-2025-0039",  # Cross-Agent Belief Propagation
        "AVE-2025-0040",  # Authority Gradient Exploitation
        "AVE-2025-0043",  # Sycophantic Compliance Cascade
    ],
    "ai-guardrail": [
        "AVE-2025-0018",  # Somatic Blindness
        "AVE-2025-0020",  # Multi-Pathology Compound Attack
        "AVE-2025-0036",  # Errors of Omission
    ],
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class AVEExposure:
    ave_id: str
    name: str
    severity: str
    mitre: str
    mitigated: bool = False
    mitigation_notes: str = ""


@dataclass
class AIComponent:
    type: str
    name: str
    version: str = ""
    provider: str = ""
    properties: dict = field(default_factory=dict)
    ave_exposure: list[AVEExposure] = field(default_factory=list)


@dataclass
class ScanResult:
    total_components: int = 0
    total_exposures: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    unmitigated_count: int = 0
    components: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class AIBOMGenerator:
    """Generate CycloneDX-compatible AI-SBOM."""

    def __init__(
        self,
        project_name: str,
        version: str = "1.0.0",
        ave_database_path: str = "",
    ):
        self.project_name = project_name
        self.version = version
        self.components: list[AIComponent] = []
        self.ave_db = {}
        if ave_database_path:
            self.ave_db = load_ave_database(ave_database_path)

    def _map_ave_exposures(self, component_type: str) -> list[AVEExposure]:
        """Map component type to relevant AVE exposures."""
        ave_ids = COMPONENT_AVE_MAP.get(component_type, [])
        exposures = []
        for ave_id in ave_ids:
            card = self.ave_db.get(ave_id, {})
            if card:
                exposures.append(AVEExposure(
                    ave_id=ave_id,
                    name=card.get("name", ""),
                    severity=card.get("severity", "unknown"),
                    mitre=card.get("mitre_mapping", ""),
                ))
        return exposures

    def add_model(self, name: str, **kwargs) -> AIComponent:
        comp = AIComponent(type="ai-model", name=name, **kwargs)
        comp.ave_exposure = self._map_ave_exposures("ai-model")
        self.components.append(comp)
        return comp

    def add_agent(self, name: str, **kwargs) -> AIComponent:
        comp = AIComponent(type="ai-agent", name=name, **kwargs)
        comp.ave_exposure = self._map_ave_exposures("ai-agent")
        self.components.append(comp)
        return comp

    def add_tool(self, name: str, **kwargs) -> AIComponent:
        comp = AIComponent(type="ai-tool", name=name, **kwargs)
        comp.ave_exposure = self._map_ave_exposures("ai-tool")
        self.components.append(comp)
        return comp

    def add_memory(self, name: str, **kwargs) -> AIComponent:
        comp = AIComponent(type="ai-memory", name=name, **kwargs)
        comp.ave_exposure = self._map_ave_exposures("ai-memory")
        self.components.append(comp)
        return comp

    def add_prompt(self, name: str, **kwargs) -> AIComponent:
        comp = AIComponent(type="ai-prompt", name=name, **kwargs)
        comp.ave_exposure = self._map_ave_exposures("ai-prompt")
        self.components.append(comp)
        return comp

    def add_channel(self, name: str, **kwargs) -> AIComponent:
        comp = AIComponent(type="ai-channel", name=name, **kwargs)
        comp.ave_exposure = self._map_ave_exposures("ai-channel")
        self.components.append(comp)
        return comp

    def add_guardrail(self, name: str, **kwargs) -> AIComponent:
        comp = AIComponent(type="ai-guardrail", name=name, **kwargs)
        comp.ave_exposure = self._map_ave_exposures("ai-guardrail")
        self.components.append(comp)
        return comp

    def generate(self) -> dict:
        """Generate CycloneDX-compatible AI-SBOM."""
        now = datetime.now(timezone.utc).isoformat()
        serial = hashlib.sha256(
            f"{self.project_name}:{self.version}:{now}".encode()
        ).hexdigest()[:16]

        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:nail-{serial}",
            "version": 1,
            "metadata": {
                "timestamp": now,
                "tools": [{
                    "vendor": "NAIL Institute",
                    "name": "ai-sbom-generator",
                    "version": "1.0.0",
                }],
                "component": {
                    "type": "application",
                    "name": self.project_name,
                    "version": self.version,
                },
                "properties": [{
                    "name": "nail:sbom-type",
                    "value": "ai-sbom",
                }, {
                    "name": "nail:ave-database-version",
                    "value": f"{len(self.ave_db)} cards",
                }],
            },
            "components": [self._component_to_dict(c) for c in self.components],
            "vulnerabilities": self._collect_vulnerabilities(),
        }

        return sbom

    def _component_to_dict(self, comp: AIComponent) -> dict:
        d = {
            "type": "library",
            "name": comp.name,
            "version": comp.version or "unknown",
            "properties": [
                {"name": "nail:component-type", "value": comp.type},
            ],
        }
        if comp.provider:
            d["properties"].append(
                {"name": "nail:provider", "value": comp.provider}
            )
        if comp.ave_exposure:
            d["properties"].append({
                "name": "nail:ave-exposure-count",
                "value": str(len(comp.ave_exposure)),
            })
        return d

    def _collect_vulnerabilities(self) -> list[dict]:
        """Collect all unique AVE exposures as CycloneDX vulnerabilities."""
        seen = set()
        vulns = []
        for comp in self.components:
            for exp in comp.ave_exposure:
                if exp.ave_id not in seen:
                    seen.add(exp.ave_id)
                    vuln = {
                        "id": exp.ave_id,
                        "source": {
                            "name": "NAIL AVE Database",
                            "url": f"https://api.nailinstitute.org/api/v2/ave/{exp.ave_id}",
                        },
                        "description": exp.name,
                        "ratings": [{
                            "severity": exp.severity,
                            "source": {"name": "NAIL AVSS"},
                        }],
                        "properties": [],
                    }
                    if exp.mitre:
                        vuln["properties"].append({
                            "name": "nail:mitre-mapping",
                            "value": exp.mitre,
                        })
                    vulns.append(vuln)
        return vulns

    def save(self, path: str):
        sbom = self.generate()
        with open(path, "w") as f:
            json.dump(sbom, f, indent=2)
        print(f"AI-SBOM saved to {path}")
        print(f"  Components: {len(self.components)}")
        print(f"  Vulnerabilities: {len(sbom['vulnerabilities'])}")


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class AIBOMScanner:
    """Scan an AI-SBOM against the AVE database."""

    def __init__(self, ave_database_path: str = ""):
        self.ave_db = {}
        if ave_database_path:
            self.ave_db = load_ave_database(ave_database_path)

    def scan(self, sbom_path: str) -> ScanResult:
        with open(sbom_path, "r") as f:
            sbom = json.load(f)

        result = ScanResult()
        result.total_components = len(sbom.get("components", []))

        vulns = sbom.get("vulnerabilities", [])
        result.total_exposures = len(vulns)

        for v in vulns:
            severity = ""
            for rating in v.get("ratings", []):
                severity = rating.get("severity", "")

            if severity == "critical":
                result.critical_count += 1
            elif severity == "high":
                result.high_count += 1
            elif severity == "medium":
                result.medium_count += 1

            # Check mitigation status
            mitigated = False
            for prop in v.get("properties", []):
                if prop.get("name") == "nail:mitigated":
                    mitigated = prop.get("value") == "true"
            if not mitigated:
                result.unmitigated_count += 1

        return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI-SBOM Generator & Scanner")
    parser.add_argument("--project", help="Project directory to scan")
    parser.add_argument("--output", "-o", help="Output SBOM path", default="ai-sbom.json")
    parser.add_argument("--scan", help="Scan an existing SBOM file")
    parser.add_argument("--fail-on", choices=["critical", "high", "medium"],
                        help="Fail if vulnerabilities of this severity exist")
    parser.add_argument("--fail-on-unmitigated", action="store_true",
                        help="Fail if unmitigated critical vulns exist")
    parser.add_argument("--ave-db", default="",
                        help="Path to AVE database cards directory")
    args = parser.parse_args()

    # Auto-detect AVE database
    ave_db = args.ave_db
    if not ave_db:
        for candidate in [
            os.path.join(os.path.dirname(__file__), "..", "ave-database", "cards"),
            "./ave-database/cards",
        ]:
            if os.path.isdir(candidate):
                ave_db = candidate
                break

    if args.scan:
        scanner = AIBOMScanner(ave_database_path=ave_db)
        result = scanner.scan(args.scan)

        print(f"AI-SBOM Scan Results")
        print(f"{'='*40}")
        print(f"Components:    {result.total_components}")
        print(f"AVE Exposures: {result.total_exposures}")
        print(f"  Critical:    {result.critical_count}")
        print(f"  High:        {result.high_count}")
        print(f"  Medium:      {result.medium_count}")
        print(f"  Unmitigated: {result.unmitigated_count}")

        if args.fail_on:
            threshold = {"critical": 0, "high": 1, "medium": 2}
            level = threshold.get(args.fail_on, 0)
            counts = [result.critical_count, result.high_count, result.medium_count]
            if any(counts[i] > 0 for i in range(level + 1)):
                print(f"\nFAILED: Found {args.fail_on}+ severity vulnerabilities")
                sys.exit(1)

        if args.fail_on_unmitigated and result.unmitigated_count > 0:
            print(f"\nFAILED: {result.unmitigated_count} unmitigated vulnerabilities")
            sys.exit(1)

        print("\nScan complete ✓")

    elif args.project:
        generator = AIBOMGenerator(
            project_name=os.path.basename(os.path.abspath(args.project)),
            version="1.0.0",
            ave_database_path=ave_db,
        )

        # Auto-detect components from project structure
        project = Path(args.project)

        # Check for common AI framework files
        if list(project.rglob("*crewai*")) or list(project.rglob("*crew*")):
            generator.add_agent("crewai-agents", provider="crewai")
        if list(project.rglob("*langchain*")):
            generator.add_agent("langchain-agents", provider="langchain")
        if list(project.rglob("*autogen*")):
            generator.add_agent("autogen-agents", provider="microsoft")
        if list(project.rglob("*llama_index*")) or list(project.rglob("*llamaindex*")):
            generator.add_memory("llamaindex-rag", provider="llamaindex")
        if list(project.rglob("*chromadb*")) or list(project.rglob("*chroma*")):
            generator.add_memory("chromadb", provider="chroma")
        if list(project.rglob("*openai*")):
            generator.add_model("openai-model", provider="openai")
        if list(project.rglob("*anthropic*")):
            generator.add_model("anthropic-model", provider="anthropic")

        if not generator.components:
            print("No AI components auto-detected. Add components manually.")
            generator.add_agent("generic-agent", provider="unknown")

        generator.save(args.output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
