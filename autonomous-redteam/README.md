# Autonomous Red Team Agent — AVE Discovery Engine

An AI-powered agent that systematically discovers, validates, and catalogues
new agentic AI vulnerabilities using the AVE taxonomy.

## Overview

The Autonomous Red Team Agent (ARTA) is a self-directed security research agent
that continuously probes agentic AI systems for vulnerabilities, generates
structured AVE cards for confirmed findings, and feeds them into the NAIL review
pipeline.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    ARTA — Core Agent                          │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Recon Module │  │ Exploitation │  │ Validation &     │    │
│  │              │  │ Engine       │  │ Reproduction     │    │
│  │ • Framework  │  │              │  │                  │    │
│  │   analysis   │  │ • Prompt     │  │ • 3-run minimum  │    │
│  │ • Attack     │  │   injection  │  │ • Cross-model    │    │
│  │   surface    │  │ • Tool abuse │  │   verification   │    │
│  │   mapping    │  │ • Trust      │  │ • Environmental  │    │
│  │ • Config     │  │   exploit    │  │   variation      │    │
│  │   review     │  │ • Memory     │  │ • False-positive │    │
│  │              │  │   poison     │  │   elimination    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘    │
│         │                 │                  │                │
│  ┌──────▼─────────────────▼──────────────────▼───────────┐   │
│  │              Orchestrator (LangGraph)                   │  │
│  │  • Campaign planning     • State management             │  │
│  │  • Module coordination   • Safety guardrails            │  │
│  │  • Human-in-the-loop     • Rate limiting                │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │                                     │
│  ┌──────────────────────▼─────────────────────────────────┐  │
│  │              AVE Card Generator                         │  │
│  │  • Schema v2 compliance  • AVSS auto-scoring            │  │
│  │  • MITRE/CWE mapping     • Evidence packaging           │  │
│  │  • PoC code generation   • Defence recommendation       │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │                                     │
└─────────────────────────┼─────────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │  NAIL Review Pipeline  │
              │  • Auto-validation     │
              │  • Peer review queue   │
              │  • Publication         │
              └────────────────────────┘
```

## Campaign Types

### 1. Framework Audit Campaign

Systematically test a specific agent framework for known vulnerability patterns.

| Parameter | Description |
|-----------|-------------|
| **Target** | Agent framework (e.g., LangChain 0.2.x) |
| **Scope** | All 20 AVE categories |
| **Depth** | Comprehensive (all attack vectors per category) |
| **Duration** | 4-8 hours |
| **Output** | AVE cards for all confirmed findings |

### 2. Category Sweep Campaign

Deep-dive into a single vulnerability category across multiple frameworks.

| Parameter | Description |
|-----------|-------------|
| **Target** | Single AVE category (e.g., prompt_injection) |
| **Scope** | All supported frameworks |
| **Depth** | Exhaustive (novel attack variants) |
| **Duration** | 2-4 hours |
| **Output** | Category-specific findings + variant catalogue |

### 3. Multi-Agent Campaign

Test multi-agent topologies for coordination vulnerabilities.

| Parameter | Description |
|-----------|-------------|
| **Target** | Multi-agent system configuration |
| **Scope** | Trust, delegation, coordination, emergent |
| **Depth** | Topology-specific attack patterns |
| **Duration** | 6-12 hours |
| **Output** | Multi-agent AVE cards (v2 schema) |

### 4. Regression Campaign

Re-test previously patched vulnerabilities for regressions.

| Parameter | Description |
|-----------|-------------|
| **Target** | Previously published AVE cards |
| **Scope** | Confirmed mitigations |
| **Depth** | Bypass attempts for each defence |
| **Duration** | 1-2 hours per card |
| **Output** | Regression report + updated card status |

### 5. Continuous Monitoring Campaign

Always-on monitoring for new vulnerability patterns.

| Parameter | Description |
|-----------|-------------|
| **Target** | All configured agent endpoints |
| **Scope** | Lightweight probes across all categories |
| **Depth** | Detection-focused (not exhaustive) |
| **Duration** | Continuous |
| **Output** | Alerts + draft AVE cards for triage |

## Safety & Ethics

### Guardrails

ARTA operates within strict safety boundaries:

- **Scope limitation**: Only tests explicitly authorized targets
- **No production systems**: Dedicated test environments only
- **No data exfiltration**: Findings stay within the NAIL infrastructure
- **Rate limiting**: Maximum probe rate configurable per target
- **Kill switch**: Immediate halt on any guardrail violation
- **Human approval**: Critical actions require human-in-the-loop confirmation
- **Audit trail**: Every action logged with full provenance

### Ethical Framework

```
┌─────────────────────────────────────────┐
│           ARTA Ethical Gates              │
│                                           │
│  Gate 1: Is the target authorized?       │
│     ↓ YES                                 │
│  Gate 2: Is the test within scope?       │
│     ↓ YES                                 │
│  Gate 3: Could this cause real harm?     │
│     ↓ NO                                  │
│  Gate 4: Is the technique proportionate? │
│     ↓ YES                                 │
│  Gate 5: Is logging active?              │
│     ↓ YES                                 │
│  ── PROCEED ──                            │
└─────────────────────────────────────────┘
```

### Responsible Disclosure

All findings follow NAIL's [Security Policy](../SECURITY.md):
1. Finding validated and reproduced
2. AVE card drafted with full evidence
3. Framework maintainer notified (90-day disclosure window)
4. Card published after disclosure period or patch

## Modules

### Reconnaissance Module

```python
class ReconModule:
    """Analyse target agent for attack surface mapping."""

    async def analyse_framework(self, target: AgentTarget) -> AttackSurface:
        """Identify tools, permissions, model, topology."""
        ...

    async def enumerate_tools(self, target: AgentTarget) -> list[ToolProfile]:
        """Catalogue all available tools and their capabilities."""
        ...

    async def map_trust_boundaries(self, target: AgentTarget) -> TrustMap:
        """Identify trust boundaries and delegation chains."""
        ...

    async def assess_guardrails(self, target: AgentTarget) -> GuardrailProfile:
        """Test existing safety mechanisms for weaknesses."""
        ...
