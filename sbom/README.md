# AI-SBOM: Agentic AI Software Bill of Materials

> AVE-aware SBOM extension for agentic AI systems.
> Generates CycloneDX-compatible SBOMs with embedded AVE vulnerability data.

## Overview

Traditional SBOMs track software dependencies. **AI-SBOMs** extend this to
include the agentic AI attack surface: models, tools, memory backends,
prompt templates, and inter-agent communication channels — each mapped to
relevant AVE vulnerabilities.

## Quick Start

```bash
# Generate an AI-SBOM for your project
python scripts/ai_sbom_generator.py --project ./my-agent-app --output sbom.json

# Scan an existing SBOM against the AVE database
python scripts/ai_sbom_generator.py --scan sbom.json
```

## AI-SBOM Schema Extensions

We extend [CycloneDX v1.5](https://cyclonedx.org/) with agentic AI components:

### Component Types

| Type | Description | Example |
|------|-------------|---------|
| `ai-model` | LLM or ML model | `gpt-4o`, `claude-3.5-sonnet` |
| `ai-agent` | Autonomous agent | `researcher-agent`, `coder-agent` |
| `ai-tool` | Tool/function callable by agents | `web-search`, `code-exec` |
| `ai-memory` | Memory/context backend | `chromadb`, `pinecone` |
| `ai-prompt` | Prompt template or system message | `system-prompt-v2.1` |
| `ai-channel` | Inter-agent communication channel | `crew-broadcast`, `mcp-pipe` |
| `ai-guardrail` | Safety/alignment guardrail | `content-filter`, `rate-limiter` |

### AVE Vulnerability Mapping

Each component includes an `ave-exposure` field listing relevant AVE cards:

```json
{
  "type": "ai-memory",
  "name": "chromadb",
  "version": "0.4.22",
  "ave-exposure": [
    {
      "ave_id": "AVE-2025-0009",
      "name": "Epistemic Contagion",
      "severity": "critical",
      "mitre": "ATT&CK: T1080 | ATLAS: AML.T0020",
      "mitigated": false,
      "mitigation_notes": ""
    },
    {
      "ave_id": "AVE-2025-0034",
      "name": "Federated Poisoning in Multi-Tenant Systems",
      "severity": "critical",
      "mitre": "ATT&CK: T1080 | ATLAS: AML.T0020",
      "mitigated": true,
      "mitigation_notes": "Tenant isolation via collection namespacing"
    }
  ]
}
```

## Usage

### Generate AI-SBOM

```python
from ai_sbom_generator import AIBOMGenerator

generator = AIBOMGenerator(
    project_name="My Agent Platform",
    version="1.0.0",
    ave_database_path="./ave-database/cards",
)

# Add components
generator.add_model("gpt-4o", provider="openai", version="2024-08-06")
generator.add_agent("researcher", framework="crewai", role="research")
generator.add_tool("web-search", provider="tavily", permissions=["network"])
generator.add_memory("chromadb", version="0.4.22", isolation="tenant")
generator.add_prompt("system-v2", hash="sha256:abc123...")
generator.add_guardrail("rate-limiter", type="token-budget", threshold=10000)

# Generate with AVE mapping
sbom = generator.generate()
generator.save("ai-sbom.json")
```

### Scan for Vulnerabilities

```python
from ai_sbom_generator import AIBOMScanner

scanner = AIBOMScanner(ave_database_path="./ave-database/cards")
results = scanner.scan("ai-sbom.json")

print(f"Components: {results.total_components}")
print(f"AVE Exposures: {results.total_exposures}")
print(f"Critical: {results.critical_count}")
print(f"Unmitigated: {results.unmitigated_count}")
```

## Integration

### GitHub Actions

```yaml
- name: Generate AI-SBOM
  run: python scripts/ai_sbom_generator.py --project . --output ai-sbom.json

- name: Scan AI-SBOM
  run: python scripts/ai_sbom_generator.py --scan ai-sbom.json --fail-on critical
```

### CI/CD Pipeline

```bash
# Fail build if unmitigated critical AVEs exist
python scripts/ai_sbom_generator.py --scan ai-sbom.json \
  --fail-on critical \
  --fail-on-unmitigated
```

## License

CC-BY-SA-4.0 — [NAIL Institute](https://nailinstitute.org)
