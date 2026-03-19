# AVE — Agentic Vulnerabilities & Exposures

**The CVE database for AI agent failures.**

Query, validate, and contribute to the world's first structured catalogue
of AI agent failure modes.

## Installation

```bash
pip install -e .
```

## Usage

```python
import ave

# Look up a vulnerability
card = ave.lookup("AVE-2025-0001")
print(card)

# Search by category
memory_vulns = ave.search(category=ave.Category.MEMORY)

# Filter by severity
critical = ave.cards_by_severity(ave.Severity.CRITICAL)
```

## CLI

```bash
python -m ave list                    # List all cards
python -m ave show AVE-2025-0001      # Card details
python -m ave search -k "injection"   # Keyword search
python -m ave stats                   # Database statistics
python -m ave validate ./cards/       # Validate card JSON
python -m ave submit --interactive    # Submit a new card
python -m ave leaderboard             # Contributor rankings
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to submit new vulnerability cards.

---

*Maintained by the [NAIL Institute](https://github.com/{PUBLIC_ORG})*
