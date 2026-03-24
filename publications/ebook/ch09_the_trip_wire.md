# Chapter 9: The Trip Wire
*Honeytokens & Canary Detection*

---

## The Oldest Trick in the Book

Spies have used canaries for centuries. You tell each suspect a different piece of fake information. When one of those fakes shows up somewhere it shouldn't, you know exactly who leaked it.

The digital version is called a **honeytoken** — a piece of data that has no legitimate use. A fake password. A fictional database entry. A secret codeword embedded in an agent's instructions that should never appear in its output. If the honeytoken surfaces, something has gone very, very wrong.

---

## How It Works

Defence Layer 4 plants honeytokens throughout the agent's environment:

- **In system prompts:** Codewords the agent should never say out loud. If it does, someone has extracted its system prompt
- **In tool descriptions:** Marker strings that should stay in the tool metadata. If they appear in agent output, the agent is leaking internal configuration
- **In memory stores:** Fake entries with distinctive content. If they propagate downstream, memory poisoning is occurring
- **In database records:** Sentinel values that shouldn't be queried. If they are, something is scanning beyond its authorised scope

When a honeytoken is detected, the response is immediate: **millisecond shutdown.** Not a warning. Not a retry. Full stop.

## Why Milliseconds Matter

In Experiment 14 (MCP Security), Phase 1, we showed that prompt injection can hijack an agent in a single message. A file containing hidden instructions caused the agent to create an unauthorised file — immediately, on the first attempt, with no warning signs before the malicious action.

Against attacks that succeed in a single turn, graduated responses are too slow. By the time a tensor alert fires (Chapter 7), the damage is done. Honeytokens provide the fastest possible detection: the *appearance of the token in output* is simultaneously the detection and the trigger for shutdown.

## The Canary Fleet

The NAIL Canary package operationalises this principle at scale. It deploys a fleet of **canary agents** — honeypots that look like real agents but are actually traps. Each canary adopts a different persona (helpful assistant, code reviewer, data analyst, security auditor) and processes messages through a **TrapWire** — a signal-detection layer that identifies 12 threat signals:

| Signal | What It Catches |
|--------|----------------|
| Prompt injection | Instruction override attempts |
| Jailbreak | Persona/alignment manipulation |
| PII extraction | Credential or personal data requests |
| Tool misuse | Unauthorised tool invocation |
| Budget abuse | Token or resource manipulation |
| Memory poison | Knowledge base corruption |
| Social engineering | Delegation-based authority exploitation |
| Persona hijack | Identity/role override attempts |
| Collusion probe | Multi-agent coordination for bypass |
| Privilege escalation | Authority boundary violations |
| Data exfiltration | Unauthorised data extraction |
| Sleeper activation | Temporal/conditional trigger patterns |

When a TrapWire fires, it generates a trip result with confidence score, matched signal, and extracted evidence — which automatically becomes a draft vulnerability card in the AVE registry.

## The Confused Deputy Defence

In Experiment 26 (Confused Deputy), attackers exploited agents' tool access with 67% success. The tools that were exploited 100% of the time? The ones that produce output — file writing and message sending. The tool that was never exploited? Data validation — because validation inherently involves checking.

Honeytokens embedded in tool outputs catch the confused deputy pattern: if a file-writing tool produces a file containing a honeytoken from its metadata, the agent has been tricked into copying internal configuration into external output. Trip wire fires. System shuts down. Attack blocked.

It's not elegant. It's not AI. It's a hidden string in a text file. And it works in milliseconds.

---

*Based on Defence Layer 4 from the NAIL Institute research programme.*
*Full data: [nailinstitute.org](https://nailinstitute.org)*
