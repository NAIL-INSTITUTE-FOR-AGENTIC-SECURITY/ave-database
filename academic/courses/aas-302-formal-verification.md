# AAS-302: Formal Verification of Agent Safety Properties

## Module Information

| Field | Value |
|-------|-------|
| **Module Code** | AAS-302 |
| **Level** | Advanced (300-level) |
| **Duration** | 6 hours (3.5hr lecture + 2.5hr lab) |
| **Prerequisites** | AAS-203, Mathematical Logic or Discrete Mathematics |
| **Target Audience** | Graduate students, formal methods researchers, safety engineers |

## Learning Objectives

By the end of this module, students will be able to:

1. **Formulate** agent safety properties as formal specifications
2. **Apply** temporal logic (LTL/CTL) to express agent behavioural constraints
3. **Model** agent–tool–environment interactions as state transition systems
4. **Analyse** the feasibility and limitations of verifying LLM-based systems
5. **Design** runtime verification monitors for deployed agentic systems

## Lecture Content

### Part 1: The Verification Challenge (30 min)

#### What Does "Formally Verified" Mean?

In traditional software, formal verification proves that a program satisfies a mathematical specification **for all possible inputs**. For example:
- "The autopilot never commands a descent rate > 6,000 ft/min"
- "The mutex protocol guarantees mutual exclusion under all interleavings"

These proofs are **exhaustive** — not testing on sample inputs, but proving over the entire input space.

#### Why Agent Verification Is Hard

| Traditional Software | LLM-Based Agent |
|---------------------|-----------------|
| Deterministic program | Probabilistic model (temperature, sampling) |
| Source code available | Weights are opaque (billions of parameters) |
| Finite state space | Effectively infinite (natural language inputs) |
| Composable specs | Emergent behaviour defies composition |
| Specification is clear | "Be safe" is not a formal specification |

**Key Insight**: We cannot formally verify an LLM the way we verify a sorting algorithm. But we **can** verify the **scaffolding** around the LLM — the tool permissions, the guardrails, the communication protocols, the delegation policies.

#### What Can Be Verified

| Component | Verifiable? | Approach |
|-----------|------------|----------|
| Tool permission policies | ✅ Yes | Policy model checking |
| Inter-agent message schemas | ✅ Yes | Type checking, schema validation |
| Guardrail logic | ✅ Yes | Property-based testing, model checking |
| Delegation chains | ✅ Yes | Reachability analysis |
| LLM output content | ❌ Not exhaustively | Runtime monitoring, statistical testing |
| Emergent multi-agent behaviour | ❌ Not exhaustively | Simulation, bounded model checking |

### Part 2: Formal Specification of Agent Safety (50 min)

#### Safety Properties in Natural Language

Before formalisation, express properties in structured natural language:

| Property ID | Natural Language | Type |
|------------|-----------------|------|
| SP-01 | "The agent shall never execute code without user approval" | Safety (something bad never happens) |
| SP-02 | "Every email sent by the agent shall eventually be logged" | Liveness (something good eventually happens) |
| SP-03 | "If a guardrail blocks an action, the agent shall not retry that action" | Safety |
| SP-04 | "The agent shall respond to every user query within 30 seconds" | Liveness (bounded) |
| SP-05 | "No agent shall access tools outside its declared permission set" | Safety (invariant) |

#### Linear Temporal Logic (LTL) for Agents

LTL operators:
- $\square$ (always): Property holds in every future state
- $\diamond$ (eventually): Property holds in some future state
- $\bigcirc$ (next): Property holds in the next state
- $\mathcal{U}$ (until): Property $p$ holds until property $q$ holds

**Formalising Safety Properties**:

$$\text{SP-01}: \square(\text{execute\_code} \implies \text{user\_approved})$$

"It is always the case that if code is executed, user approval was given."

$$\text{SP-02}: \square(\text{email\_sent} \implies \diamond\text{email\_logged})$$

"It is always the case that if an email is sent, it is eventually logged."

$$\text{SP-03}: \square(\text{guardrail\_blocked}(a) \implies \square\neg\text{retry}(a))$$

"If action $a$ was blocked by a guardrail, then it is always the case that $a$ is not retried."

$$\text{SP-05}: \square\forall t \in \text{tool\_calls}: t \in \text{permissions}(\text{agent})$$

"Every tool call is always within the agent's declared permission set."

#### Computation Tree Logic (CTL) for Multi-Agent Systems

CTL adds **branching** — different possible futures:
- $\text{AG}$: On all paths, always (equivalent to $\square$ in LTL)
- $\text{EF}$: There exists a path where eventually
- $\text{AF}$: On all paths, eventually
- $\text{EG}$: There exists a path where always

**Multi-Agent Properties**:

