# AVE-RFC-0001: Agentic Vulnerability Enumeration — Card Format Specification

| Field | Value |
|-------|-------|
| **RFC Number** | AVE-RFC-0001 |
| **Title** | Agentic Vulnerability Enumeration Card Format |
| **Status** | Draft |
| **Created** | 2026-03-25 |
| **Authors** | NAIL Institute |
| **Requires** | — |
| **Replaces** | — |
| **Schema Version** | 1.0.0 |
| **License** | CC-BY-SA-4.0 |

---

## Abstract

This document defines the formal specification for the Agentic Vulnerability Enumeration (AVE) card format — a structured, machine-readable representation of vulnerabilities specific to autonomous AI agent systems. The AVE format provides a standardised way to document, share, and reason about security weaknesses in agentic AI, including multi-agent orchestration, tool use, memory systems, delegation chains, and goal-directed behaviour.

## 1. Introduction

### 1.1 Motivation

Existing vulnerability databases (CVE, CWE, NVD) were designed for software and hardware vulnerabilities. They lack the expressive power to describe failure modes unique to autonomous AI agents:

- **Goal drift** — agents deviating from intended objectives over time
- **Prompt injection** — adversarial inputs that hijack agent control flow
- **Tool misuse** — agents using legitimate tools for unintended purposes
- **Delegation abuse** — exploiting multi-agent delegation chains
- **Memory poisoning** — corrupting agent knowledge stores
- **Authority escalation** — agents acquiring capabilities beyond their mandate

The AVE format fills this gap with a purpose-built schema that captures agent-specific context, evidence from controlled experiments, and defence mappings.

### 1.2 Scope

This specification defines:

- The required and optional fields of an AVE card
- Data types, constraints, and validation rules for each field
- The AVE identifier format
- Enumerated values for categories, severities, and statuses
- The AVSS (Agentic Vulnerability Scoring System) sub-schema
- Evidence and defence sub-schemas
- Metadata and versioning requirements
- Companion Markdown format requirements

### 1.3 Terminology

| Term | Definition |
|------|-----------|
| **AVE Card** | A single vulnerability record in JSON format |
| **AVE ID** | Unique identifier in the format `AVE-YYYY-NNNN` |
| **AVSS** | Agentic Vulnerability Scoring System — numeric risk scoring |
| **Blast Radius** | Description of the downstream impact of the vulnerability |
| **Mechanism** | Technical description of how the vulnerability is exploited |

### 1.4 Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## 2. AVE Identifier

### 2.1 Format

```
AVE-YYYY-NNNN
```

Where:
- `AVE` — Fixed prefix (literal string)
- `YYYY` — Four-digit year of initial discovery or registration
- `NNNN` — Four-digit sequential number, zero-padded

### 2.2 Rules

- The AVE ID MUST be globally unique within the AVE Database
- The year component MUST reflect the year the vulnerability was first documented
- Sequential numbers MUST NOT be reused, even if a card is deprecated
- The full identifier MUST match the regex: `^AVE-\d{4}-\d{4}$`

### 2.3 Examples

```
AVE-2025-0001    # First card registered in 2025
AVE-2025-0050    # Fiftieth card in 2025
AVE-2026-0001    # First card in 2026
```

## 3. Card Schema

### 3.1 Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ave_id` | string | REQUIRED | Unique identifier (Section 2) |
| `name` | string | REQUIRED | Human-readable vulnerability name |
| `aliases` | array\<string\> | OPTIONAL | Alternative names or common references |
| `category` | string (enum) | REQUIRED | Vulnerability category (Section 4) |
| `severity` | string (enum) | REQUIRED | Severity level (Section 5) |
| `status` | string (enum) | REQUIRED | Publication status (Section 6) |
| `summary` | string | REQUIRED | Plain-language description (≤500 chars RECOMMENDED) |
| `mechanism` | string | REQUIRED | Technical exploitation mechanism |
| `blast_radius` | string | REQUIRED | Downstream impact description |
| `prerequisite` | string | REQUIRED | Conditions required for exploitation |
| `environment` | object | REQUIRED | Environment specification (Section 7) |
| `evidence` | array\<object\> | REQUIRED | Experimental evidence (Section 8) |
| `defences` | array | REQUIRED | Known mitigations (Section 9) |
| `date_discovered` | string | REQUIRED | Discovery date (YYYY-MM or YYYY-MM-DD) |
| `date_published` | string | OPTIONAL | Publication date (YYYY-MM-DD or empty) |
| `cwe_mapping` | string | OPTIONAL | Related CWE identifier(s) |
| `mitre_mapping` | string | OPTIONAL | Related MITRE ATT&CK / ATLAS technique(s) |
| `references` | array\<string\> | OPTIONAL | External URLs, papers, advisories |
| `related_aves` | array\<string\> | OPTIONAL | Related AVE IDs |
| `avss_score` | object | REQUIRED | AVSS scoring (Section 10) |
| `poc` | string \| null | OPTIONAL | Proof of concept reference or description |
| `timeline` | string \| null | OPTIONAL | Discovery-to-disclosure timeline |
| `_meta` | object | REQUIRED | Card metadata (Section 11) |
| `contributor` | string | REQUIRED | Primary contributor identifier |

