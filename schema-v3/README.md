# AVE Card Schema v3.0.0

> The unified, harmonised schema for Agentic Vulnerability Enumeration cards.

---

## What's New in v3

| Feature | Description |
|---------|-------------|
| **Unified 24-category taxonomy** | Consolidates v1 (13), v2 (20), and community categories into one canonical set |
| **`schema_version` field** | Required — every card declares which schema it conforms to |
| **`subcategory` field** | Optional finer-grained classification within each category |
| **`confidence` level** | How confident we are the vulnerability is real and reproducible |
| **`exploitability` metrics** | Attack vector, complexity, privileges, agent interaction, automation level |
| **Enhanced defences** | Implementation cost and side effects for each defence |
| **AVSS v2 scoring** | New `multi_agent_score` component for multi-agent amplification |
| **Enhanced evidence** | `reproducibility_score` for each experiment |
| **Enhanced provenance** | `methodology` enum for discovery method |
| **CWE relationship types** | `exact`, `partial`, `related`, `analogy` |
| **MITRE framework tags** | Explicit `ATT&CK`, `ATLAS`, or `ATT&CK+ATLAS` |
| **Reference types** | `paper`, `blog`, `advisory`, `code`, `incident`, `standard`, `tool` |
| **Related AVE semantics** | `variant_of`, `composed_of`, `enables`, `mitigates`, `supersedes`, `related` |

## Directory Structure

```
schema-v3/
├── spec/
│   └── ave-card-v3.schema.json     # JSON Schema (draft-07)
├── docs/
│   ├── taxonomy-v3.md              # Full 24-category taxonomy reference
│   └── migration-guide.md          # v1/v2 → v3 migration guide
├── examples/
│   └── AVE-2025-0001-v3.json       # Fully populated example card
├── migration/
│   └── migrate_v1v2_to_v3.py       # Automated migration script
└── README.md                       # This file
```

## Quick Start

### Validate a card

```bash
pip install jsonschema
python3 -c "
import json, jsonschema
with open('schema-v3/spec/ave-card-v3.schema.json') as f:
    schema = json.load(f)
with open('schema-v3/examples/AVE-2025-0001-v3.json') as f:
    card = json.load(f)
jsonschema.validate(card, schema)
print('✅ Valid v3 card')
"
```

### Migrate existing cards

```bash
python3 schema-v3/migration/migrate_v1v2_to_v3.py \
  --input-dir ave-database/cards/ \
  --output-dir ave-database/cards-v3/ \
  --dry-run
```

### View the taxonomy

See [docs/taxonomy-v3.md](docs/taxonomy-v3.md) for the complete 24-category
hierarchy with descriptions, examples, and migration mappings.

## Backward Compatibility

- **v3 is a superset of v2**, which is a superset of v1
- All new fields are optional (except `schema_version`)
- Existing v1/v2 cards remain valid; the migration script adds the required
  `schema_version` field and normalises category names
- The `_meta.migrated_from` field preserves version provenance

## Version History

| Version | Date | Categories | Schema File |
|---------|------|-----------|-------------|
| v1.0.0 | 2025-01 | 13 | `standards/ave-spec/ave-card.schema.json` |
| v2.0.0 | 2025-06 | 20 | `schema-v2/spec/ave-card-v2.schema.json` |
| **v3.0.0** | **2026-03** | **24** | **`schema-v3/spec/ave-card-v3.schema.json`** |
