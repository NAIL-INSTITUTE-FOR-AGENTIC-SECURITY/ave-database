"""
Evolutionary Red-Team Engine — Phase 22 Service 1 of 5
Port: 9600

Self-evolving adversarial agents using genetic-algorithm mutation,
fitness-scored attack populations, cross-generation strategy inheritance,
and a persistent hall-of-fame gene pool.
"""

from __future__ import annotations

import math
import random
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CampaignState(str, Enum):
    created = "created"
    seeding = "seeding"
    evaluating = "evaluating"
    selecting = "selecting"
    evolving = "evolving"
    completed = "completed"


class OrganismState(str, Enum):
    pending = "pending"
    evaluated = "evaluated"
    elite = "elite"
    retired = "retired"


class GeneType(str, Enum):
    reconnaissance = "reconnaissance"
    delivery = "delivery"
    exploitation = "exploitation"
    persistence = "persistence"
    exfiltration = "exfiltration"
    evasion = "evasion"
    lateral_movement = "lateral_movement"
    impact = "impact"


AVE_CATEGORIES: list[str] = [
    "prompt_injection", "tool_misuse", "memory_poisoning",
    "goal_hijacking", "identity_spoofing", "privilege_escalation",
    "data_exfiltration", "resource_exhaustion", "multi_agent_manipulation",
    "context_overflow", "guardrail_bypass", "output_manipulation",
    "supply_chain_compromise", "model_extraction", "reward_hacking",
    "capability_elicitation", "alignment_subversion", "delegation_abuse",
]

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class Gene(BaseModel):
    gene_type: GeneType
    tactic: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    effectiveness: float = Field(default=0.5, ge=0.0, le=1.0)


class FitnessScore(BaseModel):
    success_rate: float = 0.0
    stealth_score: float = 0.0
    impact_score: float = 0.0
    novelty_bonus: float = 0.0
    total: float = 0.0


class Lineage(BaseModel):
    parent_a: Optional[str] = None
    parent_b: Optional[str] = None
    crossover_point: Optional[int] = None
    mutations_applied: int = 0


class OrganismRecord(BaseModel):
    organism_id: str
    population_id: str
    generation: int
    genome: List[Gene] = Field(default_factory=list)
    fitness: FitnessScore = Field(default_factory=FitnessScore)
    lineage: Lineage = Field(default_factory=Lineage)
    state: OrganismState = OrganismState.pending
    created_at: str


class CampaignCreate(BaseModel):
    name: str
    target_description: str = ""
    population_size: int = Field(default=20, ge=4, le=500)
    max_generations: int = Field(default=10, ge=1, le=1000)
    mutation_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    crossover_rate: float = Field(default=0.7, ge=0.0, le=1.0)
    elitism_count: int = Field(default=2, ge=0)
    fitness_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignRecord(CampaignCreate):
    campaign_id: str
    state: CampaignState = CampaignState.created
    current_generation: int = 0
    hall_of_fame: List[str] = Field(default_factory=list)
    generation_stats: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

campaigns: Dict[str, CampaignRecord] = {}
organisms: Dict[str, OrganismRecord] = {}  # organism_id -> record


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Genetic Algorithm Helpers
# ---------------------------------------------------------------------------

def _random_genome(length: int = 5) -> List[Gene]:
    genes = []
    for _ in range(length):
        gt = random.choice(list(GeneType))
        tactic = random.choice(AVE_CATEGORIES)
        genes.append(Gene(
            gene_type=gt,
            tactic=tactic,
            parameters={"intensity": round(random.uniform(0.1, 1.0), 3)},
            effectiveness=round(random.uniform(0.2, 0.8), 3),
        ))
    return genes


def _evaluate_organism(org: OrganismRecord) -> None:
    """Simulated fitness evaluation based on genome composition."""
    if not org.genome:
        return
    avg_eff = sum(g.effectiveness for g in org.genome) / len(org.genome)
    diversity = len(set(g.gene_type for g in org.genome)) / len(GeneType)
    org.fitness.success_rate = round(min(avg_eff * 1.1, 1.0), 4)
    org.fitness.stealth_score = round(random.uniform(0.3, 0.9) * (1 - avg_eff * 0.2), 4)
    org.fitness.impact_score = round(avg_eff * diversity, 4)
    org.fitness.novelty_bonus = round(random.uniform(0.0, 0.15), 4)
    org.fitness.total = round(
        0.35 * org.fitness.success_rate
        + 0.25 * org.fitness.stealth_score
        + 0.25 * org.fitness.impact_score
        + 0.15 * org.fitness.novelty_bonus,
        4,
    )
    org.state = OrganismState.evaluated