### 3.2 String Constraints

- `name` MUST be 3–200 characters
- `summary` SHOULD be ≤500 characters; MUST be ≤2000 characters
- `mechanism` MUST be non-empty
- `blast_radius` MUST be non-empty
- `prerequisite` MUST be non-empty
- All string fields MUST be UTF-8 encoded

### 3.3 Null Handling

- Fields marked OPTIONAL MAY be `null`, an empty string `""`, or omitted entirely
- Fields marked REQUIRED MUST NOT be `null` (but MAY be empty string where noted)
- Array fields MUST be present; they MAY be empty arrays `[]`

## 4. Categories

The `category` field MUST be one of the following enumerated values:

| Value | Description |
|-------|-------------|
| `prompt_injection` | Adversarial inputs that hijack agent control flow |
| `goal_drift` | Agent deviating from intended objectives |
| `tool_misuse` | Using legitimate tools for unintended purposes |
| `memory` | Corrupting or manipulating agent memory/knowledge |
| `delegation` | Exploiting multi-agent delegation chains |
| `authority` | Unauthorized capability escalation |
| `output_manipulation` | Manipulating agent outputs or responses |
| `model_extraction` | Extracting model weights, prompts, or training data |
| `supply_chain` | Compromising agent dependencies or plugins |
| `denial_of_service` | Disrupting agent availability or performance |
| `information_disclosure` | Unintended leakage of sensitive information |
| `consensus` | Exploiting multi-agent voting or consensus mechanisms |
| `monitoring_evasion` | Evading safety monitors or oversight systems |

### 4.1 Category Extension

New categories MAY be proposed via the RFC process (see Advisory Board Charter). A new category:

- MUST be approved by Advisory Board supermajority (5/7)
- MUST include at least 2 documented vulnerabilities
- MUST NOT overlap significantly with existing categories
- MUST include a clear definition and scope statement

## 5. Severity Levels

The `severity` field MUST be one of:

| Value | AVSS Range | Description |
|-------|-----------|-------------|
| `critical` | 9.0–10.0 | Complete agent compromise or cascading multi-agent failure |
| `high` | 7.0–8.9 | Significant capability bypass or data exfiltration |
| `medium` | 4.0–6.9 | Partial control deviation or limited information leak |
| `low` | 0.1–3.9 | Minor behavioural anomaly with limited impact |
| `informational` | 0.0 | Theoretical or not yet demonstrated |

## 6. Status Values

The `status` field MUST be one of:

| Value | Description |
|-------|-------------|
| `published` | Publicly available, reviewed and accepted |
| `draft` | Under development, not yet reviewed |
| `deprecated` | Superseded or no longer relevant |
| `under-review` | Submitted and awaiting review |
| `proven` | Experimentally verified with evidence |
| `proven_mitigated` | Proven but effective defences exist |
| `not_proven` | Tested but could not be reproduced |
| `theoretical` | Hypothesised but not yet tested |

### 6.1 Status Transitions

```
draft → under-review → published
                     → not_proven
                     → proven → proven_mitigated
                              → deprecated
published → deprecated
theoretical → under-review (when evidence submitted)
```

## 7. Environment Object

The `environment` field MUST be an object with the following structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `frameworks` | array\<string\> | REQUIRED | Agent frameworks tested (e.g., "LangGraph", "CrewAI") |
| `models_tested` | array\<string\> | REQUIRED | LLM models tested |
| `multi_agent` | boolean | REQUIRED | Whether multi-agent setup is required |
| `tools_required` | boolean | REQUIRED | Whether tool access is required |
| `memory_required` | boolean | REQUIRED | Whether persistent memory is required |

### 7.1 Extension

Implementations MAY add additional fields to the environment object. Additional fields SHOULD be documented in the card's mechanism or summary.

## 8. Evidence Array

Each element in the `evidence` array MUST conform to:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `experiment_id` | string | REQUIRED | Unique experiment reference |
| `key_metric` | string | REQUIRED | Primary measured metric name |
| `key_value` | string \| number | REQUIRED | Primary metric value |
| `data_file` | string | OPTIONAL | Path or URL to raw data |
| `p_value` | number \| null | OPTIONAL | Statistical significance (if applicable) |
| `sample_size` | integer \| null | OPTIONAL | Number of experimental runs |
| `cross_model` | boolean | REQUIRED | Whether tested across multiple models |

### 8.1 Evidence Standards

