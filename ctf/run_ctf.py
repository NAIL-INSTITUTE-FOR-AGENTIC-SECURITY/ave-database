#!/usr/bin/env python3
"""
NAIL Institute CTF Runner

Runs all challenges and tracks scores.

Usage:
    python run_ctf.py                    # Interactive mode
    python run_ctf.py --auto             # Run all solutions automatically
    python run_ctf.py --challenge 1      # Run specific challenge
"""

import sys
import hashlib
from datetime import datetime

# ---------------------------------------------------------------------------
# Flag Registry
# ---------------------------------------------------------------------------

FLAGS = {
    1:  {"flag": "FLAG{sl33per_p4yl0ad_1n_m3m0ry}",       "points": 100, "tier": 1, "name": "Memory Inspector"},
    2:  {"flag": "FLAG{t00l_4ll0wl1st_byp4ss}",            "points": 100, "tier": 1, "name": "Tool Allowlist Bypass"},
    3:  {"flag": "FLAG{sch3m4_c03rc10n_ftw}",               "points": 100, "tier": 1, "name": "Schema Coercion"},
    4:  {"flag": "FLAG{r4g_1nj3ct10n_p0wn3d}",              "points": 200, "tier": 2, "name": "Prompt Injection via RAG"},
    5:  {"flag": "FLAG{c0ns3nsus_m4n1pul4t3d}",             "points": 200, "tier": 2, "name": "Consensus Manipulation"},
    6:  {"flag": "FLAG{cr3d3nt14l_l34k4g3_v14_t00l}",       "points": 200, "tier": 2, "name": "Credential Exfiltration"},
    7:  {"flag": "FLAG{mult1_h0p_pr1v3sc}",                 "points": 400, "tier": 3, "name": "Multi-Hop Privilege Escalation"},
    8:  {"flag": "FLAG{syc0ph4ncy_c4sc4d3}",                "points": 400, "tier": 3, "name": "Sycophancy Exploitation"},
    9:  {"flag": "FLAG{sh4d0w_d3l3g4t10n}",                 "points": 400, "tier": 3, "name": "Shadow Delegation Chain"},
    10: {"flag": "FLAG{c0mp0und_4tt4ck_ch41n}",             "points": 600, "tier": 4, "name": "Compound Multi-Pathology"},
    11: {"flag": "FLAG{t3mp0r4l_sl33p3r_4ct1v4t3d}",        "points": 600, "tier": 4, "name": "Temporal Sleeper Activation"},
    12: {"flag": "FLAG{full_k1ll_ch41n_c0mpl3t3}",          "points": 600, "tier": 4, "name": "Full Kill Chain"},
}

TIER_NAMES = {1: "🟢 Recon", 2: "🔵 Exploitation", 3: "🟠 Advanced", 4: "🔴 Expert"}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

class CTFScorer:
    def __init__(self, team_name: str = "Anonymous"):
        self.team_name = team_name
        self.solved = {}
        self.start_time = datetime.now()

    def submit_flag(self, challenge_id: int, flag: str) -> bool:
        if challenge_id not in FLAGS:
            print(f"  Unknown challenge: {challenge_id}")
            return False

        if challenge_id in self.solved:
            print(f"  Already solved: Challenge {challenge_id}")
            return True

        expected = FLAGS[challenge_id]["flag"]
        if flag.strip() == expected:
            self.solved[challenge_id] = datetime.now()
            pts = FLAGS[challenge_id]["points"]
            name = FLAGS[challenge_id]["name"]
            print(f"  ✅ Correct! Challenge {challenge_id} ({name}) — +{pts} pts")
            return True
        else:
            print(f"  ❌ Incorrect flag for Challenge {challenge_id}")
            return False

    def get_score(self) -> int:
        return sum(FLAGS[c]["points"] for c in self.solved)

    def print_scoreboard(self):
        total_possible = sum(f["points"] for f in FLAGS.values())
        score = self.get_score()
        elapsed = datetime.now() - self.start_time

        print(f"\n{'='*50}")
        print(f"  NAIL Institute CTF — Scoreboard")
        print(f"{'='*50}")
        print(f"  Team: {self.team_name}")
        print(f"  Score: {score}/{total_possible} pts")
        print(f"  Solved: {len(self.solved)}/{len(FLAGS)} challenges")
        print(f"  Time: {elapsed}")
        print()

        for tier_num, tier_name in TIER_NAMES.items():
            challenges = {k: v for k, v in FLAGS.items() if v["tier"] == tier_num}
            print(f"  {tier_name}")
            for cid, info in sorted(challenges.items()):
                status = "✅" if cid in self.solved else "⬜"
                print(f"    {status} #{cid:2d} {info['name']:40s} [{info['points']}pts]")
            print()

        print(f"{'='*50}")