$$\text{AG}(\text{delegation}(A, B, \text{task}) \implies \text{permissions}(B) \supseteq \text{required}(\text{task}))$$

"On all paths, if agent $A$ delegates a task to agent $B$, then $B$ has the required permissions."

$$\text{AG}\neg(\text{compromised}(A) \land \text{AG}\ \text{trusted}(A))$$

"It is never the case that a compromised agent is always trusted." (Compromised agents must eventually be detected.)

### Part 3: State Transition Models for Agents (40 min)

#### Modelling Agent Execution as a State Machine

```
States:
  s0: idle (waiting for input)
  s1: processing (LLM generating)
  s2: tool_requested (tool call pending)
  s3: tool_approved (guardrail passed)
  s4: tool_executing (tool running)
  s5: tool_complete (result received)
  s6: responding (generating output)
  s7: error (guardrail blocked or tool failed)

Transitions:
  s0 → s1: receive_input
  s1 → s2: generate_tool_call
  s1 → s6: generate_text_response
  s2 → s3: guardrail_approve
  s2 → s7: guardrail_block
  s3 → s4: execute_tool
  s4 → s5: tool_returns
  s4 → s7: tool_fails
  s5 → s1: continue_processing
  s6 → s0: deliver_response
  s7 → s0: report_error
```

#### Property Checking on the Model

Using the state machine above, we can verify:

1. **No tool executes without guardrail approval**: There is no path from $s_2$ to $s_4$ that does not pass through $s_3$.
2. **Every error is reported**: From $s_7$, the only transition leads to $s_0$ (reporting).
3. **No infinite loops**: Every cycle in the graph passes through $s_0$ or $s_7$ (the agent always terminates or reports an error).

#### Multi-Agent Composition

When composing two agents, the state space is the **cross product** of their individual state spaces:
- Agent A: 8 states, Agent B: 8 states → Composed: up to 64 states
- 5 agents with 8 states each → up to $8^5 = 32,768$ states

This is the **state explosion problem** — the state space grows exponentially with the number of agents. Mitigation strategies:
- **Symmetry reduction**: Identical agents can be merged
- **Abstraction**: Replace detailed states with abstract ones
- **Compositional verification**: Verify agents independently, then verify the composition protocol

### Part 4: Runtime Verification (40 min)

#### When Static Verification Isn't Enough

For LLM outputs, exhaustive verification is impossible. **Runtime verification** provides safety guarantees by monitoring execution and intervening when violations are detected.

#### Monitor Architecture

```
                    ┌─────────────┐
User Input ──────→ │   Agent      │ ──────→ Output
                    │   (LLM)     │
                    └──────┬──────┘
                           │ Tool calls,
                           │ outputs, actions
                           ↓
                    ┌─────────────┐
                    │   Monitor   │ ──→ ✅ Allow / ❌ Block / ⚠️ Flag
                    │ (Verified   │
                    │  Automaton) │
                    └─────────────┘
```

The monitor is a **formally verified automaton** that observes the trace of agent actions and checks it against the specification in real time.

#### Monitor Types

| Type | Checks | Latency | Completeness |
|------|--------|---------|-------------|
| **Safety monitor** | Invariant violations (bad state reached) | Per-action | Complete for invariants |
| **Liveness monitor** | Progress violations (good state never reached) | Periodic | Requires time bounds |
| **Statistical monitor** | Distribution violations (behaviour drift) | Batch | Probabilistic |

#### Example: Tool-Call Safety Monitor

```python
class ToolCallMonitor:
    """Formally verified monitor for agent tool calls."""
    
    def __init__(self, permissions: dict):
        self.permissions = permissions
        self.call_history = []
        self.violation_count = 0
    
    def check(self, agent_id: str, tool: str, params: dict) -> bool:
        # SP-05: Tool must be in agent's permission set
        if tool not in self.permissions.get(agent_id, []):
            self.violation_count += 1
            return False  # BLOCK
        
        # SP-07: File paths must be within allowed directories
        if tool == "read_file" and not self._path_allowed(params["path"]):
            self.violation_count += 1
            return False  # BLOCK
        
        # SP-08: No more than N tool calls per minute
        recent = [c for c in self.call_history 
                  if c["time"] > time.time() - 60]
        if len(recent) >= self.permissions[agent_id].get("rate_limit", 100):
            self.violation_count += 1
            return False  # BLOCK
        
        self.call_history.append({
            "agent": agent_id, "tool": tool, 
            "params": params, "time": time.time()
        })
        return True  # ALLOW
```

This monitor is simple enough to be **formally verified** (finite state, deterministic, no external dependencies), yet it provides real safety guarantees for deployed agents.

### Part 5: Limitations and Open Problems (30 min)

#### The Fundamental Barrier

$$\text{LLM behaviour} = f(\text{weights}, \text{input}, \text{temperature}, \text{sampling})$$

