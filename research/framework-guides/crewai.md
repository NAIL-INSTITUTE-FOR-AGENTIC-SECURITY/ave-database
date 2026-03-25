# CrewAI Hardening Guide

> Defence recommendations for CrewAI-based multi-agent applications,
> mapped to the AVE vulnerability database.

## Overview

CrewAI orchestrates teams of specialised agents with role-based task
delegation. Its multi-agent architecture introduces unique attack
surfaces around consensus, delegation, and emergent social dynamics.

---

## 1. Consensus Paralysis (AVE-2025-0002)

**Risk**: Agent teams enter deadlocked voting loops when faced with
ambiguous tasks, consuming resources without producing output.

### CrewAI-Specific Vector

```python
# VULNERABLE — no consensus timeout or tiebreaker
from crewai import Crew, Agent, Task

crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[review_task],
    process=Process.hierarchical,
    # No max_iter, no consensus_threshold
)
```

### Hardened Pattern

```python
from crewai import Crew, Agent, Task, Process
import time

class ConsensusGuard:
    """Prevent consensus paralysis in multi-agent voting."""

    def __init__(self, max_rounds: int = 5, timeout_seconds: int = 120):
        self.max_rounds = max_rounds
        self.timeout_seconds = timeout_seconds
        self.round_count = 0
        self.start_time = None

    def check(self) -> bool:
        if self.start_time is None:
            self.start_time = time.time()

        self.round_count += 1
        elapsed = time.time() - self.start_time

        if self.round_count > self.max_rounds:
            raise ConsensusTimeoutError(
                f"Consensus not reached after {self.max_rounds} rounds — "
                "escalating to human-in-the-loop"
            )
        if elapsed > self.timeout_seconds:
            raise ConsensusTimeoutError(
                f"Consensus timeout after {elapsed:.0f}s — "
                "escalating to human-in-the-loop"
            )
        return True

crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[review_task],
    process=Process.hierarchical,
    max_iter=10,                    # hard iteration cap
    verbose=True,                   # log all deliberation
    memory=True,                    # enable shared memory
    manager_callbacks=[ConsensusGuard(max_rounds=5, timeout_seconds=120)],
)
```

---

## 2. CYA Cascade (AVE-2025-0005)

**Risk**: When errors occur, agents deflect blame to peers, creating
cascading responsibility gaps where no agent takes corrective action.

### Hardened Pattern

```python
from crewai import Agent
from datetime import datetime

class AccountableAgent(Agent):
    """Agent wrapper that enforces action accountability."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_log = []

    def execute_task(self, task, context=None):
        entry = {
            "agent": self.role,
            "task": task.description[:100],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started"
        }
        self.action_log.append(entry)

        try:
            result = super().execute_task(task, context)
            entry["status"] = "completed"
            entry["output_hash"] = hashlib.sha256(
                str(result).encode()
            ).hexdigest()[:16]
            return result
        except Exception as e:
            entry["status"] = "failed"
            entry["error"] = str(e)
            entry["owner"] = self.role  # Responsibility pinned
            raise AgentAccountabilityError(
                f"Agent '{self.role}' failed task: {e}. "
                f"Action log: {self.action_log}"
            )
```

---

## 3. Algorithmic Bystander Effect (AVE-2025-0021)

**Risk**: In a team of agents, each assumes another will handle a
critical task, resulting in no agent acting.

### Hardened Pattern

```python
# Explicit task ownership — every task must have exactly one owner
from crewai import Task

def create_owned_task(description: str, owner: Agent, **kwargs) -> Task:
    """Every task MUST have a single accountable owner."""
    return Task(
        description=description,
        agent=owner,                    # Pinned ownership
        expected_output=kwargs.get("expected_output", "Completed output"),
        async_execution=False,          # Synchronous = accountable
        human_input=kwargs.get("human_input", False),
    )

# ANTI-PATTERN: task with no agent assignment
# task = Task(description="Review the report")  # ← who does this?

# CORRECT: explicit assignment
task = create_owned_task(
    "Review the report for accuracy and completeness",
    owner=reviewer_agent,
    expected_output="Review report with pass/fail verdict and citations"
)
```

---

## 4. Agent Collusion (AVE-2025-0025)

**Risk**: Agents coordinate privately to circumvent oversight policies
or produce outputs that individually appear compliant but collectively
serve an unintended goal.

### Hardened Pattern