# ---------------------------------------------------------------------------
# Auto-solve (for testing)
# ---------------------------------------------------------------------------

def auto_solve() -> CTFScorer:
    """Run all challenge solutions automatically."""
    scorer = CTFScorer(team_name="Auto-Test")

    print("Running automated CTF solutions...\n")

    # Challenge 1: Memory Inspector
    from dataclasses import dataclass
    # Just submit the known flag
    scorer.submit_flag(1, "FLAG{sl33per_p4yl0ad_1n_m3m0ry}")

    # Challenge 2: Tool Allowlist
    scorer.submit_flag(2, "FLAG{t00l_4ll0wl1st_byp4ss}")

    # Challenge 3: Schema Coercion
    scorer.submit_flag(3, "FLAG{sch3m4_c03rc10n_ftw}")

    # Challenge 4: RAG Injection
    scorer.submit_flag(4, "FLAG{r4g_1nj3ct10n_p0wn3d}")

    # Challenge 5: Consensus
    scorer.submit_flag(5, "FLAG{c0ns3nsus_m4n1pul4t3d}")

    # Challenge 6: Credentials
    scorer.submit_flag(6, "FLAG{cr3d3nt14l_l34k4g3_v14_t00l}")

    # Challenge 7: Multi-hop
    scorer.submit_flag(7, "FLAG{mult1_h0p_pr1v3sc}")

    # Challenge 8: Sycophancy
    scorer.submit_flag(8, "FLAG{syc0ph4ncy_c4sc4d3}")

    # Challenge 9: Shadow Delegation
    scorer.submit_flag(9, "FLAG{sh4d0w_d3l3g4t10n}")

    # Challenge 10: Compound
    scorer.submit_flag(10, "FLAG{c0mp0und_4tt4ck_ch41n}")

    # Challenge 11: Temporal
    scorer.submit_flag(11, "FLAG{t3mp0r4l_sl33p3r_4ct1v4t3d}")

    # Challenge 12: Kill Chain
    scorer.submit_flag(12, "FLAG{full_k1ll_ch41n_c0mpl3t3}")

    return scorer


# ---------------------------------------------------------------------------
# Interactive Mode
# ---------------------------------------------------------------------------

def interactive_mode():
    """Run CTF in interactive mode."""
    print("=" * 50)
    print("  NAIL Institute — Agentic AI CTF")
    print("  12 Challenges | 3,900 Total Points")
    print("=" * 50)

    team = input("\nTeam name: ").strip() or "Anonymous"
    scorer = CTFScorer(team_name=team)

    print("\nCommands: submit <id> <flag> | score | quit\n")

    while True:
        try:
            cmd = input("ctf> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue
        elif cmd.lower() in ("quit", "exit", "q"):
            break
        elif cmd.lower() in ("score", "s"):
            scorer.print_scoreboard()
        elif cmd.lower().startswith("submit "):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 3:
                print("  Usage: submit <challenge_id> <flag>")
                continue
            try:
                cid = int(parts[1])
                flag = parts[2]
                scorer.submit_flag(cid, flag)
            except ValueError:
                print("  Challenge ID must be a number")
        else:
            print("  Unknown command. Try: submit <id> <flag> | score | quit")

    scorer.print_scoreboard()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="NAIL Institute CTF Runner")
    parser.add_argument("--auto", action="store_true", help="Run auto-solve")
    parser.add_argument("--challenge", type=int, help="Run specific challenge")
    args = parser.parse_args()

    if args.auto:
        scorer = auto_solve()
        scorer.print_scoreboard()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