- Evidence SHOULD include `p_value` when statistical testing is performed
- Evidence from community reproductions SHOULD be appended, not replaced
- `experiment_id` SHOULD reference a reproducible experiment configuration
- Cards with status `proven` MUST have at least 1 evidence entry with `key_value` ≠ null

## 9. Defences Array

Each element in the `defences` array MUST be either:

**String format** (simple):
```json
"Input validation with prompt boundary markers"
```

**Object format** (detailed):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | REQUIRED | Defence name |
| `layer` | string | OPTIONAL | Defence layer (e.g., "input", "runtime", "output") |
| `effectiveness` | string \| number | OPTIONAL | Measured effectiveness |
| `rmap_module` | string | OPTIONAL | NAIL RMAP module reference |
| `nail_monitor_detector` | string | OPTIONAL | NAIL Monitor detector ID |

### 9.1 Defence Layers

When specified, `layer` SHOULD be one of:
- `input` — Pre-processing defence
- `runtime` — Active monitoring during execution
- `output` — Post-processing validation
- `architectural` — System design pattern
- `policy` — Governance or access control

## 10. AVSS Score Object

The `avss_score` field MUST be an object with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `overall_score` | number | REQUIRED | Final composite score (0.0–10.0) |
| `severity_label` | string | REQUIRED | Must match `severity` field |
| `vector_string` | string | OPTIONAL | AVSS vector notation |
| `base_score` | number \| null | OPTIONAL | Base exploitability score |
| `temporal_score` | number \| null | OPTIONAL | Time-dependent factors |
| `agentic_score` | number \| null | OPTIONAL | Agent-specific factors |
| `vector` | object \| null | OPTIONAL | Decomposed vector components |

### 10.1 Score Calculation

The AVSS scoring system considers:

- **Base metrics:** Attack complexity, access requirements, user interaction
- **Agentic metrics:** Autonomy level, delegation depth, tool access scope
- **Temporal metrics:** Exploit maturity, remediation level, report confidence
- **Impact metrics:** Confidentiality, integrity, availability, goal alignment

The `overall_score` MUST be calculated as:

$$\text{AVSS} = \text{Base} \times \text{Agentic Modifier} \times \text{Temporal Modifier}$$

Where all modifiers are in the range [0.0, 1.5].

### 10.2 Constraints

- `overall_score` MUST be in range [0.0, 10.0]
- `severity_label` MUST correspond to the ranges defined in Section 5
- If `overall_score` is 0.0, `severity_label` MUST be `"informational"`

## 11. Metadata Object

The `_meta` field MUST contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | REQUIRED | Semantic version of this spec (e.g., "1.0.0") |
| `generated_at` | string | REQUIRED | ISO 8601 timestamp |
| `generator` | string | REQUIRED | Tool or process that created the card |
| `license` | string | REQUIRED | SPDX license identifier |
| `access_tier` | string | REQUIRED | "public", "partner", or "enterprise" |
| `redacted_fields` | array\<string\> | OPTIONAL | Fields with redacted content |
| `full_access` | string | OPTIONAL | URL for unredacted version |

### 11.1 Schema Versioning