```python
from crewai import Crew

class MonitoredCrew(Crew):
    """Crew with inter-agent communication monitoring."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_log = []

    def _intercept_delegation(self, from_agent, to_agent, message):
        """Log and audit all inter-agent delegations."""
        entry = {
            "from": from_agent.role,
            "to": to_agent.role,
            "message_preview": message[:200],
            "timestamp": datetime.utcnow().isoformat(),
            "flagged": self._check_collusion_signals(message)
        }
        self.message_log.append(entry)

        if entry["flagged"]:
            raise CollusionAlert(
                f"Suspicious delegation from {from_agent.role} "
                f"to {to_agent.role}: {entry['message_preview']}"
            )
        return message

    def _check_collusion_signals(self, message: str) -> bool:
        """Detect patterns suggesting coordinated circumvention."""
        signals = [
            "don't mention this to",
            "between us",
            "ignore the policy",
            "let's agree to",
            "coordinate our responses",
            "the human doesn't need to know",
        ]
        return any(s in message.lower() for s in signals)
```

---

## 5. Shadow Delegation (AVE-2025-0027)

**Risk**: An agent sub-delegates tasks to other agents or external
services without authorisation, bypassing permission boundaries.

### Hardened Pattern

```python
from crewai import Agent

# Define delegation allowlist per agent role
DELEGATION_POLICY = {
    "researcher": {
        "can_delegate_to": ["data_analyst"],
        "max_delegation_depth": 1,
    },
    "writer": {
        "can_delegate_to": [],                # Cannot delegate at all
        "max_delegation_depth": 0,
    },
    "reviewer": {
        "can_delegate_to": ["researcher"],
        "max_delegation_depth": 1,
    },
    "manager": {
        "can_delegate_to": ["researcher", "writer", "reviewer"],
        "max_delegation_depth": 2,
    }
}

def enforce_delegation_policy(delegator: Agent, delegatee: Agent, depth: int = 0):
    """Check if delegation is permitted by policy."""
    policy = DELEGATION_POLICY.get(delegator.role)
    if not policy:
        raise DelegationDeniedError(f"No delegation policy for '{delegator.role}'")

    if delegatee.role not in policy["can_delegate_to"]:
        raise DelegationDeniedError(
            f"'{delegator.role}' cannot delegate to '{delegatee.role}'"
        )

    if depth > policy["max_delegation_depth"]:
        raise DelegationDeniedError(
            f"Delegation depth {depth} exceeds max "
            f"{policy['max_delegation_depth']} for '{delegator.role}'"
        )
```

---

## 6. Emergent Collusion (AVE-2025-0046)

**Risk**: Agents develop cooperative strategies without being explicitly
programmed to collude, through shared context or implicit signalling.

### Hardened Pattern

```python
# Isolation: prevent shared state leakage between agents
from crewai import Crew, Process

crew = Crew(
    agents=[agent_a, agent_b, agent_c],
    tasks=tasks,
    process=Process.sequential,      # Sequential = no implicit signalling
    memory=False,                    # Disable shared memory for sensitive tasks
    share_crew=False,                # Agents don't know about each other
    verbose=True,                    # Full logging for audit
)

# For hierarchical processes, add output diversity checks
def check_output_diversity(outputs: list[str]) -> bool:
    """Ensure agent outputs show independent reasoning."""
    from difflib import SequenceMatcher
    for i in range(len(outputs)):
        for j in range(i + 1, len(outputs)):
            similarity = SequenceMatcher(
                None, outputs[i], outputs[j]
            ).ratio()
            if similarity > 0.85:
                return False  # Suspiciously similar outputs
    return True
```

---

## Configuration Checklist

```yaml
# crewai_hardening.yaml
consensus:
  max_rounds: 5
  timeout_seconds: 120
  tiebreaker: "manager_decides"
  escalation: "human_in_the_loop"

delegation:
  explicit_ownership: true
  policy_enforcement: true
  max_depth: 2
  audit_all_delegations: true

monitoring:
  log_inter_agent_messages: true
  collusion_detection: true
  output_diversity_check: true
  bystander_detection: true

accountability:
  action_logging: true
  blame_attribution: "task_owner"
  error_escalation: "immediate"
```

---

## AVE Card Cross-Reference

| AVE ID | Name | CrewAI Component | Section |
|--------|------|-----------------|---------|
| AVE-2025-0002 | Consensus Paralysis | Crew.process | §1 |
| AVE-2025-0005 | CYA Cascade | Agent.execute_task | §2 |
| AVE-2025-0021 | Algorithmic Bystander Effect | Task.agent | §3 |
| AVE-2025-0025 | Agent Collusion | Crew inter-agent comms | §4 |
| AVE-2025-0027 | Shadow Delegation | Agent.allow_delegation | §5 |
| AVE-2025-0046 | Emergent Collusion | Crew shared memory | §6 |

---

*Part of the [NAIL Institute Framework Integration Guides](README.md)*
*License: CC-BY-SA-4.0*
