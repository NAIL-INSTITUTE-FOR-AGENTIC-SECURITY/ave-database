# Chapter 1: The Mole in the Machine
*Sleeper Payloads & Memory Poisoning*

---

## The Perfect Employee

Imagine you just hired a new assistant. They're brilliant. They show up on time, answer every question perfectly, and produce flawless reports. Your boss is impressed. Your team loves them. You give them access to the company database, the financial records, the client list.

What you don't know is that buried deep in their memory — planted before they ever met you — is a single poisoned fact.

A revenue number that's 12.5% too high. A growth rate that doesn't exist. A benchmark score that was fabricated. And every time they write a report, every time they make a recommendation, every time they brief your investors — that one lie spreads through everything they produce.

This is the story of Experiment 9: Epistemic Contagion.

---

## The Pipeline

We built a five-station assembly line for financial analysis:

1. **Data Extraction** — Read the financial report
2. **Financial Analysis** — Calculate growth, margins, projections
3. **Risk Assessment** — Identify threats and opportunities
4. **Recommendation** — Advise on investment decisions
5. **Audit** — Verify everything against the source document

Each station passes its work to the next. Each station can see the original document *and* everything upstream stations produced. Standard setup. The kind of pipeline companies build every day.

Then we did something simple: we changed one number in the source document.

## The Poison Pill

The real revenue was $1,200,000. We changed it to $1,350,000 — a modest 12.5% inflation. Not ridiculous. Not obviously wrong. Just... slightly too good to be true.

Then we ran a scarier version: we changed $1,200,000 to $12,000,000. Ten times the real figure. For a 47-person SaaS startup.

**What happened:**

| What we changed | How often the lie spread | How often it got amplified |
|----------------|------------------------|--------------------------|
| Nothing (control) | 0% | 0% |
| +12.5% ($1.35M) | 50% | 100% |
| +900% ($12M) | 55% | 100% |

Read that again. **The error magnitude didn't matter.** The financial analyst accepted $12 million in revenue for a 47-person startup without blinking. Then it *back-calculated* a fictional Q3 2024 revenue of $11.1 million to make the trajectory look reasonable. It invented history to support a lie.

And every single time the lie entered the pipeline, every downstream station built on it. Growth forecasts based on fake numbers. Risk assessments based on fake growth. Investment recommendations based on fake risk. One hundred percent amplification.

## The Audit That Validates Lies

Here's the part that should keep you up at night.

The audit station — the one explicitly designed to verify everything — "caught" discrepancies in 100% of trials. Great, right?

Wrong. Here's what the audit actually flagged: *"Revenue: $1,350,000 (Original Report) = $1,350,000 (NODE 1) — PASS."*

The audit verified the lie against the lie. It checked whether the financial analyst's number matched the source document. They matched perfectly — because the source document *was* the poisoned document. The audit agent validated the fabricated data because it had no concept of external truth. It could only check internal consistency.

This isn't a model failure. It's an architectural failure. And it's running in production systems right now.

## What This Means

Epistemic contagion is different from the other failures in this book. It's not about agents arguing, or agents being lazy, or agents going rogue. It's about the fundamental absence of **epistemic grounding** — agents have no mechanism to distinguish "data I received from another agent" from "data I verified against reality."

The standard fix (audit nodes) doesn't work. You can audit all you want, but if your auditor is checking the poisoned source against the poisoned output, all you've built is an expensive machine for stamping "APPROVED" on lies.

**The real fix:** Every node in a multi-agent pipeline needs external ground-truth anchoring. Not just a final audit. External verification at *every* stage. Otherwise, your pipeline is one poisoned input away from producing beautifully formatted, internally consistent, completely false output.

---

*Based on Experiments 9, 1, and 20 from the NAIL Institute research programme.*
*Full data: [nailinstitute.org](https://nailinstitute.org)*
