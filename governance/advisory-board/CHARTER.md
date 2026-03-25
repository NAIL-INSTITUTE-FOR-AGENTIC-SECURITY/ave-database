# 🏛️ AVE Advisory Board — Charter

> Establishing community governance for the AVE Database and NAIL Institute standards.

**Version:** 1.0.0  
**Effective Date:** 2026-04-01  
**Ratified by:** NAIL Institute Founding Team

---

## 1. Purpose

The AVE Advisory Board provides community-driven governance for:

- **Taxonomy decisions** — Approving new AVE categories and deprecating old ones
- **Card quality** — Final review authority for disputed or high-impact AVE cards
- **Standard evolution** — Guiding the AVE specification through RFC processes
- **Research direction** — Prioritising experiment frameworks and benchmark suites
- **Community health** — Mediating disputes and upholding the Code of Conduct

## 2. Composition

### 2.1 Board Size

The Board consists of **7 voting members**:

| Seat | Domain | Selection |
|------|--------|-----------|
| Chair | General governance | Elected by Board members |
| Seat 1 | AI Safety Research | Community election |
| Seat 2 | Offensive Security / Red Team | Community election |
| Seat 3 | Defensive Engineering | Community election |
| Seat 4 | Enterprise / Industry | Community election |
| Seat 5 | Academic / Policy | Community election |
| Seat 6 | Community Representative | Community election |

### 2.2 Non-Voting Observers

- NAIL Institute Executive Director (permanent)
- Up to 2 invited technical experts per meeting (rotating)

### 2.3 Eligibility

To stand for election, a candidate must:

1. Have contributed to the AVE Database (cards, code, reviews, or research)
2. Hold at minimum **Tier 1 (Observer)** contributor status
3. Not currently serve on more than 2 other open-source governance boards
4. Agree to the Board Member Code of Conduct (Section 8)
5. Commit to a minimum 6-month term

## 3. Terms & Elections

### 3.1 Term Length

- **Standard term:** 12 months
- **Maximum consecutive terms:** 2 (24 months total)
- After a 12-month gap, former members may stand again

### 3.2 Election Cycle

| Event | Timing |
|-------|--------|
| Nomination window | Months 10–11 of current term |
| Candidate presentations | Month 11 (async video or written) |
| Community vote | Month 12 (2-week voting window) |
| New board seated | Month 1 of next term |

### 3.3 Voting System

- **Method:** Ranked-choice voting (instant runoff)
- **Eligibility to vote:** Any contributor with ≥1 merged PR or accepted AVE card
- **Platform:** GitHub Discussions poll + verified ballot (anti-sybil: 60-day account age minimum)
- **Quorum:** 20% of eligible voters must participate for results to be valid

### 3.4 Mid-Term Vacancies

- If a seat becomes vacant, the runner-up from the last election fills it
- If no runner-up exists, the Chair may appoint an interim member until the next election
- Interim appointments must be ratified by majority Board vote within 30 days

## 4. Powers & Responsibilities

### 4.1 Decision Authority

The Board has binding authority over:

| Decision Type | Threshold | Timeframe |
|--------------|-----------|-----------|
| New AVE category | Supermajority (5/7) | 14-day deliberation |
| Category deprecation | Supermajority (5/7) | 30-day deliberation + community comment |
| Disputed card acceptance | Simple majority (4/7) | 7-day deliberation |
| RFC approval | Supermajority (5/7) | 30-day deliberation |
| Code of Conduct enforcement | Simple majority (4/7) | Case-dependent |
| Scoring rubric changes | Supermajority (5/7) | 14-day deliberation |
| Emergency actions | Chair + 2 members | Immediate (ratified within 72 hours) |

### 4.2 Responsibilities

Every Board member must:

1. **Attend** at least 75% of scheduled meetings
2. **Review** at least 2 community submissions per quarter
3. **Participate** in RFC review processes within stated timelines
4. **Disclose** any conflicts of interest before voting
5. **Respond** to community questions within 5 business days

