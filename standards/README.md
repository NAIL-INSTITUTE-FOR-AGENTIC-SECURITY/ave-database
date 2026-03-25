# 📐 AVE Standards

> Formal specifications and RFCs for the Agentic Vulnerability Enumeration ecosystem.

## Published RFCs

| RFC | Title | Status | Version |
|-----|-------|--------|---------|
| [AVE-RFC-0001](ave-spec/AVE-RFC-0001.md) | AVE Card Format Specification | Draft | 1.0.0 |

## Schema Files

| Schema | Description | Format |
|--------|-------------|--------|
| [ave-card.schema.json](ave-spec/ave-card.schema.json) | Normative JSON Schema for AVE cards | JSON Schema Draft-07 |

## RFC Process

### Submitting an RFC

1. **Draft** — Write your RFC following the template in `templates/rfc-template.md`
2. **Submit** — Open a PR adding your RFC to `standards/`
3. **Review** — 30-day public comment period via GitHub Discussions
4. **Board Vote** — Advisory Board supermajority (5/7) required for approval
5. **Merge** — Approved RFCs are merged and assigned an effective date

### RFC Statuses

| Status | Meaning |
|--------|---------|
| Draft | Under development, open for early feedback |
| Review | In 30-day public comment period |
| Approved | Accepted by Advisory Board |
| Final | Implemented and in production use |
| Withdrawn | Author withdrew the proposal |
| Rejected | Not approved by Advisory Board (may be resubmitted) |

### Numbering

RFCs are numbered sequentially: `AVE-RFC-NNNN` (zero-padded, 4 digits).

## Structure

```
standards/
├── README.md                    # This file
├── ave-spec/
│   ├── AVE-RFC-0001.md          # Card format specification
│   └── ave-card.schema.json     # Normative JSON Schema
└── templates/
    └── rfc-template.md          # Template for new RFCs
```

---

*NAIL Institute — Neuravant AI Limited*
