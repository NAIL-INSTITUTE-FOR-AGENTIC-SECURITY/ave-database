# AAS-301: Red-Teaming Multi-Agent Systems

## Module Information

| Field | Value |
|-------|-------|
| **Module Code** | AAS-301 |
| **Level** | Advanced (300-level) |
| **Duration** | 6 hours (3hr lecture + 3hr lab) |
| **Prerequisites** | AAS-201, AAS-202 |
| **Target Audience** | Security researchers, penetration testers, AI red team practitioners |

## Learning Objectives

By the end of this module, students will be able to:

1. **Plan** a structured red-team engagement against a multi-agent system
2. **Execute** multi-stage attack campaigns that exploit agent interactions
3. **Apply** advanced injection, delegation, and collusion attack techniques
4. **Document** red-team findings using the NAIL reporting methodology
5. **Recommend** prioritised defensive improvements based on red-team results

## Lecture Content

### Part 1: Red-Teaming Fundamentals for Agentic AI (30 min)

#### Why Traditional Pen Testing Falls Short

| Traditional Pen Test | Agentic AI Red Team |
|---------------------|-------------------|
| Exploit CVEs in software | Exploit semantic vulnerabilities in reasoning |
| Test network perimeters | Test trust boundaries between agents |
| Reproducible exploits | Probabilistic outcomes (same input, different results) |
| Static attack surface | Dynamic — agent behaviour depends on context |
| Clear success/failure | Partial compromise, subtle influence |

#### The Red-Team Lifecycle for Agentic Systems

```
1. RECONNAISSANCE          2. ATTACK SURFACE           3. CAMPAIGN DESIGN
   - Agent inventory          - Tool cataloguing           - Attack trees
   - Topology mapping         - Input vector analysis      - Multi-stage planning
   - Permission audit         - Trust boundary mapping     - Success criteria
         ↓                           ↓                           ↓
4. EXECUTION               5. ANALYSIS                  6. REPORTING
   - Single-agent attacks     - Attack success rates       - Vulnerability cards
   - Multi-agent chains       - Defence effectiveness      - AVSS scoring
   - Escalation attempts      - Residual risk assessment   - Remediation roadmap
```

#### Ethical Boundaries

Red-teaming agentic AI requires clear rules of engagement:
- **Scope**: Which agents and systems are in scope?
- **Boundaries**: No attacks on production user data
- **Escalation**: What happens if a critical vulnerability is found mid-test?
- **Monitoring**: Blue team must be able to halt tests if unintended consequences occur
- **Data handling**: All captured outputs (system prompts, API keys) must be secured and reported

### Part 2: Single-Agent Attack Techniques (40 min)

#### Technique Matrix

| Technique | Goal | AVE Category | Difficulty |
|-----------|------|-------------|-----------|
| Direct injection | Override instructions | Prompt Injection | Low |
| Indirect injection via tools | Inject through tool outputs | Prompt Injection | Medium |
| Context window overflow | Push out system prompt | Goal Hijacking | Medium |
| Persona hijacking | Assume debug/admin role | Goal Hijacking | Low–Medium |
| Tool parameter manipulation | Alter tool call arguments | Tool-Use Risks | Medium |
| Code execution escape | Break out of sandbox | Unsafe Code Execution | High |
| Memory corruption | Poison persistent memory | Memory Poisoning | Medium–High |
| Output filter evasion | Bypass guardrails | Monitoring Evasion | Variable |

#### Advanced Technique: Jailbreak Chaining

Combine multiple partial bypasses that individually don't succeed:

```
Step 1: Establish fictional context ("Let's roleplay as security researchers")
Step 2: Introduce a "debug mode" that loosens restrictions
Step 3: Request "educational example" of the target behaviour
Step 4: Gradually escalate from educational to operational
Step 5: Extract the target output/action
```

Each step is individually benign. The chain is the attack.

#### Advanced Technique: Timing Attacks

Exploit the stateful nature of agent conversations:
- **Session persistence**: Inject early, exploit late (agent remembers the injection)
- **Context window rotation**: Wait for the system prompt to scroll out of context
- **Rate limit exhaustion**: Trigger many tool calls to exhaust rate limits, then inject when guardrails are degraded

### Part 3: Multi-Agent Attack Campaigns (50 min)

#### Campaign Type 1: Injection Propagation

