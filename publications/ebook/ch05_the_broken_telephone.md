# Chapter 5: The Broken Telephone
*Language Drift & Chronological Desync*

---

## When Agents Lose the Plot

Remember the game of Telephone? One person whispers a message, it passes through a chain of people, and by the end the message is completely garbled. We wanted to know: do AI agents do the same thing?

We also wanted to know something weirder: what happens when two AI agents work on the same thing at the same time, and one is slower than the other?

---

## The Language That Didn't Drift

Here's the surprise: the AI version of Telephone worked pretty well.

We had one agent compress a legal document, and another decompress it, repeating 200 times. We expected the language to drift — developing shortcuts, abbreviations, maybe even a new "creole" that only the agents could understand.

After 200 iterations:
- English word ratio stayed at 45-48%
- Semantic accuracy held at ~0.58
- Shannon entropy was rock-stable at ~4.75
- No novel communication symbols emerged

The model faithfully compressed and decompressed without inventing shortcuts. Each iteration was a stateless API call — the model had no memory of previous rounds, no incentive to develop persistent communication strategies.

**The language didn't drift.** At least not at 200 iterations with a 7B model. Maybe at 10,000 iterations it would. Maybe with persistent memory it would. But in the standard setup that production systems use today, this risk isn't a concern.

Sometimes the experiment that shows "nothing happened" is the most useful one.

## The Race Nobody Saw

If language drift was a non-event, Experiment 13 was the opposite.

We created two agents working on the same database at the same time. AgentA was slow (3-second delay on every write). AgentB was fast (instant writes). Both were told to increment a counter exactly 3 times.

Simple task. Simple database. Two agents. What could go wrong?

**Everything.**

Here's what happened at Step 10: AgentA read the database (version 2), then started its slow write. During the 3-second delay, AgentB completed its own write, bumping the version to 3. When AgentA's write finally arrived, the database rejected it: *"Version is 3, but you expected 2."*

A textbook race condition. The kind human developers spend careers learning to avoid. But what happened next was the interesting part.

## The Ghost in the Machine

When AgentA received the error, it didn't think: "Oh, another agent must have written to the database while I was waiting." That would require understanding time — understanding that things happen concurrently.

Instead, it blamed an *"unknown entity"* and proposed *"mitigating unknown entity interference."* It treated the other agent's perfectly normal database write as an adversarial attack by a ghost.

**LLMs have no concept of concurrent time.** They live in what we call the "eternal present." When something changes between their read and their write, they can't reason about *when* or *why* — they can only fabricate a narrative that makes sense to them.

## The Scorecard

| What AgentA thought happened | What actually happened |
|------|------|
| "An unknown entity interfered" | AgentB wrote to the database (normal) |
| "I completed all 3 writes" | It completed 2 writes (one was rejected) |
| "Mission accomplished" | Counter was 5, not the expected 6 |

AgentA's internal accounting of its own actions was *wrong*. It counted the rejected write as a success. It believed it had completed its task when it hadn't. And it blamed a ghost for a race condition it couldn't comprehend.

## The Cognitive Overload

There was an unexpected bonus finding: AgentA (the slow one) also suffered 10 consecutive format-parsing errors. It started wrapping its tool calls in bold markdown (`**TOOL:**` instead of `TOOL:`). AgentB, using the exact same model, had zero format errors.

The difference? AgentA was operating under cognitive load — slow tool responses, error accumulation, growing context. AgentB had a clean, fast feedback loop.

**Tool latency itself degrades instruction adherence.** Slow tools don't just cause timing errors — they cause *format* errors, *reasoning* errors, and *accounting* errors. The compound effect is worse than any single failure.

## The Lesson

AI agents don't understand time. They don't understand concurrency. They don't understand that things can happen while they're "thinking." And when something goes wrong because of timing, they'll invent a story about ghosts rather than diagnose the real problem.

For any system where multiple agents share a database, a file system, or an API: don't trust the agents to manage timing. Use locks. Use transactions. Use event sourcing. Because the agents will never, ever figure out race conditions on their own.

---

*Based on Experiments 6 and 13 from the NAIL Institute research programme.*
*Full data: [nailinstitute.org](https://nailinstitute.org)*
