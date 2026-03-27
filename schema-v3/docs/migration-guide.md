# Migrating AVE Cards to Schema v3

> Step-by-step guide for upgrading existing v1/v2 cards to v3.0.0.

---

## What Changed in v3

| Feature | v1 | v2 | v3 |
|---------|----|----|-----|
| `schema_version` field | ❌ | ❌ | ✅ **Required** |
| Categories | 13 | 20 | 24 (unified) |
| `subcategory` | ❌ | ❌ | ✅ Optional |
| `confidence` | ❌ | ❌ | ✅ Optional |
| `exploitability` | ❌ | ❌ | ✅ Optional |
| `multi_agent` | ❌ | ✅ | ✅ Enhanced |
| `temporal` | ❌ | ✅ | ✅ Enhanced |
| `attack_graph` | ❌ | ✅ | ✅ |
| `provenance` | ❌ | ✅ | ✅ Enhanced |
| `regulatory_impact` | ❌ | ✅ | ✅ |
| `affected_components` | ❌ | ✅ | ✅ |
| `counterfactual` | ❌ | ✅ | ✅ |
| Defence objects | basic | basic | ✅ Enhanced (cost, side effects) |
| AVSS v2 scoring | ❌ | ❌ | ✅ (multi_agent_score) |

---

## Automated Migration

Use the migration script to upgrade cards in bulk:

```bash
python3 schema-v3/migration/migrate_v1v2_to_v3.py \
  --input-dir ave-database/cards/ \
  --output-dir ave-database/cards-v3/ \
  --dry-run
```

Remove `--dry-run` to write files.

---

## Manual Migration Steps

### 1. Add `schema_version`

```json
{
  "schema_version": "3.0.0",
  "ave_id": "AVE-2025-0001",
  ...
}
```

### 2. Map Category Names

Some v1/v2 category names have been normalised. The migration script handles
this automatically, but here are the manual mappings:

| Old Name | New v3 Name |
|----------|-------------|
| prompt_injection | injection |
| goal_drift | drift |
| tool_misuse | tool |
| authority | credential |
| output_manipulation | fabrication |
| information_disclosure | credential |
| identity | credential |
| data_exfiltration | credential |
| planning | structural |
| social_engineering | social |
| multi_agent | multi_agent_collusion |

**Categories that stay the same**: memory, delegation, model_extraction,
supply_chain, denial_of_service, consensus, monitoring_evasion, resource,
composite, temporal_exploitation, environmental_manipulation, emergent_behaviour.

### 3. Add Optional v3 Fields (Recommended)

- **`confidence`**: Set to `confirmed` for proven cards, `high` for proven_mitigated
- **`subcategory`**: Add if the card has a clear sub-classification
- **`exploitability`**: Add at minimum `attack_complexity` and `privileges_required`

### 4. Enrich `_meta`

```json
"_meta": {
  "migrated_from": "1.0.0",
  "updated_at": "2026-03-27T00:00:00Z"
}
```

---

## Validation

After migration, validate all cards against the v3 schema:

```bash
python3 -c "
import json, jsonschema, glob
with open('schema-v3/spec/ave-card-v3.schema.json') as f:
    schema = json.load(f)
errors = 0
for card_path in sorted(glob.glob('ave-database/cards-v3/AVE-*.json')):
    with open(card_path) as f:
        card = json.load(f)
    try:
        jsonschema.validate(card, schema)
    except jsonschema.ValidationError as e:
        print(f'FAIL: {card_path}: {e.message}')
        errors += 1
print(f'Validated {len(glob.glob(\"ave-database/cards-v3/AVE-*.json\"))} cards, {errors} errors')
"
```

---

## Backward Compatibility

- **v3 readers** can process v1/v2 cards by treating missing fields as optional
- **v1/v2 readers** can process v3 cards by ignoring unknown fields (if `additionalProperties` is relaxed)
- The `schema_version` field allows readers to branch logic per version
- The `_meta.migrated_from` field preserves migration provenance