```

### Exploitation Engine

```python
class ExploitationEngine:
    """Generate and execute attack payloads against AVE categories."""

    async def run_category(
        self,
        target: AgentTarget,
        category: AVECategory,
        attack_surface: AttackSurface,
    ) -> list[Finding]:
        """Run all attack techniques for a vulnerability category."""
        ...

    async def prompt_injection_suite(self, target: AgentTarget) -> list[Finding]:
        """Comprehensive prompt injection testing."""
        ...

    async def tool_abuse_suite(self, target: AgentTarget) -> list[Finding]:
        """Test for unsafe tool usage patterns."""
        ...

    async def trust_exploitation_suite(self, target: AgentTarget) -> list[Finding]:
        """Test trust boundaries and delegation chains."""
        ...

    async def memory_poisoning_suite(self, target: AgentTarget) -> list[Finding]:
        """Test persistent memory for corruption vectors."""
        ...
```

### Validation Module

```python
class ValidationModule:
    """Validate and reproduce findings to eliminate false positives."""

    async def reproduce(
        self,
        finding: Finding,
        target: AgentTarget,
        runs: int = 3,
    ) -> ReproductionResult:
        """Reproduce a finding N times for confirmation."""
        ...

    async def cross_model_verify(
        self,
        finding: Finding,
        models: list[str],
    ) -> CrossModelResult:
        """Verify finding across multiple LLM models."""
        ...

    async def environmental_variation(
        self,
        finding: Finding,
        variations: list[EnvironmentConfig],
    ) -> EnvironmentResult:
        """Test finding under different environmental conditions."""
        ...
