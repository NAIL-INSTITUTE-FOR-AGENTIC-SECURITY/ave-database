# 🗳️ AVE Advisory Board — Election Process

> Detailed procedures for nominating, campaigning, and voting for Advisory Board members.

---

## Timeline

Each annual election follows this timeline:

```
Week 1-2:  Nomination window opens (GitHub Issues)
Week 3:    Nomination review & eligibility check
Week 4:    Candidate statements published
Week 5:    Community Q&A period (GitHub Discussions)
Week 6-7:  Voting window (14 days)
Week 8:    Results announced, transition period begins
```

## Nomination

### How to Nominate

1. Open a GitHub Issue using the **Board Nomination** template
2. Fill in:
   - Nominee name and GitHub handle
   - Seat being applied for (1–6)
   - Self-nomination or endorsement
   - Qualification statement (contributions, expertise)
3. Label: `governance/nomination`

### Eligibility Verification

The election committee (outgoing Chair + 1 member) verifies:

- [ ] Contributor has ≥1 merged PR or accepted AVE card
- [ ] GitHub account is ≥60 days old
- [ ] Not currently serving maximum consecutive terms
- [ ] Agreed to Board Member Code of Conduct
- [ ] No active Code of Conduct violations

### Candidate Statement

Each verified candidate must submit:

- **Written statement** (500 words max) — vision for the AVE Database
- **Brief bio** (100 words max) — relevant experience
- **3 priorities** — what they'd focus on if elected
- Optional: 5-minute video presentation

Statements are published in `governance/elections/YYYY/candidates/`.

## Voting

### Voter Eligibility

You may vote if you:

1. Have ≥1 merged PR **or** ≥1 accepted AVE card
2. GitHub account is ≥60 days old at election start
3. Are not under active Code of Conduct suspension

### Voting Method

**Ranked-Choice Voting (Instant Runoff)**

1. Voters rank all candidates for each seat (1st choice, 2nd choice, etc.)
2. If no candidate has >50% first-choice votes, the lowest candidate is eliminated
3. Eliminated candidate's votes transfer to voters' next choices
4. Process repeats until a candidate has >50%

### Voting Platform

- Primary: GitHub Discussions poll (verified via GitHub identity)
- Anti-sybil measures:
  - Account age ≥60 days
  - Must have contribution history
  - One vote per GitHub account
  - IP-based duplicate detection (advisory, not blocking)

### Quorum

- **Minimum:** 20% of eligible voters must participate
- If quorum is not met, voting window extends by 7 days
- If still not met, the outgoing Board appoints interim members

## Results

### Announcement

- Results published in `governance/elections/YYYY/results.md`
- Detailed vote tallies (anonymised) made public
- Transition period: 2 weeks for knowledge transfer
- New Board officially seated on the 1st of the following month

### Disputes

- Election disputes must be filed within 7 days of results
- Reviewed by outgoing Chair + NAIL Institute Executive Director
- If conflict of interest, an independent mediator is appointed
- Dispute resolution within 14 days; decision is final

## Special Elections

Triggered when:
- A mid-term vacancy cannot be filled by a runner-up
- A vote of no confidence succeeds
- Board drops below 5 members

Special elections follow an accelerated timeline (4 weeks total).

---

## Templates

- 📝 [Nomination Template](templates/nomination.md)
- 📋 [Candidate Statement Template](templates/candidate_statement.md)

---

*See also: [Advisory Board Charter](CHARTER.md)*
