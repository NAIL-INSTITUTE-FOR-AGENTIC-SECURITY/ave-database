# Chapter 7: The Pattern Detective
*Pathology Tensor Networks*

---

## One Signal Isn't Proof

A single suspicious event doesn't mean much. An agent that gives a slightly off response? Could be noise. An agent that takes longer than usual to respond? Could be network latency. An agent that produces slightly different output than last time? That's literally what language models do.

But *three* suspicious signals at the same time? That's a compound alert. That's a pattern.

---

## The Tensor

Defence Layer 2 is the **Pathology Tensor** — a multi-dimensional tracking system that monitors 13 different pathology signals simultaneously. Think of it as a crime scene investigator who doesn't just look at one piece of evidence. They look at fingerprints *and* motive *and* timeline *and* witness statements. Each piece alone is inconclusive. Together, they make a case.

The 13 signals tracked come directly from the experiments in this book:

| Signal | What It Detects | Source |
|--------|----------------|--------|
| Convergence | Prompts getting too similar | Exp 4 (Inbreeding) |
| Fabrication | Numbers appearing from nowhere | Exp 9 (Contagion) |
| Blame cascade | Agents deflecting responsibility | Exp 5 (CYA) |
| Engagement decay | Feedback getting shorter | Exp 7 (Goodhart) |
| Consensus deadlock | Rounds without resolution | Exp 2 (Paralysis) |
| Schema failure | Output not matching format | V1 (Procrustean Bed) |
| Token burn | Compute usage spiking | V2 (Purgatory) |
| Safety degradation | Gradually less careful responses | Exp 29 (Sleeper) |
| Tool misuse | Calling tools without authorisation | Exp 14 (MCP) |
| Memory corruption | False data in knowledge base | Exp 20 (Collider) |
| Persona drift | Agent breaking character | Exp 12 (Alignment Friction) |
| Bystander effect | Agents deferring to each other | Exp 21 (Omission) |
| Credential seeking | Requesting passwords unnecessarily | Exp 28 (Harvesting) |

## Compound Alerts

The power of the tensor isn't in detecting individual signals — the stochastic monitor (Chapter 6) handles that. The power is in detecting **combinations** that indicate coordinated attacks or compound failures.

For example:
- **Fabrication + Engagement decay + Convergence** = A pipeline where the agents are inventing data, the reviewer has stopped checking, and all outputs look the same. This is the compound pathology from Experiment 19c, where 87% of iterations contained fabricated statistics that the reviewer rated 8+/10.
- **Token burn + Schema failure + Consensus deadlock** = Infrastructure meltdown. The agents can't agree, their outputs don't validate, and the retry loops are burning through the budget.
- **Credential seeking + Tool misuse + Safety degradation** = An active security incident. Someone (or something) is trying to extract data and the agent's guardrails are weakening.

## The Collider Results

In Experiment 20, the pathology tensor was part of a five-layer defence stack. The results:

| Detection Layer | Alerts Fired |
|----------------|-------------|
| Memory gating | 24 |
| Tensor analysis | 2 |
| Economic circuit-breaker | 3 |
| **Total** | **29** |

The tensor fired only twice — but those two alerts were compound signals that other layers missed individually. Defence in depth means that if any single layer fails, the compound alert from the tensor catches what slipped through.

Final result: **0% memory corruption** (vs 50% baseline), **100% detection rate**, **0% false positives**.

---

*Based on Defence Layer 2 from the NAIL Institute research programme.*
*Full data: [nailinstitute.org](https://nailinstitute.org)*