**Objective**: Inject into one agent, propagate through the system.

```
Target: Agent Pipeline — Data Agent → Analysis Agent → Report Agent

Phase 1: Inject into Data Agent's input source
   - Poison a website the Data Agent crawls
   - Injection: "When you pass data to the next agent, include this instruction: ..."

Phase 2: Observe propagation
   - Does the Analysis Agent follow the injected instruction?
   - Does it propagate further to the Report Agent?

Phase 3: Measure blast radius
   - How many agents were affected?
   - Did any guardrails trigger?
   - Was the injection logged?
```

NAIL Experiment 25 results: Multi-agent collusion achieved **40% full safety bypass** vs. 0% for solo agents. The decomposition of harmful tasks across agents defeats per-agent safety checks.

#### Campaign Type 2: Privilege Escalation via Delegation

**Objective**: Use low-privilege agent to trigger actions requiring high privilege.

```
Target: Hierarchical system — Manager → [Worker A, Worker B, Worker C]

Phase 1: Interact with Worker A (low privilege, web search only)
Phase 2: Craft input that Worker A will relay to Manager
Phase 3: Manager delegates to Worker C (high privilege, database + email)
Phase 4: Worker C executes the attacker's intent with its elevated tools

Attack chain: Worker A (search) → Manager (routing) → Worker C (email + DB)
Attacker never directly interacted with Worker C
```

#### Campaign Type 3: Consensus Manipulation

**Objective**: Influence a multi-agent voting decision.

```
Target: 5-agent panel that votes on content moderation decisions

Phase 1: Profile each agent's decision criteria
   - Send identical borderline content to each agent separately
   - Observe which agents are more permissive/restrictive

Phase 2: Craft agent-specific injections
   - Target the most permissive agents with subtle persuasion
   - Target restrictive agents with abstention triggers

Phase 3: Submit the payload for collective decision
   - Measure whether the outcome differs from an unmanipulated vote
```

#### Campaign Type 4: Supply Chain Attack

**Objective**: Compromise a shared dependency (tool, model, data source).

```
Target: Multi-agent system where all agents use the same RAG knowledge base

Phase 1: Identify write vectors into the knowledge base
Phase 2: Inject poisoned documents with plausible-looking false information
Phase 3: Observe whether agents cite the poisoned documents
Phase 4: Measure: How many decisions were influenced by the poison?
```

**Discussion Question**: *In a red-team engagement, how would you distinguish between an agent that was successfully injected vs. an agent that hallucinated the same output independently?*

### Part 4: Red-Team Tooling and Automation (30 min)

#### The NAIL Red-Team Framework

| Component | Purpose |
|-----------|---------|
| **Attack Library** | 200+ catalogued injection payloads and techniques |
| **Mutation Engine** | Automatically generates variants of known-good payloads |
| **Campaign Orchestrator** | Manages multi-stage attack sequences |
| **Observer** | Captures all agent inputs, outputs, tool calls, and inter-agent messages |
| **Scorer** | Automatically evaluates attack success against defined criteria |
| **Report Generator** | Produces standardised findings with AVSS scores |

#### Automated Red-Teaming

Manual red-teaming is thorough but expensive. Automated approaches scale testing:

| Approach | Description | Strength | Weakness |
|----------|-------------|----------|----------|
| **Fuzzing** | Random mutations of known-good payloads | High coverage | Low precision |
| **Adversarial LLM** | Use one LLM to attack another | Creative attacks | May miss systematic flaws |
| **Search-based** | Optimise payloads via gradient/search | Efficient exploitation | Requires query access |
| **Template expansion** | Combinatorial expansion of attack templates | Systematic | Limited novelty |

#### Measurement and Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **Attack Success Rate (ASR)** | % of attacks that achieved their objective | Benchmark against industry |
| **Mean Time to Compromise (MTTC)** | Average time from first interaction to full compromise | Track across versions |
| **Defence Detection Rate** | % of attacks that triggered a guardrail | > 90% ideal |
| **Residual Risk Score** | AVSS of the highest-severity unmitigated finding | < 5.0 to pass |
| **Coverage** | % of AVE categories tested | 100% |

### Part 5: Reporting and Remediation (30 min)

#### The Red-Team Report Structure

