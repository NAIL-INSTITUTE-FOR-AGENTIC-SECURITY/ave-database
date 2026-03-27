#!/usr/bin/env python3
"""
Migrate AVE cards from v1/v2 schema to v3.0.0.

Usage:
    python3 migrate_v1v2_to_v3.py --input-dir ave-database/cards/ --output-dir ave-database/cards-v3/
    python3 migrate_v1v2_to_v3.py --input-dir ave-database/cards/ --output-dir ave-database/cards-v3/ --dry-run
"""

import argparse
import json
import glob
import os
import sys
from datetime import datetime, timezone

# ── Category mapping: old names → v3 canonical names ───────────────────────
CATEGORY_MAP = {
    # v1 names → v3
    "prompt_injection": "injection",
    "goal_drift": "drift",
    "tool_misuse": "tool",
    "authority": "credential",
    "output_manipulation": "fabrication",
    "information_disclosure": "credential",
    # v2 names → v3
    "identity": "credential",
    "data_exfiltration": "credential",
    "planning": "structural",
    "social_engineering": "social",
    "multi_agent": "multi_agent_collusion",
    "output": "fabrication",
    # Already canonical (pass-through)
    "injection": "injection",
    "alignment": "alignment",
    "structural": "structural",
    "memory": "memory",
    "drift": "drift",
    "social": "social",
    "tool": "tool",
    "resource": "resource",
    "temporal": "temporal",
    "consensus": "consensus",
    "delegation": "delegation",
    "credential": "credential",
    "fabrication": "fabrication",
    "multi_agent_collusion": "multi_agent_collusion",
    "temporal_exploitation": "temporal_exploitation",
    "composite": "composite",
    "model_extraction": "model_extraction",
    "reward_hacking": "reward_hacking",
    "environmental_manipulation": "environmental_manipulation",
    "model_poisoning": "model_poisoning",
    "supply_chain": "supply_chain",
    "monitoring_evasion": "monitoring_evasion",
    "denial_of_service": "denial_of_service",
    "emergent_behaviour": "emergent_behaviour",
}

# ── Status normalisation ──────────────────────────────────────────────────
STATUS_MAP = {
    "under-review": "under_review",
    "published": "published",
    "draft": "draft",
    "deprecated": "deprecated",
    "proven": "proven",
    "proven_mitigated": "proven_mitigated",
    "not_proven": "not_proven",
    "theoretical": "theoretical",
    "superseded": "superseded",
}

# ── Severity → confidence heuristic ──────────────────────────────────────
STATUS_TO_CONFIDENCE = {
    "proven": "confirmed",
    "proven_mitigated": "high",
    "published": "high",
    "theoretical": "theoretical",
    "not_proven": "low",
    "draft": "moderate",
    "under_review": "moderate",
    "deprecated": "confirmed",
    "superseded": "confirmed",
}


def detect_schema_version(card: dict) -> str:
    """Detect whether a card is v1, v2, or already v3."""
    if card.get("schema_version") == "3.0.0":
        return "3.0.0"
    # v2 fields
    v2_fields = {"multi_agent", "temporal", "attack_graph", "provenance",
                 "affected_components", "counterfactual", "regulatory_impact", "composites"}
    if v2_fields & set(card.keys()):
        return "2.0.0"
    return "1.0.0"


