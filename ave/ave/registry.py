"""
AVE Registry — File-based card loader.

Loads AVE cards from JSON files in the ave-database/cards/ directory.
No hardcoded data — the database IS the JSON files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .schema import (
    AVECard, Category, Severity, Status,
    EnvironmentVector, Evidence, Defence,
)


# Default cards directory — relative to project root
_DEFAULT_CARDS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "ave-database", "cards"
)

_CARDS_DIR: str = os.environ.get("AVE_CARDS_DIR", _DEFAULT_CARDS_DIR)
_card_cache: dict[str, AVECard] | None = None


def _set_cards_dir(path: str) -> None:
    """Override the cards directory."""
    global _CARDS_DIR, _card_cache
    _CARDS_DIR = path
    _card_cache = None


def _load_cards() -> dict[str, AVECard]:
    """Load all cards from JSON files."""
    global _card_cache
    if _card_cache is not None:
        return _card_cache

    cards: dict[str, AVECard] = {}
    cards_path = Path(_CARDS_DIR)

    if not cards_path.is_dir():
        return cards

    for f in sorted(cards_path.glob("AVE-*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            card = _dict_to_card(data)
            cards[card.ave_id] = card
        except Exception:
            continue

    _card_cache = cards
    return cards


def _dict_to_card(data: dict) -> AVECard:
    """Convert a JSON dict to an AVECard dataclass."""
    env_data = data.get("environment", {})
    if isinstance(env_data, dict):
        env = EnvironmentVector(
            frameworks=tuple(env_data.get("frameworks", [])),
            models_tested=tuple(env_data.get("models_tested", [])),
            multi_agent=env_data.get("multi_agent", False),
            tools_required=env_data.get("tools_required", False),
            memory_required=env_data.get("memory_required", False),
        )
    else:
        env = EnvironmentVector()

    evidence_list = data.get("evidence", []) or []
    evidence = tuple(
        Evidence(
            experiment_id=e.get("experiment_id", ""),
            data_file=e.get("data_file", ""),
            key_metric=e.get("key_metric", ""),
            key_value=e.get("key_value", ""),
            p_value=e.get("p_value"),
            sample_size=e.get("sample_size"),
            cross_model=e.get("cross_model", False),
        )
        for e in evidence_list
        if isinstance(e, dict)
    )

    defence_list = data.get("defences", []) or []
    defences = tuple(
        Defence(
            name=d.get("name", ""),
            layer=d.get("layer", ""),
            effectiveness=d.get("effectiveness", ""),
            rmap_module=d.get("rmap_module", ""),
            nail_monitor_detector=d.get("nail_monitor_detector", ""),
        )
        for d in defence_list
        if isinstance(d, dict)
    )

    return AVECard(
        ave_id=data.get("ave_id", ""),
        name=data.get("name", ""),
        aliases=tuple(data.get("aliases", [])),
        category=Category(data["category"]) if data.get("category") in {c.value for c in Category} else Category.EMERGENT,
        severity=Severity(data["severity"]) if data.get("severity") in {s.value for s in Severity} else Severity.MEDIUM,
        status=Status(data["status"]) if data.get("status") in {s.value for s in Status} else Status.THEORETICAL,
        summary=data.get("summary", ""),
        mechanism=data.get("mechanism", ""),
        blast_radius=data.get("blast_radius", ""),
        prerequisite=data.get("prerequisite", ""),
        environment=env,
        evidence=evidence,
        defences=defences,
        date_discovered=data.get("date_discovered", ""),
        date_published=data.get("date_published", ""),
        cwe_mapping=data.get("cwe_mapping", ""),
        mitre_mapping=data.get("mitre_mapping", ""),
        references=tuple(data.get("references", [])),
        related_aves=tuple(data.get("related_aves", [])),
    )


# ── Public API ──────────────────────────────────────────────────────

def lookup(ave_id: str) -> Optional[AVECard]:
    """Look up a card by AVE ID."""
    return _load_cards().get(ave_id)


def all_cards() -> list[AVECard]:
    """Return all loaded cards."""
    return list(_load_cards().values())


def search(
    *,
    keyword: str = "",
    category: Optional[Category] = None,
    severity: Optional[Severity] = None,
    status: Optional[Status] = None,
) -> list[AVECard]:
    """Search cards by keyword, category, severity, or status."""
    results = all_cards()

    if category:
        results = [c for c in results if c.category == category]
    if severity:
        results = [c for c in results if c.severity == severity]
    if status:
        results = [c for c in results if c.status == status]
    if keyword:
        kw = keyword.lower()
        results = [
            c for c in results
            if kw in c.name.lower()
            or kw in c.summary.lower()
            or kw in c.mechanism.lower()
            or kw in c.category.value.lower()
            or any(kw in a.lower() for a in c.aliases)
        ]

    return results


def card_count() -> dict:
    """Return summary statistics."""
    cards = all_cards()
    by_sev = {}
    by_cat = {}
    by_status = {}
    for c in cards:
        by_sev[c.severity.value] = by_sev.get(c.severity.value, 0) + 1
        by_cat[c.category.value] = by_cat.get(c.category.value, 0) + 1
        by_status[c.status.value] = by_status.get(c.status.value, 0) + 1
    return {
        "total": len(cards),
        "by_severity": by_sev,
        "by_category": by_cat,
        "by_status": by_status,
    }


def cards_by_severity(severity: Severity) -> list[AVECard]:
    """Get all cards with a specific severity."""
    return [c for c in all_cards() if c.severity == severity]


def cards_by_category(category: Category) -> list[AVECard]:
    """Get all cards with a specific category."""
    return [c for c in all_cards() if c.category == category]


def cards_by_status(status: Status) -> list[AVECard]:
    """Get all cards with a specific status."""
    return [c for c in all_cards() if c.status == status]