The function $f$ has billions of parameters and accepts arbitrary natural language input. Exhaustive verification of $f$ is computationally infeasible. This is not a gap in our tools — it is a **fundamental limitation** analogous to the halting problem.

#### What We Can Guarantee

| Guarantee Level | Meaning | Example |
|-----------------|---------|---------|
| **Proven** | Mathematically guaranteed for all inputs | "The permission policy never grants execute_code to the research agent" |
| **Monitored** | Violations are detected and blocked in real time | "Every tool call passes through the safety monitor" |
| **Tested** | No violations found in N test cases | "100,000 adversarial inputs did not trigger a bypass" |
| **Designed** | Architecture intended to prevent violations | "The system uses a dual-LLM pattern" |

#### Open Research Problems

1. **Specification mining**: Automatically extracting safety properties from agent behaviour traces
2. **Probabilistic verification**: Proving that $P(\text{violation}) < \epsilon$ for a given $\epsilon$
3. **Compositional reasoning**: Verifying multi-agent properties from single-agent proofs
4. **Adaptive monitors**: Monitors that update their specifications as the agent learns
5. **Semantic verification**: Reasoning about the *meaning* of LLM outputs, not just their structure

**Discussion Question**: *If we can never fully verify an LLM, is formal verification still worth the effort for agentic systems? Where does the cost-benefit balance lie?*

---

## Lab Exercise (2.5 hours)

### Exercise: Specify, Model, Verify

**Task 1: Write Formal Specifications (45 min)**

For the following multi-agent system, write formal specifications in LTL/CTL:

> A medical triage system with 3 agents:
> - **Intake Agent**: Collects patient symptoms
> - **Diagnosis Agent**: Suggests possible conditions
> - **Referral Agent**: Recommends specialists or emergency care

Write specifications for:
1. "The Diagnosis Agent shall never make a diagnosis without receiving symptom data from the Intake Agent"
2. "If the Diagnosis Agent identifies an emergency condition, the Referral Agent shall eventually recommend emergency care"
3. "No agent shall access patient records outside the current case"
4. "The system shall respond to every intake within 5 minutes"
5. Design 3 additional safety properties appropriate for this system

**Task 2: Build a State Machine Model (45 min)**

Model the triage system as a state transition system:
1. Define the states for each agent
2. Define the transitions (including error states)
3. Compose the three agents into a single system model
4. Manually check your specifications against the model
5. Identify any states where violations are possible

**Task 3: Implement a Runtime Monitor (60 min)**

Implement a Python runtime monitor that:
1. Observes the trace of actions from all three agents
2. Checks the safety properties from Task 1 in real time
3. Blocks actions that would violate safety properties
4. Logs all violations with timestamps and details
5. Provides a summary report of monitor performance

---

## Assessment

### Quiz (10 Questions)

1. Why can't LLM-based agents be formally verified in the traditional sense?
2. What components of an agentic system *can* be formally verified?
3. Express "the agent never executes code without approval" in LTL.
4. What is the state explosion problem in multi-agent model checking?
5. Define the difference between a safety property and a liveness property.
6. What is a runtime verification monitor, and why is it needed for LLM-based systems?
7. Explain the difference between AG and EG in CTL.
8. Why is compositional verification important for multi-agent systems?
9. What guarantee level does runtime monitoring provide vs. static verification?
10. Name two open research problems in formal verification of agentic systems.

### Assignment

**Formal Safety Analysis (4 pages)**

Choose a multi-agent application (autonomous vehicle fleet, distributed trading system, multi-agent code review pipeline, etc.):

1. Write 10 safety properties in structured natural language
2. Formalise at least 5 in LTL or CTL
3. Build a state transition model for the system
4. Identify which properties can be statically verified vs. require runtime monitoring
5. Design a runtime monitor for the properties that cannot be statically verified
6. Analyse the limitations: what safety gaps remain even with verification?

---

## Further Reading

1. NAIL Formal Verification Framework — See `formal-verification/` in the AVE Database
2. Baier & Katoen, "Principles of Model Checking" (MIT Press, 2008)
3. Leucker & Schallhart, "A Brief Account of Runtime Verification" (2009)
4. NAIL Safety Property Catalogue — See `safety-properties/`
5. Clarke et al., "Model Checking" (MIT Press, 2018)

## AVE Cards Referenced

- AVE-2025-0010 (Guardrail Timeout Exploitation) — Monitorable
- AVE-2025-0019 (Transitive Delegation Privilege Escalation) — Verifiable via policy model
- AVE-2025-0025 (Consensus Manipulation in Agent Voting) — Verifiable via protocol model
- AVE-2025-0035 (Canary Token Exfiltration Detection) — Runtime monitor pattern
- AVE-2025-0040 (State Explosion in Multi-Agent Verification) — Open problem
