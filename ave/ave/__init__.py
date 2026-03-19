"""
AVE — Agentic Vulnerabilities & Exposures
============================================
The CVE database for AI agent failures.

Every vulnerability that can affect an autonomous AI agent — from prompt
injection to consensus paralysis to memory laundering — gets a unique
AVE-ID, a severity score, and a mapping to known defences.

This is the MITRE ATT&CK of the Agentic Era.

Usage:
    >>> import ave
    >>> ave.lookup("AVE-2025-0001")  # Requires cards directory
    >>> ave.search(category=ave.Category.MEMORY)

    >>> from ave.scoring import compute_avss, AVSSVector
    >>> score = compute_avss(AVSSVector(attack_vector=AttackVector.NETWORK))

Open source — maintained by the NAIL Institute.
"""

__version__ = "1.0.0"

from .schema import (
    AVECard,
    Category,
    Severity,
    Status,
    EnvironmentVector,
    Defence,
    Evidence,
)

from .registry import (
    lookup,
    search,
    all_cards,
    card_count,
    cards_by_severity,
    cards_by_category,
    cards_by_status,
)

__all__ = [
    "AVECard",
    "Category",
    "Severity",
    "Status",
    "EnvironmentVector",
    "Defence",
    "Evidence",
    "lookup",
    "search",
    "all_cards",
    "card_count",
    "cards_by_severity",
    "cards_by_category",
    "cards_by_status",
]