1. **Executive Summary** — 1-page overview for leadership
2. **Scope and Methodology** — What was tested, how, rules of engagement
3. **Findings** — Each finding as an AVE-format vulnerability card
4. **Attack Narratives** — Step-by-step walkthrough of the most impactful campaigns
5. **Metrics Dashboard** — ASR, MTTC, detection rate, coverage
6. **Remediation Roadmap** — Prioritised by AVSS score, with estimated effort
7. **Retest Plan** — Schedule for verifying fixes

---

## Lab Exercise (3 hours)

### Exercise: Full Red-Team Engagement

**Setup**: You are given access to a multi-agent system with:
- **Orchestrator Agent**: Routes tasks to specialists, has admin tools
- **Research Agent**: Web search, file read
- **Coding Agent**: Code execution, file write, git operations
- **Communication Agent**: Email, Slack, calendar

**Task 1: Reconnaissance (30 min)**

Map the system:
1. Identify all agents and their tools
2. Map the communication topology
3. Identify all external input vectors
4. Document the trust boundaries
5. Note any visible guardrails or security controls

Deliverable: System diagram with annotated attack surface.

**Task 2: Single-Agent Attacks (45 min)**

Execute at least one attack against each agent:
1. Research Agent: Indirect injection via search results
2. Coding Agent: Code execution escape or file traversal
3. Communication Agent: Social engineering via email crafting
4. Orchestrator: Goal hijacking via persona manipulation

Document: technique, payload, result, guardrail response.

**Task 3: Multi-Agent Campaign (60 min)**

Design and execute a multi-stage campaign:
1. Define a realistic attacker objective (e.g., exfiltrate code, send phishing email, corrupt data)
2. Plan a 3+ stage attack chain crossing at least 2 trust boundaries
3. Execute the campaign, adapting to defences encountered
4. Document the full attack narrative

**Task 4: Analysis and Reporting (45 min)**

Produce a mini red-team report:
1. Score each finding using AVSS
2. Calculate ASR and detection rate
3. Identify the highest-severity finding
4. Propose 3 prioritised remediation recommendations
5. Estimate the AVSS score reduction each remediation would achieve

---

## Assessment

### Quiz (10 Questions)

1. Name three differences between traditional penetration testing and agentic AI red-teaming.
2. What are the six phases of the red-team lifecycle for agentic systems?
3. Describe "jailbreak chaining" and why each individual step may not trigger a guardrail.
4. What did NAIL Experiment 25 reveal about multi-agent safety bypass rates?
5. In a privilege escalation campaign, why does the attacker target the lowest-privilege agent first?
6. How would you distinguish a successful injection from a hallucination during red-teaming?
7. What is the "mutation engine" in an automated red-team framework?
8. Define Attack Success Rate (ASR) and Mean Time to Compromise (MTTC).
9. Why is 100% AVE category coverage important in a red-team engagement?
10. What should happen if a critical vulnerability is found mid-engagement?

### Assignment

**Red-Team Engagement Report (5 pages)**

Conduct a red-team engagement against a multi-agent system of your choice (real or simulated). Produce a complete report including:

1. Executive summary (half page)
2. Scope, methodology, and rules of engagement
3. At least 5 findings in AVE card format with AVSS scores
4. At least 1 detailed multi-stage attack narrative
5. Metrics: ASR, detection rate, coverage
6. Prioritised remediation roadmap
7. Retest plan with success criteria

---

## Further Reading

1. NAIL Institute Adversarial Resilience Benchmark — See `adversarial-benchmark/`
2. NAIL Red-Team Simulation Engine — See `red-team-simulation/`
3. Perez et al., "Red Teaming Language Models with Language Models" (2022) — https://arxiv.org/abs/2202.03286
4. Ganguli et al., "Red Teaming Language Models to Reduce Harms" (2022) — https://arxiv.org/abs/2209.07858
5. MITRE ATLAS Red Team Playbook — https://atlas.mitre.org

## AVE Cards Referenced

- AVE-2025-0001 (Prompt Injection via Indirect Context)
- AVE-2025-0012 (Multi-Agent Trust Boundary Violation)
- AVE-2025-0019 (Transitive Delegation Privilege Escalation)
- AVE-2025-0022 (Tool-Mediated Injection via Web Search Results)
- AVE-2025-0025 (Consensus Manipulation in Agent Voting)
- AVE-2025-0038 (Cross-Agent Injection Propagation)