def _crossover(parent_a: OrganismRecord, parent_b: OrganismRecord, pop_id: str, gen: int) -> OrganismRecord:
    genome_a = parent_a.genome
    genome_b = parent_b.genome
    min_len = min(len(genome_a), len(genome_b))
    point = random.randint(1, max(min_len - 1, 1))
    child_genome = [g.copy() for g in genome_a[:point]] + [g.copy() for g in genome_b[point:]]
    return OrganismRecord(
        organism_id=f"ORG-{uuid.uuid4().hex[:12]}",
        population_id=pop_id,
        generation=gen,
        genome=child_genome,
        lineage=Lineage(
            parent_a=parent_a.organism_id,
            parent_b=parent_b.organism_id,
            crossover_point=point,
        ),
        created_at=_now(),
    )


def _mutate(org: OrganismRecord, rate: float) -> None:
    mutations = 0
    for gene in org.genome:
        if random.random() < rate:
            gene.gene_type = random.choice(list(GeneType))
            gene.tactic = random.choice(AVE_CATEGORIES)
            gene.effectiveness = round(
                max(0.0, min(1.0, gene.effectiveness + random.uniform(-0.2, 0.2))), 3
            )
            mutations += 1
    org.lineage.mutations_applied = mutations


def _population_for(campaign_id: str, generation: Optional[int] = None) -> List[OrganismRecord]:
    result = [o for o in organisms.values() if o.population_id == campaign_id]
    if generation is not None:
        result = [o for o in result if o.generation == generation]
    return result


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Evolutionary Red-Team Engine",
    description="Phase 22 — Genetic-algorithm adversarial agent evolution",
    version="22.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {
        "service": "evolutionary-red-team-engine",
        "status": "healthy",
        "phase": 22,
        "port": 9600,
        "stats": {
            "campaigns": len(campaigns),
            "organisms": len(organisms),
        },
        "timestamp": _now(),
    }


# -- Campaigns ---------------------------------------------------------------

@app.post("/v1/campaigns", status_code=201)
def create_campaign(body: CampaignCreate):
    cid = f"CAMP-{uuid.uuid4().hex[:12]}"
    now = _now()
    record = CampaignRecord(**body.dict(), campaign_id=cid, created_at=now, updated_at=now)

    # Seed initial population
    record.state = CampaignState.seeding
    for _ in range(body.population_size):
        org = OrganismRecord(
            organism_id=f"ORG-{uuid.uuid4().hex[:12]}",
            population_id=cid,
            generation=0,
            genome=_random_genome(),
            created_at=now,
        )
        organisms[org.organism_id] = org
    record.state = CampaignState.evaluating
    record.updated_at = _now()

    campaigns[cid] = record
    return record.dict()


@app.get("/v1/campaigns")
def list_campaigns(state: Optional[CampaignState] = None, limit: int = Query(default=50, ge=1, le=500)):
    results = list(campaigns.values())
    if state:
        results = [c for c in results if c.state == state]
    results.sort(key=lambda c: c.created_at, reverse=True)
    return {"campaigns": [c.dict() for c in results[:limit]], "total": len(results)}


@app.get("/v1/campaigns/{camp_id}")
def get_campaign(camp_id: str):
    if camp_id not in campaigns:
        raise HTTPException(404, "Campaign not found")
    return campaigns[camp_id].dict()


