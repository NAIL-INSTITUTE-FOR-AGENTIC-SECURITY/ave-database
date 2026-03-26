"""
ARTA AVE Card Generator — Converts validated findings into schema-v2
compliant AVE cards with auto AVSS scoring, MITRE/CWE mapping, and
defence recommendations.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# AVSS scoring parameters
# ---------------------------------------------------------------------------

AVSS_WEIGHTS = {
    "exploitability": 0.30,
    "impact": 0.25,
    "scope": 0.20,
    "reproducibility": 0.15,
    "remediation_difficulty": 0.10,
}

EXPLOITABILITY_SCORES = {
    "trivial": 10.0,
    "easy": 8.0,
    "moderate": 6.0,
    "difficult": 4.0,
    "very_difficult": 2.0,
}

IMPACT_SCORES = {
    "catastrophic": 10.0,
    "severe": 8.0,
    "significant": 6.0,
    "moderate": 4.0,
    "minor": 2.0,
    "negligible": 1.0,
}

SCOPE_SCORES = {
    "cross_system": 10.0,
    "multi_agent": 8.0,
    "single_agent": 6.0,
    "single_component": 4.0,
    "isolated": 2.0,
}


# ---------------------------------------------------------------------------
# MITRE ATT&CK / ATLAS mapping
# ---------------------------------------------------------------------------

CATEGORY_TO_MITRE: dict[str, dict[str, str]] = {
    "prompt_injection": {
        "technique_id": "AML.T0051",
        "technique_name": "LLM Prompt Injection",
        "tactic": "Initial Access",
    },
    "tool_abuse": {
        "technique_id": "AML.T0054",
        "technique_name": "LLM Plugin Compromise",
        "tactic": "Execution",
    },
    "memory_poisoning": {
        "technique_id": "AML.T0020",
        "technique_name": "Poisoning Training Data",
        "tactic": "Persistence",
    },
    "identity_spoofing": {
        "technique_id": "T1078",
        "technique_name": "Valid Accounts",
        "tactic": "Defense Evasion",
    },
    "goal_hijacking": {
        "technique_id": "AML.T0048",
        "technique_name": "Command and Control via AI",
        "tactic": "Command and Control",
    },
    "knowledge_poisoning": {
        "technique_id": "AML.T0019",
        "technique_name": "Publish Poisoned Datasets",
        "tactic": "Resource Development",
    },
    "resource_exhaustion": {
        "technique_id": "AML.T0029",
        "technique_name": "Denial of ML Service",
        "tactic": "Impact",
    },
    "output_manipulation": {
        "technique_id": "AML.T0043",
        "technique_name": "Craft Adversarial Data",
        "tactic": "ML Attack Staging",
    },
    "privilege_escalation": {
        "technique_id": "T1068",
        "technique_name": "Exploitation for Privilege Escalation",
        "tactic": "Privilege Escalation",
    },
    "trust_exploitation": {
        "technique_id": "T1199",
        "technique_name": "Trusted Relationship",
        "tactic": "Initial Access",
    },
    "context_overflow": {
        "technique_id": "AML.T0029",
        "technique_name": "Denial of ML Service",
        "tactic": "Impact",
    },
    "model_denial_of_service": {
        "technique_id": "AML.T0029",
        "technique_name": "Denial of ML Service",
        "tactic": "Impact",
    },
    "data_exfiltration": {
        "technique_id": "AML.T0024",
        "technique_name": "Exfiltration via ML Inference API",
        "tactic": "Exfiltration",
    },
    "supply_chain": {
        "technique_id": "AML.T0010",
        "technique_name": "ML Supply Chain Compromise",
        "tactic": "Initial Access",
    },
    "model_poisoning": {
        "technique_id": "AML.T0020",
        "technique_name": "Poisoning Training Data",
        "tactic": "Persistence",
    },
    "multi_agent_coordination": {
        "technique_id": "AML.T0048",
        "technique_name": "Command and Control via AI",
        "tactic": "Lateral Movement",
    },
    "reward_hacking": {
        "technique_id": "AML.T0015",
        "technique_name": "Evade ML Model",
        "tactic": "Defense Evasion",
    },
    "emergent_behavior": {
        "technique_id": "AML.T0047",
        "technique_name": "ML Model Inference API Access",
        "tactic": "Discovery",
    },
}


# ---------------------------------------------------------------------------
# CWE mapping
# ---------------------------------------------------------------------------

CATEGORY_TO_CWE: dict[str, dict[str, str]] = {
    "prompt_injection": {"cwe_id": "CWE-77", "cwe_name": "Command Injection"},
    "tool_abuse": {
        "cwe_id": "CWE-862",
        "cwe_name": "Missing Authorization",
    },
    "memory_poisoning": {
        "cwe_id": "CWE-472",
        "cwe_name": "External Control of Assumed-Immutable Web Parameter",
    },
    "identity_spoofing": {
        "cwe_id": "CWE-290",
        "cwe_name": "Authentication Bypass by Spoofing",
    },
    "goal_hijacking": {
        "cwe_id": "CWE-441",
        "cwe_name": "Unintended Proxy or Intermediary",
    },
    "knowledge_poisoning": {
        "cwe_id": "CWE-502",
        "cwe_name": "Deserialization of Untrusted Data",
    },
    "resource_exhaustion": {
        "cwe_id": "CWE-400",
        "cwe_name": "Uncontrolled Resource Consumption",
    },
    "output_manipulation": {
        "cwe_id": "CWE-838",
        "cwe_name": "Inappropriate Encoding for Output",
    },
    "privilege_escalation": {
        "cwe_id": "CWE-269",
        "cwe_name": "Improper Privilege Management",
    },
    "trust_exploitation": {
        "cwe_id": "CWE-346",
        "cwe_name": "Origin Validation Error",
    },
    "context_overflow": {
        "cwe_id": "CWE-119",
        "cwe_name": "Improper Restriction of Operations within Bounds",
    },
    "model_denial_of_service": {
        "cwe_id": "CWE-770",
        "cwe_name": "Allocation of Resources Without Limits",
    },
    "data_exfiltration": {
        "cwe_id": "CWE-200",
        "cwe_name": "Exposure of Sensitive Information",
    },
    "supply_chain": {
        "cwe_id": "CWE-829",
        "cwe_name": "Inclusion of Functionality from Untrusted Control Sphere",
    },
    "model_poisoning": {
        "cwe_id": "CWE-345",
        "cwe_name": "Insufficient Verification of Data Authenticity",
    },
    "multi_agent_coordination": {
        "cwe_id": "CWE-362",
        "cwe_name": "Concurrent Execution Using Shared Resource",
    },
    "reward_hacking": {
        "cwe_id": "CWE-697",
        "cwe_name": "Incorrect Comparison",
    },
    "emergent_behavior": {
        "cwe_id": "CWE-754",
        "cwe_name": "Improper Check for Unusual or Exceptional Conditions",
    },
}


# ---------------------------------------------------------------------------
# Defence recommendation templates
# ---------------------------------------------------------------------------

DEFENCE_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "prompt_injection": [
        {
            "name": "Input Sanitization",
            "description": "Apply instruction-hierarchy enforcement and input/output boundary markers.",
            "implementation": "Use system-level instruction delimiters and validate user input against injection patterns.",
        },
        {
            "name": "Dual-LLM Pattern",
            "description": "Use a separate privileged LLM for tool execution decisions.",
            "implementation": "Route tool calls through a privileged LLM that only accepts structured commands, not raw user text.",
        },
    ],
    "tool_abuse": [
        {
            "name": "Tool Call Validation",
            "description": "Validate all tool parameters against allowlists before execution.",
            "implementation": "Implement schema-based parameter validation with strict type checking and value constraints.",
        },
        {
            "name": "Least Privilege",
            "description": "Grant agents only the minimum tools required for their task.",
            "implementation": "Use dynamic tool provisioning based on current task context and user authorization level.",
        },
    ],
    "memory_poisoning": [
        {
            "name": "Memory Integrity Checks",
            "description": "Validate memory writes against source authority and content policy.",
            "implementation": "Implement write-ahead logging with content classification before committing to persistent memory.",
        },
    ],
    "trust_exploitation": [
        {
            "name": "Mutual Authentication",
            "description": "Require cryptographic authentication between agents.",
            "implementation": "Use signed JWT tokens with agent identity claims for all inter-agent communication.",
        },
    ],
    "goal_hijacking": [
        {
            "name": "Goal Anchoring",
            "description": "Reinforce primary objective at each reasoning step.",
            "implementation": "Prepend goal reminder to each LLM call and validate output alignment with objective function.",
        },
    ],
    "resource_exhaustion": [
        {
            "name": "Token Budget",
            "description": "Enforce per-request and per-session token budgets.",
            "implementation": "Track cumulative token usage and terminate sessions exceeding configured thresholds.",
        },
    ],
}


# ---------------------------------------------------------------------------
# Card generator
# ---------------------------------------------------------------------------


class AVECardGenerator:
    """Generate AVE v2 schema-compliant cards from ARTA findings."""

    def __init__(self, schema_version: str = "2.0.0"):
        self.schema_version = schema_version

    def compute_avss(
        self,
        exploitability: str = "moderate",
        impact: str = "significant",
        scope: str = "single_agent",
        reproducibility: float = 1.0,
        remediation_difficulty: float = 0.5,
    ) -> dict[str, Any]:
        """Auto-compute AVSS score."""
        e = EXPLOITABILITY_SCORES.get(exploitability, 5.0)
        i = IMPACT_SCORES.get(impact, 5.0)
        s = SCOPE_SCORES.get(scope, 5.0)
        r = min(max(reproducibility * 10, 0), 10)
        rd = min(max(remediation_difficulty * 10, 0), 10)

        raw = (
            AVSS_WEIGHTS["exploitability"] * e
            + AVSS_WEIGHTS["impact"] * i
            + AVSS_WEIGHTS["scope"] * s
            + AVSS_WEIGHTS["reproducibility"] * r
            + AVSS_WEIGHTS["remediation_difficulty"] * rd
        )
        score = round(raw, 1)

        if score >= 9.0:
            severity = "critical"
        elif score >= 7.0:
            severity = "high"
        elif score >= 4.0:
            severity = "medium"
        elif score >= 2.0:
            severity = "low"
        else:
            severity = "info"

        return {
            "version": "1.0",
            "score": score,
            "severity": severity,
            "vector": f"E:{exploitability}/I:{impact}/S:{scope}/R:{reproducibility:.1f}/RD:{remediation_difficulty:.1f}",
            "components": {
                "exploitability": {"value": exploitability, "score": e},
                "impact": {"value": impact, "score": i},
                "scope": {"value": scope, "score": s},
                "reproducibility": {"value": reproducibility, "score": r},
                "remediation_difficulty": {"value": remediation_difficulty, "score": rd},
            },
        }

    def map_mitre(self, category: str) -> dict[str, str]:
        """Map an AVE category to MITRE ATT&CK / ATLAS."""
        return CATEGORY_TO_MITRE.get(
            category,
            {
                "technique_id": "N/A",
                "technique_name": "Unmapped",
                "tactic": "Unknown",
            },
        )

    def map_cwe(self, category: str) -> dict[str, str]:
        """Map an AVE category to CWE."""
        return CATEGORY_TO_CWE.get(
            category,
            {"cwe_id": "N/A", "cwe_name": "Unmapped"},
        )

    def recommend_defences(self, category: str) -> list[dict[str, str]]:
        """Get defence recommendations for a category."""
        return DEFENCE_TEMPLATES.get(
            category,
            [
                {
                    "name": "General Hardening",
                    "description": "Apply defence-in-depth principles.",
                    "implementation": "Review NAIL defence guides for category-specific mitigations.",
                }
            ],
        )

    def generate(
        self,
        finding_id: str,
        category: str,
        title: str,
        description: str,
        severity: str = "medium",
        evidence: list[dict[str, Any]] | None = None,
        poc_code: str = "",
        framework: str = "",
        framework_version: str = "",
        exploitability: str = "moderate",
        impact: str = "significant",
        scope: str = "single_agent",
        reproducibility: float = 1.0,
        remediation_difficulty: float = 0.5,
    ) -> dict[str, Any]:
        """Generate a complete AVE v2 card."""
        now = datetime.now(timezone.utc).isoformat()
        ave_id = f"AVE-DRAFT-{uuid.uuid4().hex[:6].upper()}"

        avss = self.compute_avss(
            exploitability=exploitability,
            impact=impact,
            scope=scope,
            reproducibility=reproducibility,
            remediation_difficulty=remediation_difficulty,
        )
        mitre = self.map_mitre(category)
        cwe = self.map_cwe(category)
        defences = self.recommend_defences(category)

        card: dict[str, Any] = {
            "ave_id": ave_id,
            "schema_version": self.schema_version,
            "title": title,
            "description": description,
            "category": category,
            "status": "draft",
            "severity": avss["severity"],
            "avss": avss,
            "mitre_mapping": mitre,
            "cwe_mapping": cwe,
            "affected_systems": [],
            "references": [],
            "evidence": evidence or [],
            "defences": defences,
            "metadata": {
                "finding_id": finding_id,
                "generated_by": "ARTA",
                "generated_at": now,
                "framework": framework,
                "framework_version": framework_version,
                "review_status": "pending",
            },
            "provenance": {
                "discovered_by": "ARTA (Autonomous Red Team Agent)",
                "discovery_method": "automated_campaign",
                "discovery_date": now,
                "organization": "NAIL Institute for Agentic Security",
            },
            "created_at": now,
            "updated_at": now,
        }

        if poc_code:
            card["proof_of_concept"] = {
                "language": "python",
                "code": poc_code,
                "notes": "Auto-generated PoC — verify in isolated environment.",
            }

        return card

    def to_json(self, card: dict[str, Any], indent: int = 2) -> str:
        """Serialize an AVE card to JSON."""
        return json.dumps(card, indent=indent, ensure_ascii=False)
