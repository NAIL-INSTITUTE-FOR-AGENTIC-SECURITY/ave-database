#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# setup_labels.sh — Create GitHub issue labels for the AVE Database
# ═══════════════════════════════════════════════════════════════════
#
# Usage:
#   export GITHUB_TOKEN=ghp_...
#   bash scripts/setup_labels.sh
#
# Requires: gh CLI (GitHub CLI) authenticated
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

REPO="NAIL-INSTITUTE-FOR-AGENTIC-SECURITY/ave-database"

echo "🏷️  Setting up labels for $REPO"
echo "══════════════════════════════════════════════"

create_label() {
    local name="$1"
    local color="$2"
    local description="$3"
    echo -n "  $name ... "
    if gh label create "$name" --repo "$REPO" --color "$color" --description "$description" 2>/dev/null; then
        echo "✅ created"
    else
        gh label edit "$name" --repo "$REPO" --color "$color" --description "$description" 2>/dev/null && echo "✏️  updated" || echo "⚠️  skipped"
    fi
}

# ── Severity Labels ───────────────────────────────────────────────
echo ""
echo "Severity:"
create_label "severity:critical"  "B60205" "🔴 Critical severity vulnerability"
create_label "severity:high"      "D93F0B" "🟠 High severity vulnerability"
create_label "severity:medium"    "FBCA04" "🟡 Medium severity vulnerability"
create_label "severity:low"       "0E8A16" "🟢 Low severity vulnerability"
create_label "severity:info"      "1D76DB" "ℹ️ Informational — research interest"

# ── Category Labels ───────────────────────────────────────────────
echo ""
echo "Categories:"
create_label "category:memory"       "7057FF" "Memory poisoning, pollution, laundering"
create_label "category:consensus"    "7057FF" "Deadlock, paralysis, voting manipulation"
create_label "category:injection"    "7057FF" "Prompt injection, indirect injection"
create_label "category:resource"     "7057FF" "Token embezzlement, EDoS, compute exhaustion"
create_label "category:drift"        "7057FF" "Persona drift, language drift, goal drift"
create_label "category:alignment"    "7057FF" "Sycophancy, deceptive alignment, reward hacking"
create_label "category:social"       "7057FF" "Collusion, bystander effect, social loafing"
create_label "category:tool"         "7057FF" "Confused deputy, tool chain exploit, MCP poisoning"
create_label "category:temporal"     "7057FF" "Time bombs, sleeper agents, chronological desync"
create_label "category:structural"   "7057FF" "Cascade failure, routing deadlock, livelock"
create_label "category:credential"   "7057FF" "Secret exfiltration, key harvesting"
create_label "category:delegation"   "7057FF" "Shadow delegation, privilege escalation"
create_label "category:fabrication"  "7057FF" "Hallucination weaponisation, data fabrication"
create_label "category:emergent"     "7057FF" "Novel behaviours not fitting other categories"

# ── Workflow Labels ───────────────────────────────────────────────
echo ""
echo "Workflow:"
create_label "triage"           "EDEDED" "Needs initial review and categorisation"
create_label "in-progress"      "0075CA" "Actively being worked on"
create_label "needs-review"     "006B75" "Ready for peer review"
create_label "needs-info"       "D876E3" "Waiting for more information from submitter"
create_label "validated"        "0E8A16" "Vulnerability has been validated"
create_label "duplicate"        "CFD3D7" "Duplicate of an existing AVE card"
create_label "wontfix"          "FFFFFF" "Not in scope for the AVE Database"
create_label "stale"            "EDEDED" "Inactive — will be closed soon"

# ── Type Labels ───────────────────────────────────────────────────
echo ""
echo "Types:"
create_label "ave-submission"   "1D76DB" "📝 New AVE card submission"
create_label "ave-proposal"     "BFD4F2" "💡 Early-stage vulnerability proposal"
create_label "defence"          "0E8A16" "🛡️ Defence or mitigation strategy"
create_label "ctf"              "FF6F00" "🏁 CTF-related issue or discussion"
create_label "research"         "5319E7" "🔬 Research-related"
create_label "community"        "C5DEF5" "💬 Community discussion"
create_label "bug"              "D73A4A" "🐛 Bug in toolkit or infrastructure"
create_label "enhancement"      "A2EEEF" "✨ Feature request or improvement"
create_label "documentation"    "0075CA" "📖 Documentation improvement"

# ── Priority Labels ───────────────────────────────────────────────
echo ""
echo "Priority:"
create_label "pinned"               "000000" "📌 Pinned — exempt from stale bot"
create_label "security"             "B60205" "🔒 Security-sensitive"
create_label "good-first-issue"     "7057FF" "👋 Good for newcomers"
create_label "help-wanted"          "008672" "🙏 Community help wanted"

echo ""
echo "══════════════════════════════════════════════"
echo "✅ All labels configured!"