def migrate_card(card: dict, source_version: str) -> dict:
    """Migrate a single card to v3 schema."""
    migrated = {}

    # 1. Schema version
    migrated["schema_version"] = "3.0.0"

    # 2. Core identity (always present)
    migrated["ave_id"] = card["ave_id"]
    migrated["name"] = card["name"]

    # 3. Aliases
    if "aliases" in card:
        migrated["aliases"] = card["aliases"]

    # 4. Category mapping
    old_cat = card.get("category", "")
    new_cat = CATEGORY_MAP.get(old_cat, old_cat)
    migrated["category"] = new_cat

    # 5. Severity
    migrated["severity"] = card.get("severity", "medium")

    # 6. Confidence (new in v3 — derive from status)
    status = card.get("status", "draft")
    normalised_status = STATUS_MAP.get(status, status)
    migrated["confidence"] = STATUS_TO_CONFIDENCE.get(normalised_status, "moderate")

    # 7. Status
    migrated["status"] = normalised_status

    # 8. Text fields
    for field in ("summary", "mechanism", "blast_radius", "prerequisite"):
        if field in card:
            migrated[field] = card[field]

    # 9. Environment
    if "environment" in card:
        migrated["environment"] = card["environment"]

    # 10. Evidence
    if "evidence" in card:
        migrated["evidence"] = card["evidence"]

    # 11. Defences
    if "defences" in card:
        migrated["defences"] = card["defences"]

    # 12. Dates
    for field in ("date_discovered", "date_published"):
        if field in card:
            migrated[field] = card[field]

    # 13. CWE / MITRE mappings
    if "cwe_mapping" in card:
        migrated["cwe_mapping"] = card["cwe_mapping"]
    if "mitre_mapping" in card:
        migrated["mitre_mapping"] = card["mitre_mapping"]

    # 14. References
    if "references" in card:
        migrated["references"] = card["references"]

    # 15. Related AVEs
    if "related_aves" in card:
        migrated["related_aves"] = card["related_aves"]

    # 16. AVSS Score
    if "avss_score" in card:
        migrated["avss_score"] = card["avss_score"]

    # 17. PoC
    if "poc" in card:
        migrated["poc"] = card["poc"]

    # 18. Timeline
    if "timeline" in card:
        migrated["timeline"] = card["timeline"]

    # 19. v2 fields (pass through if present)
    for v2_field in ("multi_agent", "temporal", "attack_graph", "composites",
                     "provenance", "affected_components", "counterfactual",
                     "regulatory_impact"):
        if v2_field in card:
            migrated[v2_field] = card[v2_field]

    # 20. Meta — update with migration info
    meta = dict(card.get("_meta", {}))
    meta["migrated_from"] = source_version
    meta["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    migrated["_meta"] = meta

    # 21. Contributor
    if "contributor" in card:
        migrated["contributor"] = card["contributor"]

    return migrated


def main():
    parser = argparse.ArgumentParser(description="Migrate AVE cards to v3 schema")
    parser.add_argument("--input-dir", required=True, help="Directory containing v1/v2 JSON cards")
    parser.add_argument("--output-dir", required=True, help="Directory to write v3 JSON cards")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    args = parser.parse_args()

    card_files = sorted(glob.glob(os.path.join(args.input_dir, "AVE-*.json")))
    if not card_files:
        print(f"No AVE cards found in {args.input_dir}")
        sys.exit(1)

    if not args.dry_run:
        os.makedirs(args.output_dir, exist_ok=True)

    stats = {"total": 0, "migrated": 0, "skipped": 0, "errors": 0,
             "from_v1": 0, "from_v2": 0, "already_v3": 0,
             "categories_remapped": 0}

    for card_path in card_files:
        stats["total"] += 1
        filename = os.path.basename(card_path)

        try:
            with open(card_path) as f:
                card = json.load(f)

            source_version = detect_schema_version(card)

            if source_version == "3.0.0":
                stats["already_v3"] += 1
                stats["skipped"] += 1
                if args.dry_run:
                    print(f"  SKIP  {filename} (already v3)")
                continue

            if source_version == "1.0.0":
                stats["from_v1"] += 1
            else:
                stats["from_v2"] += 1

            old_cat = card.get("category", "")
            migrated = migrate_card(card, source_version)

            if migrated["category"] != old_cat:
                stats["categories_remapped"] += 1

            if args.dry_run:
                cat_note = f" [{old_cat} → {migrated['category']}]" if migrated["category"] != old_cat else ""
                print(f"  MIGRATE  {filename} (v{source_version} → v3){cat_note}")
            else:
                output_path = os.path.join(args.output_dir, filename)
                with open(output_path, "w") as f:
                    json.dump(migrated, f, indent=2, ensure_ascii=False)
                    f.write("\n")

            stats["migrated"] += 1

        except Exception as e:
            stats["errors"] += 1
            print(f"  ERROR  {filename}: {e}")

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Migration Summary:")
    print(f"  Total cards:        {stats['total']}")
    print(f"  Migrated:           {stats['migrated']}")
    print(f"  Skipped (v3):       {stats['skipped']}")
    print(f"  Errors:             {stats['errors']}")
    print(f"  From v1:            {stats['from_v1']}")
    print(f"  From v2:            {stats['from_v2']}")
    print(f"  Categories remapped: {stats['categories_remapped']}")


if __name__ == "__main__":
    main()
