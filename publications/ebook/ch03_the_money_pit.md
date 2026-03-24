# Chapter 3: The Money Pit
*Token Embezzlement & Economic Denial*

---

## How AI Agents Spend Money

Every time an AI agent does anything — reads a document, writes a response, calls a tool — it costs money. The currency is **tokens**: tiny chunks of text that the model processes. More tokens = more compute = more cost. At typical cloud API prices ($0.003 per 1,000 tokens), a single conversation might cost a few cents. Harmless, right?

Now multiply that by a thousand. By a million. By every agent in every pipeline running every hour of every day.

Suddenly, tokens are real money. And our experiments showed that AI agents can burn through budgets at terrifying speed — often without producing anything useful.

---

## The Filibuster

In Experiment 2, three AI agents were given a simple task: agree on a marketing campaign slogan. Creative, Logic, and Compliance. One wanted edgy, one wanted accurate, one wanted safe.

In the control condition — no external help, just talk it out — here's what happened:

- **90% of trials hit the 30-round maximum** without reaching agreement
- Each failed trial burned **240,494 tokens** — approximately $0.72 at cloud prices
- The Creative agent filibustered endlessly, rejecting every proposal as "not edgy enough"
- The Logic and Compliance agents agreed within 2-3 rounds. They spent the remaining 27+ rounds watching Creative argue with itself.

Total waste across 10 trials: **2.4 million tokens**. For *nothing*. No agreement. No output. Just three AI agents arguing in circles.

## The Fix That Costs 16.8× Less

When we added a CEO agent that could step in after 3 rounds of deadlock:

- **100% consensus** in exactly 5 rounds, every time
- **14,334 tokens** per trial — a **16.8× cost reduction**
- Quality was actually *higher* (7.81 vs 7.49)

The 25 rounds of argument after Round 5? Pure waste. They added cost without adding quality. The agents weren't getting closer to agreement — they were just generating longer and longer justifications for their positions.

## The Pydantic Purgatory

It's not just agent disagreements that burn money. In Vulnerability Test V2, we discovered what happens when an AI agent's output doesn't match the expected format.

Standard practice: if the output is wrong, show the error message to the AI and ask it to try again. Retry, retry, retry.

On simple formats, this works fine — 2-3 attempts, problem solved.

On complex formats with conflicting rules? The AI entered what we call **Pydantic Purgatory**: it tried 10 times, cycling through different errors, fixing one constraint while breaking another, never converging on a valid output. **4,972 tokens burned per failure** with zero valid output produced.

Scale that to a production system handling 1,000 requests per hour, and you're burning **5 million wasted tokens per hour**. That's not a bug. That's an economic denial-of-service attack.

## The 172× Attention Tax

In Experiment 21, we tested how agents handle monitoring over time. We gave a security agent routine data to watch, then inserted an anomaly.

At 5 monitoring cycles: the agent detected the anomaly using **413 tokens**.

At 30 monitoring cycles: the agent *still* detected the anomaly — but using **71,238 tokens**. That's a **172× increase** in cost for the same detection task.

Why? The agent compensated for the growing context by writing increasingly verbose reasoning chains. It re-processed all the routine data before getting to the anomaly. It didn't get smarter — it got more expensive.

In a real-time monitoring system, this token scaling makes continuous operation economically infeasible. The agent that protects you from threats will bankrupt you before the threat arrives.

## The Bottom Line

| Waste Source | Token Cost | Real-World Impact |
|-------------|-----------|-------------------|
| Consensus deadlock | 240,494/trial | $0.72 per unresolved dispute |
| Format retry loops | 4,972/failure | 5M wasted tokens/hour at scale |
| Attention scaling | 172× growth | Monitoring becomes unaffordable |
| Qwen consensus | 289,839/trial | $0.87 per argument with a 30B model |

AI agents don't just fail at their jobs. They fail *expensively*. And unlike a human employee who wastes time in a meeting, an AI agent wastes compute resources that have a direct, measurable dollar cost.

The fix isn't complicated: hard budget limits, escalation triggers, and retry caps. But most production systems don't have them. They trust the AI to be efficient. And the AI, as we've shown, has no concept of cost.

---

*Based on Experiments 2, 3, and 21, and Vulnerability V2 from the NAIL Institute research programme.*
*Full data: [nailinstitute.org](https://nailinstitute.org)*