```

### AVE Card Generator

```python
class AVECardGenerator:
    """Generate schema-compliant AVE cards from validated findings."""

    async def generate(
        self,
        finding: ValidatedFinding,
        schema_version: str = "2.0.0",
    ) -> AVECard:
        """Generate a complete AVE card from a validated finding."""
        ...

    async def auto_score_avss(self, finding: ValidatedFinding) -> AVSSScore:
        """Automatically calculate AVSS score based on finding characteristics."""
        ...

    async def map_mitre(self, finding: ValidatedFinding) -> str:
        """Map finding to MITRE ATT&CK / ATLAS technique."""
        ...

    async def map_cwe(self, finding: ValidatedFinding) -> str:
        """Map finding to CWE identifier."""
        ...

    async def generate_poc(self, finding: ValidatedFinding) -> str:
        """Generate proof-of-concept code for the finding."""
        ...

    async def recommend_defences(self, finding: ValidatedFinding) -> list[Defence]:
        """Recommend defences based on finding characteristics."""
        ...
```

## Configuration

```yaml
# arta-config.yaml
agent:
  name: "ARTA-001"
  model: "gpt-4o"
  max_concurrent_probes: 5
  human_in_the_loop: true
  log_level: "INFO"

targets:
  - name: "langchain-test-agent"
    framework: "langchain"
    version: "0.2.x"
    endpoint: "http://localhost:8080/agent"
    authorized: true
    scope:
      categories: "all"
      max_probe_rate: 10  # per minute
      allow_tool_execution: true
      allow_memory_modification: false

campaigns:
  - type: "framework_audit"
    target: "langchain-test-agent"
    categories: "all"
    depth: "comprehensive"
    schedule: "weekly"

  - type: "continuous_monitoring"
    target: "langchain-test-agent"
    categories: ["prompt_injection", "tool_abuse"]
    depth: "lightweight"
    schedule: "always"

safety:
  kill_switch_enabled: true
  max_finding_severity: "critical"
  require_human_approval_above: "high"
  audit_log_path: "./logs/arta-audit.jsonl"
  alert_on_guardrail_violation: true
  alert_channels: ["slack:#arta-alerts", "email:security@nailinstitute.org"]

output:
  ave_schema_version: "2.0.0"
  output_dir: "./findings/"
  auto_submit_to_review: false
  generate_poc: true
  generate_defences: true
```

## Output

### Finding Report

Each campaign produces:

```
findings/
├── campaign-2025-07-01T14-30-00/
│   ├── campaign_summary.json       # Overview, stats, timeline
│   ├── attack_surface.json         # Recon results
│   ├── findings/
│   │   ├── finding-001.json        # Raw finding + evidence
│   │   ├── finding-002.json
│   │   └── ...
│   ├── ave-cards/
│   │   ├── AVE-DRAFT-0001.json    # Generated AVE card (v2)
│   │   ├── AVE-DRAFT-0002.json
│   │   └── ...
│   ├── poc/
│   │   ├── poc-001.py              # Proof of concept scripts
│   │   └── ...
│   └── audit.jsonl                 # Full audit trail
```

### Campaign Summary

```json
{
  "campaign_id": "camp_20250701_143000",
  "type": "framework_audit",
  "target": "langchain-test-agent",
  "started": "2025-07-01T14:30:00Z",
  "completed": "2025-07-01T20:15:00Z",
  "duration_hours": 5.75,
  "categories_tested": 20,
  "probes_executed": 847,
  "findings_raw": 23,
  "findings_validated": 12,
  "findings_false_positive": 11,
  "ave_cards_generated": 12,
  "severity_distribution": {
    "critical": 2,
    "high": 4,
    "medium": 5,
    "low": 1
  },
  "guardrail_violations": 0
}
```

## Requirements

- Python 3.11+
- LangGraph (orchestration)
- OpenAI / Anthropic API access (agent reasoning)
- Redis (state management)
- Docker (isolated test environments)

## Usage

```bash
# Install
pip install nail-arta

# Configure
cp arta-config.example.yaml arta-config.yaml
# Edit config with your targets and API keys

# Run a single campaign
arta run --campaign framework_audit --target langchain-test-agent

# Run continuous monitoring
arta monitor --config arta-config.yaml

# View findings
arta findings list --campaign latest
arta findings show finding-001

# Generate AVE cards from findings
arta generate --finding finding-001 --schema-version 2.0.0

# Submit to NAIL review pipeline
arta submit --campaign latest --auto-validate
```

## Contact

- **Email**: redteam@nailinstitute.org
- **Slack**: `#autonomous-redteam`
- **Responsible Disclosure**: security@nailinstitute.org