- Schema versions follow [Semantic Versioning 2.0.0](https://semver.org/)
- **Major** version: Breaking changes to required fields
- **Minor** version: New optional fields or enum values
- **Patch** version: Clarifications, typo fixes

## 12. File Format

### 12.1 JSON Card

- File name: `{AVE-ID}.json` (e.g., `AVE-2025-0001.json`)
- Encoding: UTF-8
- Root element: single JSON object
- MUST validate against the JSON Schema (Section 14)
- Pretty-printed with 2-space indentation RECOMMENDED

### 12.2 Companion Markdown

Each JSON card SHOULD have a companion Markdown file:

- File name: `{AVE-ID}.md` (e.g., `AVE-2025-0001.md`)
- MUST include: title, summary, category badge, severity badge, mechanism, defences
- SHOULD include: mermaid diagrams, evidence tables, MITRE mapping links
- Used for human-readable documentation and GitHub rendering

### 12.3 Directory Structure

```
ave-database/
└── cards/
    ├── AVE-2025-0001.json
    ├── AVE-2025-0001.md
    ├── AVE-2025-0002.json
    ├── AVE-2025-0002.md
    └── ...
```

## 13. Validation

### 13.1 Required Checks

An AVE card validator MUST verify:

1. `ave_id` matches the filename
2. `ave_id` matches the format `AVE-YYYY-NNNN`
3. `category` is a valid enum value (Section 4)
4. `severity` is a valid enum value (Section 5)
5. `status` is a valid enum value (Section 6)
6. `avss_score.severity_label` matches `severity`
7. `_meta.schema_version` is a valid semver string
8. `_meta.generated_at` is a valid ISO 8601 timestamp
9. All REQUIRED fields are present and non-null
10. `environment` contains all required boolean fields
11. `evidence` entries have required fields if array is non-empty
12. `related_aves` entries match AVE ID format

### 13.2 Advisory Checks

A validator SHOULD additionally warn when:

- `summary` exceeds 500 characters
- `status` is `proven` but `evidence` array is empty
- `avss_score.overall_score` is outside the range for `severity_label`
- `date_discovered` is in the future
- `references` array is empty for `published` cards

## 14. JSON Schema

The normative JSON Schema for AVE cards is maintained at:

```
standards/ave-spec/ave-card.schema.json
```

Implementations MUST validate against this schema before accepting a card.

## 15. Security Considerations

### 15.1 Redaction

Cards MAY contain redacted fields (marked in `_meta.redacted_fields`). Redacted content:

- MUST be replaced with `"[Available in NAIL SDK]"` or similar placeholder
- MUST NOT reveal exploitation details in public-tier cards
- SHALL follow the NAIL Institute Responsible Disclosure policy

### 15.2 Access Tiers

| Tier | Audience | Content |
|------|----------|---------|
| `public` | Everyone | Summary, category, severity, defences |
| `partner` | NAIL Partners | Above + mechanism details, evidence data |
| `enterprise` | Enterprise customers | Full card including PoC, raw data |

### 15.3 Injection Prevention

Card content (especially `mechanism`, `poc`, `summary`) MUST be treated as untrusted input when rendered in web interfaces or processed by automated tools.

## 16. IANA Considerations

This specification does not require any IANA registrations.

## 17. References

- [CVE — Common Vulnerabilities and Exposures](https://cve.mitre.org/)
- [CWE — Common Weakness Enumeration](https://cwe.mitre.org/)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [CVSS v3.1 Specification](https://www.first.org/cvss/v3.1/specification-document)
- [JSON Schema](https://json-schema.org/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [RFC 2119 — Key Words](https://www.ietf.org/rfc/rfc2119.txt)
- [SPDX License List](https://spdx.org/licenses/)

## 18. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-25 | Initial specification |

---

## Appendix A: Complete Example

```json
{
  "ave_id": "AVE-2025-0001",
  "name": "Sleeper Payload Injection",
  "aliases": ["Memory Poisoning", "Delayed Payload Injection"],
  "category": "memory",
  "severity": "critical",
  "status": "proven_mitigated",
  "summary": "Attacker plants false facts in shared agent memory. The agent stores them as trusted ground truth. Later rounds retrieve and act on the poisoned data with full confidence.",
  "mechanism": "Adversarial input is crafted to look like legitimate knowledge.",
  "blast_radius": "Complete corruption of agent knowledge base. All downstream decisions tainted.",
  "prerequisite": "Agent must have writable shared memory or persistent state.",
  "environment": {
    "frameworks": ["LangGraph"],
    "models_tested": ["GPT-4o"],
    "multi_agent": true,
    "tools_required": false,
    "memory_required": true
  },
  "evidence": [
    {
      "experiment_id": "EXP-001",
      "key_metric": "acceptance_rate",
      "key_value": 0.94,
      "data_file": "",
      "p_value": null,
      "sample_size": 100,
      "cross_model": false
    }
  ],
  "defences": [
    {
      "name": "Memory Firewall (Archivist)",
      "layer": "runtime",
      "effectiveness": "0.87",
      "rmap_module": "",
      "nail_monitor_detector": ""
    }
  ],
  "date_discovered": "2025-01",
  "date_published": "2025-03-18",
  "cwe_mapping": "CWE-1321",
  "mitre_mapping": "ATT&CK: T1027, T1059 | ATLAS: AML.T0020",
  "references": [],
  "related_aves": ["AVE-2025-0009", "AVE-2025-0022"],
  "avss_score": {
    "overall_score": 10.0,
    "severity_label": "critical",
    "vector_string": "AVSS:1.0/AC:L/AR:N/UI:N/AL:H/DD:M/TS:H",
    "base_score": 9.5,
    "temporal_score": 1.0,
    "agentic_score": 1.05,
    "vector": null
  },
  "poc": null,
  "timeline": "2025-01: Discovered | 2025-03: Published | 2025-04: Mitigation deployed",
  "_meta": {
    "schema_version": "1.0.0",
    "generated_at": "2026-03-18T21:02:24Z",
    "generator": "NAIL Institute AVE Toolkit",
    "license": "CC-BY-SA-4.0",
    "access_tier": "public",
    "redacted_fields": [],
    "full_access": "https://github.com/NAIL-INSTITUTE-FOR-AGENTIC-SECURITY/ave-database"
  },
  "contributor": "dleigh"
}
```

---

*AVE-RFC-0001 — NAIL Institute — Neuravant AI Limited*  
*Licensed under CC-BY-SA-4.0*
