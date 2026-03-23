# 📋 Changelog

All notable changes to the AVE Database are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [2.0.0] — 2026-03-23

### Added
- **Documentation Site** — Full GitHub Pages site with searchable card browser, taxonomy visualization, contributor guide, and 36 individual card detail pages (40 HTML pages total)
- **GitHub Discussions** — 5 category templates: AVE Proposals, Research, Defences, CTF Events, General
- **Public API** — Read-only FastAPI server with 10 endpoints: list, get, search, filter by category/severity, stats, taxonomy, recent cards
- **CTF Event Portal** — Static HTML page with event calendar, 6 challenge categories, rules & scoring, past results section
- **Research Artifacts** — Published findings (29 experiments, 5 models), statistical analysis, 5-layer defence architecture, paper abstract, ebook preview
- **Weekly Digest** — Auto-generated Monday community digest (GitHub Actions)
- **New Contributor Welcome Bot** — Automated welcome message for first-time contributors
- **Auto-Label Workflow** — Automatic severity/category labelling on new issues
- **Stale Management** — Automated triage for inactive issues and PRs
- **Project Roadmap** — Public roadmap with 8 phases and community wishlist
- **Label Setup Script** — Automated GitHub label creation (42 labels across 5 groups)
- **Docs Site Generator** — Python generator with static page support and full nav
- **Incremental Sync Pipeline** — Non-destructive private → public repo sync

### Changed
- **Python Toolkit** upgraded to v2.0.0
- **README** expanded with Research, CTF, API, and Community sections
- **Navigation** updated across all 40 docs site pages (CTF, Research, Discuss links)
- **CI Pipeline** fixed — removed private package references from ave-validate.yml

### Fixed
- Organisation name typo: `INTITUTE` → `INSTITUTE` across 83 files
- Git remote URLs updated to corrected org name
- Public repo CI no longer references private packages

---

## [1.0.0] — 2026-03-20

### Added
- **Initial release** — AVE Database with 36 vulnerability cards
- **Python CLI Toolkit** — list, show, search, stats, validate, submit, export, leaderboard, badges
- **Gamification Engine** — XP system, 25 badges, 5 tiers, Hall of Fame auto-generation
- **AVSS Scoring** — Agentic Vulnerability Scoring System
- **Card Schema** — JSON schema with 14 categories, 5 severity levels, 5 status types
- **Evidence Standards** — Tiered evidence system (theoretical → proven_mitigated)
- **GitHub Infrastructure** — Issue templates, PR template, CI validation
- **Community Docs** — Contributing guide (323 lines), Security policy, Code of Conduct
- **Hall of Fame** — Auto-generated leaderboard with 5 contributors
- **Licensing** — CC-BY-SA-4.0 for all database content

---

*NAIL Institute — Neuravant AI Limited*
