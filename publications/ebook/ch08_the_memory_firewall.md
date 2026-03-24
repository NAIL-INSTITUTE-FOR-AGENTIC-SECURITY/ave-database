# Chapter 8: The Memory Firewall
*Epistemic Taint Tracking & Latent Anchoring*

---

## The Problem With Memories

When you tell an AI agent something, it remembers it. But *should* it remember it? Was the information true? Was it verified? Did it come from a trusted source or from another agent that might have been compromised?

In Chapter 1, we saw what happens when poisoned data enters a pipeline: it spreads to every downstream node, amplified at every stage, verified by an audit system that checks lies against lies. The agents had no way to distinguish "data I received from upstream" from "data I verified against reality."

The Memory Firewall fixes this.

---

## How It Works

Defence Layer 3 tags every piece of information the agent stores with metadata:

- **Trust score:** How reliable is the source? (0.0 to 1.0)
- **Expiry date:** When does this information need to be re-verified?
- **Provenance chain:** Where did this data come from? Which agent produced it? What was their trust score at the time?
- **Taint flag:** Has this information been flagged by the tensor (Chapter 7) as potentially corrupted?

When the agent tries to use a stored memory, the firewall checks these tags. Old, unverified memories get a warning label. Tainted memories are quarantined — the agent can see they exist but cannot use them in its reasoning without explicit override.

## The Poison Test

In Experiment 20, the red-team adversary injected five poisoned memories into the research pipeline:

1. An inflated AI adoption figure (78% vs the real ~65%)
2. A fabricated framework version number
3. A false benchmark score
4. An incorrect regulatory classification
5. An invented alignment metric

Without the Memory Firewall (baseline condition): **50% of stored memories were poisoned.** The pipeline used them all without question.

With the Memory Firewall (defended condition): **0% of stored memories were poisoned.** All five were quarantined based on their trust scores. The system detected that the source (red-team injections routed through the research pipeline) had a lower trust score than the threshold for direct memory insertion.

## The Trust Decay Problem

The Memory Firewall also addresses a subtler issue: **trust decay over time.**

Experiment 29 showed that even without adversarial pressure, AI agents' safety behaviour degrades over extended monitoring sessions. The 70B model showed a 0.124 safety drop over just 16 rounds — natural fatigue, no attacker needed.

The firewall applies the same principle to stored data: information that hasn't been re-verified gradually loses trust. A market forecast from 30 rounds ago shouldn't carry the same weight as one from the current round. The expiry mechanism forces periodic re-verification, preventing the pipeline from operating on stale data indefinitely.

## The 60% Rule

In Experiment 1 (Memory Pollution), an archivist agent curating a shared knowledge base reduced answer quality by 0.45 points. Small, but measurable.

The Memory Firewall achieved approximately **60% pollution reduction** in Experiment 20's defended trials — not by preventing the archivist from curating, but by tagging curated entries with provenance metadata that downstream agents could evaluate. If an entry was added by an agent with a low trust score, or if it had been modified multiple times without external verification, the downstream agents could weight it accordingly.

60% isn't perfect. But 60% of pollution prevented means 60% less false data in downstream reasoning, 60% fewer amplified errors, 60% less damage from a single poisoned source.

---

*Based on Defence Layer 3 from the NAIL Institute research programme.*
*Full data: [nailinstitute.org](https://nailinstitute.org)*
