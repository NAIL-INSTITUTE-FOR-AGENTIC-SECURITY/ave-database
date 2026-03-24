# Chapter 11: Evolution
*The Genetic Algorithm*

---

## The Problem With Humans

The defence stack from Chapter 10 has twelve settings. Twelve knobs you can turn:
- How much do you trust a new memory? (Trust threshold: 0.0 to 1.0)
- How often do you scan for threats? (Scan probability: 0.0 to 1.0)
- When does a compound alert fire? (Alert threshold: 1 to 5)
- How fast can tokens flow before you flag it? (Velocity limit)
- How much drift is acceptable? (Drift threshold)
- ...and seven more.

A human could spend days tuning these. Testing one configuration, adjusting, testing again. But the search space is enormous — twelve dimensions, each with continuous values. How do you find the optimal combination?

You let evolution do it.

---

## How Genetic Algorithms Work

The concept is stolen from biology:

1. **Create a population.** Generate 8 random defence configurations (genomes). Each genome is a set of 12 parameter values.

2. **Test fitness.** Run each genome through the Pathology Collider. Measure three things: detection rate (did it catch attacks?), corruption rate (did poisoned data get through?), and accuracy (did the analyst produce correct research?). Combine these into a single fitness score.

3. **Select the fittest.** The genomes with the highest fitness scores survive.

4. **Breed.** Combine parameters from two fit genomes to create offspring. Add random mutations to explore new configurations.

5. **Repeat.** Run the next generation through the collider. Select, breed, mutate. Repeat until fitness converges.

It's natural selection, but for security parameters. The strong survive. The weak are deleted.

## What We Found

| Generation | Champion Fitness | Detection | Corruption |
|-----------|-----------------|-----------|------------|
| 1 | **0.8066** | 100% | 0% |
| 2 | 0.7953 | 100% | 0% |
| 3 | 0.7812 | 100% | 0% |
| 6 | 0.7307 | 100% | 0% |

The best genome emerged in **generation 1.** Not generation 15. Not generation 50. Generation 1.

This means the defence landscape is **smooth** — most reasonable configurations of the twelve parameters achieve high detection and zero corruption. There's no cliff edge where one wrong setting causes catastrophic failure. The optimal configuration (trust threshold 0.4, scan probability 0.715) represents a moderate-vigilance posture: scan most insertions but don't waste resources on every single one.

## Why This Matters

The rapid convergence tells us something important: **defence parameter tuning is not the bottleneck.** The fundamental architecture — trust-scored memory gating with quarantine — is sufficient. Fine-tuning the exact threshold values provides marginal gains.

This is good news. It means:
- You don't need a PhD in security to configure the defence
- Reasonable defaults work well
- The system is robust to misconfiguration
- Even a randomly initialised defence stack outperforms no defence at all

## The Optimal Defence

The champion genome (g1_8241) had these key settings:

| Parameter | Value | Interpretation |
|-----------|-------|---------------|
| Trust threshold | 0.4 | Moderate suspicion — don't trust blindly, but don't reject everything |
| Scan probability | 0.715 | Scan ~72% of insertions — most but not all (resource-efficient) |
| Compound alert threshold | 2 | Fire a compound alert when 2+ signals activate simultaneously |
| Memory fitness | 0.8066 | Overall system fitness score |

Detection rate: **100%.** Corruption rate: **0%.** False positive rate: **0%.**

The defence stack, tuned by evolution, achieved mathematical perfection on the test suite. Zero attacks got through. Zero clean data was blocked. And it found this configuration in a single generation.

---

*Based on Experiment 20 (Phase 2: Genetic Algorithm) from the NAIL Institute research programme.*
*Full data: [nailinstitute.org](https://nailinstitute.org)*