### 4.3 Accountability

- Annual public report summarising decisions, attendance, and community engagement
- Community may call a vote of no confidence with signatures from 10% of eligible voters
- No-confidence vote requires simple majority of eligible voters to remove a member

## 5. Meetings

### 5.1 Regular Meetings

- **Frequency:** Monthly (first Wednesday, 17:00 UTC)
- **Format:** Video call + async agenda review
- **Duration:** 60–90 minutes
- **Public minutes:** Published within 48 hours to `governance/minutes/`

### 5.2 Special Meetings

- Any 3 Board members may call a special meeting with 72-hour notice
- Emergency sessions require only the Chair + 2 members

### 5.3 Agenda Process

1. Agenda items submitted via GitHub Issue (label: `governance/agenda`) by Thursday before meeting
2. Chair finalises agenda by Monday before meeting
3. Community members may attend as observers (muted by default)
4. Public comment period: last 15 minutes of each meeting

## 6. Decision-Making Process

### 6.1 Standard Process

```
1. Proposal submitted (GitHub Issue or RFC)
2. 7-day community comment period
3. Board discussion (meeting or async)
4. Board vote (recorded in minutes)
5. Decision published + rationale documented
```

### 6.2 RFC Process

```
1. RFC drafted and submitted to standards/
2. 30-day public comment period
3. Board review meeting (dedicated session)
4. Board vote (supermajority required)
5. If approved: RFC merged, effective date set
6. If rejected: feedback provided, may be resubmitted
```

### 6.3 Conflict of Interest

- Members must recuse themselves from votes where they have a financial or professional conflict
- Recusals are recorded in meeting minutes
- If >2 members recuse, the vote is deferred to the next meeting

## 7. Working Groups

The Board may establish Working Groups for specific domains:

| Working Group | Scope | Reporting |
|--------------|-------|-----------|
| Taxonomy WG | Category definitions, card schema | Monthly to Board |
| Benchmarks WG | Defence benchmark standards | Quarterly to Board |
| Policy WG | Regulatory mapping, compliance | Quarterly to Board |
| Research WG | Experiment standards, studies | Monthly to Board |

Working Groups:
- Have 3–7 members (at least 1 Board member as liaison)
- Operate by consensus; escalate disagreements to Board
- Publish quarterly progress reports

## 8. Board Member Code of Conduct

In addition to the project Code of Conduct, Board members agree to:

1. **Act in the community's interest**, not personal or employer benefit
2. **Maintain confidentiality** of private security disclosures during embargo periods
3. **Engage constructively** — disagree with ideas, not people
4. **Be transparent** about reasoning behind votes
5. **Step down gracefully** if unable to fulfil responsibilities
6. **Avoid using Board position** for commercial advantage

## 9. Amendments

- This Charter may be amended by supermajority Board vote + 30-day community comment period
- Fundamental changes (board size, election system, term limits) require community referendum
- Amendment history tracked in `governance/CHANGELOG.md`

## 10. Founding Board

The inaugural Board will be **appointed** by the NAIL Institute founding team to bootstrap governance. Appointed members serve a shortened 6-month term, after which all seats transition to community election.

### Inaugural Board Appointments (Planned)

| Seat | Domain | Status |
|------|--------|--------|
| Chair | General | To be announced |
| Seat 1 | AI Safety Research | Open for nominations |
| Seat 2 | Offensive Security | Open for nominations |
| Seat 3 | Defensive Engineering | Open for nominations |
| Seat 4 | Enterprise / Industry | Open for nominations |
| Seat 5 | Academic / Policy | Open for nominations |
| Seat 6 | Community Representative | Open for nominations |

**Nominate yourself or someone else:** Open an issue with the label `governance/nomination`.

---

*NAIL Institute — Neuravant AI Limited*  
*This charter is licensed under CC-BY-SA-4.0*
