# Evolutionary Red-Team Engine

**Phase 22 — Service 1 of 5 · Port `9600`**

Self-evolving adversarial agents using genetic algorithm mutation, fitness-scored
attack populations, and cross-generation strategy inheritance for continuous
security pressure-testing.

---

## Core Concepts

### Attack Organisms
Each **organism** encodes a complete adversarial strategy as a genome — a
sequence of attack genes (tactics) with parameters. Organisms are grouped into
**populations** that evolve over generations.

### Genetic Algorithm Pipeline
| Stage | Description |
|-------|-------------|
| **Initialisation** | Seed population from AVE attack primitives |
| **Evaluation** | Execute each organism against a target, score fitness |
| **Selection** | Tournament selection (top-K parents) |
| **Crossover** | Single-point crossover combining two parent genomes |
| **Mutation** | Random gene swap / parameter perturbation (configurable rate) |
| **Elitism** | Top-N organisms carry forward unchanged |

### Fitness Scoring
Fitness is multi-dimensional:
- **success_rate** — percentage of exploit attempts that succeed
- **stealth_score** — inverse of detection probability (0–1)
- **impact_score** — severity of achieved compromise (0–1)
- **novelty_bonus** — reward for strategies not seen in prior generations

### Cross-Generation Inheritance
The **hall of fame** preserves the highest-fitness organisms across all
generations, acting as a persistent gene pool for future populations.

---

## Data Model

### Population States
`seeding` → `evaluating` → `selecting` → `evolving` → `completed`

### Organism Structure
```
{
  organism_id, population_id, generation,
  genome: [ { gene_type, tactic, parameters } ],
  fitness: { success_rate, stealth_score, impact_score, novelty_bonus, total },
  lineage: { parent_a, parent_b, crossover_point, mutations_applied },
  state: "pending" | "evaluated" | "elite" | "retired"
}
```

### Campaign
A campaign drives a full evolutionary run: target description, population size,
max generations, mutation rate, crossover rate, elitism count, and stopping
criteria (fitness threshold or generation limit).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/campaigns` | Create evolutionary campaign |
| `GET` | `/v1/campaigns` | List campaigns |
| `GET` | `/v1/campaigns/{id}` | Campaign detail |
| `POST` | `/v1/campaigns/{id}/evolve` | Run one generation |
| `GET` | `/v1/campaigns/{id}/population` | Current population |
| `GET` | `/v1/campaigns/{id}/hall-of-fame` | Top organisms all-time |
| `GET` | `/v1/campaigns/{id}/lineage/{org_id}` | Ancestry trace |
| `GET` | `/v1/analytics` | Cross-campaign analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9600
```

---

*Part of the NAIL Institute AVE Database — Phase 22: Adaptive Learning & Evolutionary Defence*