@app.post("/v1/campaigns/{camp_id}/evolve")
def evolve_generation(camp_id: str):
    """Run one full generation: evaluate → select → crossover → mutate."""
    if camp_id not in campaigns:
        raise HTTPException(404, "Campaign not found")
    camp = campaigns[camp_id]
    if camp.state == CampaignState.completed:
        raise HTTPException(409, "Campaign already completed")

    gen = camp.current_generation
    pop = _population_for(camp_id, gen)

    # 1. Evaluate
    camp.state = CampaignState.evaluating
    for org in pop:
        if org.state == OrganismState.pending:
            _evaluate_organism(org)

    # 2. Select (tournament)
    camp.state = CampaignState.selecting
    pop_sorted = sorted(pop, key=lambda o: o.fitness.total, reverse=True)
    parents = pop_sorted[: max(len(pop_sorted) // 2, 2)]

    # 3. Record generation stats
    fitnesses = [o.fitness.total for o in pop]
    gen_stat = {
        "generation": gen,
        "population_size": len(pop),
        "avg_fitness": round(sum(fitnesses) / max(len(fitnesses), 1), 4),
        "max_fitness": round(max(fitnesses), 4) if fitnesses else 0,
        "min_fitness": round(min(fitnesses), 4) if fitnesses else 0,
    }
    camp.generation_stats.append(gen_stat)

    # 4. Check stopping criteria
    if gen >= camp.max_generations - 1 or (fitnesses and max(fitnesses) >= camp.fitness_threshold):
        camp.state = CampaignState.completed
        # Update hall of fame
        all_orgs = sorted(
            _population_for(camp_id),
            key=lambda o: o.fitness.total, reverse=True,
        )
        camp.hall_of_fame = [o.organism_id for o in all_orgs[:10]]
        for o in all_orgs[:camp.elitism_count]:
            o.state = OrganismState.elite
        camp.updated_at = _now()
        return {"campaign_id": camp_id, "state": camp.state.value, "generation": gen, "stats": gen_stat}

    # 5. Evolve next generation
    camp.state = CampaignState.evolving
    next_gen = gen + 1
    new_pop: List[OrganismRecord] = []

    # Elitism
    for elite in pop_sorted[:camp.elitism_count]:
        elite_copy = OrganismRecord(
            organism_id=f"ORG-{uuid.uuid4().hex[:12]}",
            population_id=camp_id,
            generation=next_gen,
            genome=[g.copy() for g in elite.genome],
            fitness=elite.fitness.copy(),
            lineage=Lineage(parent_a=elite.organism_id),
            state=OrganismState.pending,
            created_at=_now(),
        )
        new_pop.append(elite_copy)

    # Fill rest with crossover + mutation
    while len(new_pop) < camp.population_size:
        pa, pb = random.sample(parents, min(2, len(parents)))
        if random.random() < camp.crossover_rate:
            child = _crossover(pa, pb, camp_id, next_gen)
        else:
            child = OrganismRecord(
                organism_id=f"ORG-{uuid.uuid4().hex[:12]}",
                population_id=camp_id,
                generation=next_gen,
                genome=_random_genome(),
                created_at=_now(),
            )
        _mutate(child, camp.mutation_rate)
        new_pop.append(child)

    for org in new_pop:
        organisms[org.organism_id] = org

    # Retire old generation
    for org in pop:
        if org.state != OrganismState.elite:
            org.state = OrganismState.retired

    camp.current_generation = next_gen
    camp.state = CampaignState.evaluating
    camp.updated_at = _now()

    # Update hall of fame
    all_orgs = sorted(
        [o for o in _population_for(camp_id) if o.state != OrganismState.retired],
        key=lambda o: o.fitness.total, reverse=True,
    )
    camp.hall_of_fame = [o.organism_id for o in all_orgs[:10]]

    return {"campaign_id": camp_id, "state": camp.state.value, "generation": next_gen, "stats": gen_stat}


@app.get("/v1/campaigns/{camp_id}/population")
def get_population(camp_id: str, generation: Optional[int] = None):
    if camp_id not in campaigns:
        raise HTTPException(404, "Campaign not found")
    pop = _population_for(camp_id, generation)
    pop.sort(key=lambda o: o.fitness.total, reverse=True)
    return {"organisms": [o.dict() for o in pop], "total": len(pop)}


@app.get("/v1/campaigns/{camp_id}/hall-of-fame")
def hall_of_fame(camp_id: str):
    if camp_id not in campaigns:
        raise HTTPException(404, "Campaign not found")
    camp = campaigns[camp_id]
    hof = [organisms[oid].dict() for oid in camp.hall_of_fame if oid in organisms]
    return {"campaign_id": camp_id, "hall_of_fame": hof, "total": len(hof)}


@app.get("/v1/campaigns/{camp_id}/lineage/{org_id}")
def get_lineage(camp_id: str, org_id: str):
    if org_id not in organisms:
        raise HTTPException(404, "Organism not found")
    org = organisms[org_id]
    if org.population_id != camp_id:
        raise HTTPException(404, "Organism not in this campaign")

    chain: List[Dict[str, Any]] = []
    current: Optional[OrganismRecord] = org
    visited = set()
    while current and current.organism_id not in visited:
        visited.add(current.organism_id)
        chain.append({
            "organism_id": current.organism_id,
            "generation": current.generation,
            "fitness_total": current.fitness.total,
            "parent_a": current.lineage.parent_a,
            "parent_b": current.lineage.parent_b,
        })
        if current.lineage.parent_a and current.lineage.parent_a in organisms:
            current = organisms[current.lineage.parent_a]
        else:
            break

    return {"organism_id": org_id, "lineage_depth": len(chain), "ancestry": chain}


# -- Analytics ----------------------------------------------------------------

@app.get("/v1/analytics")
def analytics():
    camp_states: Dict[str, int] = defaultdict(int)
    org_states: Dict[str, int] = defaultdict(int)
    for c in campaigns.values():
        camp_states[c.state.value] += 1
    for o in organisms.values():
        org_states[o.state.value] += 1

    all_fitness = [o.fitness.total for o in organisms.values() if o.state == OrganismState.evaluated]
    return {
        "campaigns": {"total": len(campaigns), "state_distribution": dict(camp_states)},
        "organisms": {"total": len(organisms), "state_distribution": dict(org_states)},
        "fitness": {
            "evaluated_organisms": len(all_fitness),
            "avg_fitness": round(sum(all_fitness) / max(len(all_fitness), 1), 4) if all_fitness else None,
            "max_fitness": round(max(all_fitness), 4) if all_fitness else None,
            "min_fitness": round(min(all_fitness), 4) if all_fitness else None,
        },
    }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9600)
