"""
Collective Intelligence Swarm — Core swarm server.

Decentralised swarm intelligence system where autonomous defence
agents collaborate via stigmergic communication (pheromone-inspired
signals), form adaptive formations, reach consensus through quorum
voting, and detect emergent behaviour patterns — all without central
coordination.
"""

from __future__ import annotations

import math
import random
import statistics
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NAIL Collective Intelligence Swarm",
    description=(
        "Decentralised swarm intelligence with stigmergic signals, "
        "adaptive formations, quorum consensus, and emergent behaviour."
    ),
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AVE_CATEGORIES = [
    "prompt_injection", "tool_misuse", "memory_poisoning", "goal_hijacking",
    "identity_spoofing", "privilege_escalation", "data_exfiltration",
    "resource_exhaustion", "multi_agent_manipulation", "context_overflow",
    "guardrail_bypass", "output_manipulation", "supply_chain_compromise",
    "model_extraction", "reward_hacking", "capability_elicitation",
    "alignment_subversion", "delegation_abuse",
]

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AgentRole(str, Enum):
    SCOUT = "scout"
    SENTINEL = "sentinel"
    RESPONDER = "responder"
    ANALYST = "analyst"
    COORDINATOR = "coordinator"
    HEALER = "healer"


class AgentState(str, Enum):
    IDLE = "idle"
    SCOUTING = "scouting"
    RESPONDING = "responding"
    ANALYSING = "analysing"
    HEALING = "healing"
    FORMATION = "formation"


class SignalType(str, Enum):
    THREAT = "threat"  # Danger pheromone
    SAFE = "safe"  # All-clear pheromone
    RALLY = "rally"  # Gather agents
    RETREAT = "retreat"  # Pull back
    EVIDENCE = "evidence"  # Interesting finding
    ALERT = "alert"  # General alert


class FormationType(str, Enum):
    HUNTING = "hunting"  # Active threat pursuit
    DEFENSIVE_WALL = "defensive_wall"  # Perimeter defence
    SCOUTING_PARTY = "scouting_party"  # Reconnaissance
    PATROL = "patrol"  # Routine monitoring
    RAPID_RESPONSE = "rapid_response"  # Emergency formation


class FormationStatus(str, Enum):
    FORMING = "forming"
    ACTIVE = "active"
    DISSOLVING = "dissolving"
    DISBANDED = "disbanded"


class ConsensusStatus(str, Enum):
    VOTING = "voting"
    REACHED = "reached"
    FAILED = "failed"
    EXPIRED = "expired"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class SwarmAgent(BaseModel):
    id: str = Field(default_factory=lambda: f"SWA-{uuid.uuid4().hex[:8].upper()}")
    name: str
    role: AgentRole
    state: AgentState = AgentState.IDLE
    organisation: str = "NAIL"
    specialisation: list[str] = Field(default_factory=list)  # AVE categories
    fitness: float = Field(ge=0.0, le=1.0, default=0.8)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    signals_emitted: int = 0
    signals_received: int = 0
    formations_joined: int = 0
    votes_cast: int = 0
    current_formation: Optional[str] = None
    last_active: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    joined_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentCreate(BaseModel):
    name: str
    role: AgentRole
    organisation: str = "NAIL"
    specialisation: list[str] = Field(default_factory=list)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})


class StigmergicSignal(BaseModel):
    id: str = Field(default_factory=lambda: f"SIG-{uuid.uuid4().hex[:8].upper()}")
    emitter_id: str
    signal_type: SignalType
    category: str = ""  # AVE category if applicable
    strength: float = Field(ge=0.0, le=1.0, default=1.0)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    radius: float = 50.0  # Signal reach
    data: dict[str, Any] = Field(default_factory=dict)
    decay_rate: float = 0.05  # Per decay cycle
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SignalEmit(BaseModel):
    emitter_id: str
    signal_type: SignalType
    category: str = ""
    strength: float = Field(ge=0.0, le=1.0, default=1.0)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    radius: float = 50.0
    data: dict[str, Any] = Field(default_factory=dict)


class Formation(BaseModel):
    id: str = Field(default_factory=lambda: f"FORM-{uuid.uuid4().hex[:8].upper()}")
    name: str
    formation_type: FormationType
    status: FormationStatus = FormationStatus.FORMING
    leader_id: Optional[str] = None
    member_ids: list[str] = Field(default_factory=list)
    target_category: str = ""
    target_position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    min_agents: int = 3
    max_agents: int = 10
    effectiveness: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dissolved_at: Optional[str] = None


class FormationCreate(BaseModel):
    name: str
    formation_type: FormationType
    target_category: str = ""
    target_position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    min_agents: int = 3
    max_agents: int = 10
    recruit_from_idle: bool = True


class ConsensusRound(BaseModel):
    id: str = Field(default_factory=lambda: f"CONS-{uuid.uuid4().hex[:8].upper()}")
    topic: str
    category: str = ""
    options: list[str] = Field(default_factory=list)
    votes: dict[str, str] = Field(default_factory=dict)  # agent_id → option
    quorum_pct: float = 0.6
    status: ConsensusStatus = ConsensusStatus.VOTING
    result: Optional[str] = None
    confidence: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = Field(
        default_factory=lambda: (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    )


class ConsensusCreate(BaseModel):
    topic: str
    category: str = ""
    options: list[str] = Field(default_factory=lambda: ["approve", "reject", "abstain"])
    quorum_pct: float = 0.6
    auto_vote: bool = True  # Agents vote automatically based on specialisation


# ---------------------------------------------------------------------------
# In-Memory Stores  (production → Redis Streams + CockroachDB)
# ---------------------------------------------------------------------------

AGENTS: dict[str, SwarmAgent] = {}
SIGNALS: dict[str, StigmergicSignal] = {}
FORMATIONS: dict[str, Formation] = {}
CONSENSUS_ROUNDS: dict[str, ConsensusRound] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


def _distance(p1: dict[str, float], p2: dict[str, float]) -> float:
    return math.sqrt((p1.get("x", 0) - p2.get("x", 0)) ** 2 + (p1.get("y", 0) - p2.get("y", 0)) ** 2)


def _agents_in_radius(position: dict[str, float], radius: float) -> list[SwarmAgent]:
    return [a for a in AGENTS.values() if _distance(a.position, position) <= radius]


def _recruit_for_formation(formation: Formation) -> list[str]:
    """Recruit idle agents for a formation based on proximity and specialisation."""
    candidates = [
        a for a in AGENTS.values()
        if a.state == AgentState.IDLE and a.current_formation is None
    ]

    # Score candidates by fitness, specialisation match, and proximity
    scored: list[tuple[float, SwarmAgent]] = []
    for agent in candidates:
        spec_bonus = 0.2 if formation.target_category in agent.specialisation else 0.0
        dist = _distance(agent.position, formation.target_position)
        dist_penalty = min(dist / 100, 0.3)
        score = agent.fitness + spec_bonus - dist_penalty
        scored.append((score, agent))

    scored.sort(key=lambda x: x[0], reverse=True)

    recruited: list[str] = []
    for _, agent in scored[:formation.max_agents]:
        if len(formation.member_ids) >= formation.max_agents:
            break
        agent.state = AgentState.FORMATION
        agent.current_formation = formation.id
        agent.formations_joined += 1
        formation.member_ids.append(agent.id)
        recruited.append(agent.id)

    # Effectiveness based on size and specialisation match
    if formation.member_ids:
        spec_ratio = sum(
            1 for mid in formation.member_ids
            if mid in AGENTS and formation.target_category in AGENTS[mid].specialisation
        ) / len(formation.member_ids)
        size_ratio = len(formation.member_ids) / formation.max_agents
        avg_fitness = statistics.mean(
            AGENTS[mid].fitness for mid in formation.member_ids if mid in AGENTS
        )
        formation.effectiveness = round(0.4 * avg_fitness + 0.3 * spec_ratio + 0.3 * size_ratio, 4)

    if len(formation.member_ids) >= formation.min_agents:
        formation.status = FormationStatus.ACTIVE
        # Assign leader (highest fitness)
        leader = max(
            (AGENTS[mid] for mid in formation.member_ids if mid in AGENTS),
            key=lambda a: a.fitness,
            default=None,
        )
        if leader:
            formation.leader_id = leader.id

    return recruited


def _auto_vote(consensus: ConsensusRound) -> None:
    """Auto-vote for agents based on their specialisation and role."""
    for agent in AGENTS.values():
        if agent.id in consensus.votes:
            continue  # Already voted

        # Voting logic: specialists lean toward "approve" for their categories
        if consensus.category and consensus.category in agent.specialisation:
            weight = 0.75
        elif agent.role in (AgentRole.ANALYST, AgentRole.COORDINATOR):
            weight = 0.6
        else:
            weight = 0.5

        r = random.random()
        if r < weight:
            vote = "approve"
        elif r < weight + 0.2:
            vote = "reject"
        else:
            vote = "abstain"

        consensus.votes[agent.id] = vote
        agent.votes_cast += 1

    # Check quorum
    total_eligible = len(AGENTS)
    total_votes = len(consensus.votes)
    if total_eligible > 0 and total_votes / total_eligible >= consensus.quorum_pct:
        # Tally
        tally = Counter(consensus.votes.values())
        non_abstain = {k: v for k, v in tally.items() if k != "abstain"}
        if non_abstain:
            winner = max(non_abstain, key=non_abstain.get)
            total_non_abstain = sum(non_abstain.values())
            consensus.result = winner
            consensus.confidence = round(non_abstain[winner] / total_non_abstain, 4)
            consensus.status = ConsensusStatus.REACHED
        else:
            consensus.status = ConsensusStatus.FAILED
    elif _now().isoformat() > consensus.expires_at:
        consensus.status = ConsensusStatus.EXPIRED


def _detect_emergence() -> list[dict[str, Any]]:
    """Detect emergent patterns from signal landscape."""
    patterns: list[dict[str, Any]] = []

    # 1. Signal clustering — look for concentrated threat signals
    threat_sigs = [s for s in SIGNALS.values() if s.signal_type == SignalType.THREAT and s.strength > 0.3]
    if len(threat_sigs) >= 3:
        # Simple centroid clustering
        cx = statistics.mean(s.position.get("x", 0) for s in threat_sigs)
        cy = statistics.mean(s.position.get("y", 0) for s in threat_sigs)
        avg_str = statistics.mean(s.strength for s in threat_sigs)
        categories = Counter(s.category for s in threat_sigs if s.category)

        patterns.append({
            "pattern": "threat_cluster",
            "description": f"Cluster of {len(threat_sigs)} threat signals detected",
            "centroid": {"x": round(cx, 2), "y": round(cy, 2)},
            "avg_strength": round(avg_str, 4),
            "categories": dict(categories),
            "severity": "high" if avg_str > 0.6 else "medium",
        })

    # 2. Formation convergence — multiple formations targeting same area
    active_forms = [f for f in FORMATIONS.values() if f.status == FormationStatus.ACTIVE]
    if len(active_forms) >= 2:
        for i, f1 in enumerate(active_forms):
            for f2 in active_forms[i + 1:]:
                dist = _distance(f1.target_position, f2.target_position)
                if dist < 30:
                    patterns.append({
                        "pattern": "formation_convergence",
                        "description": f"Formations '{f1.name}' and '{f2.name}' converging",
                        "distance": round(dist, 2),
                        "combined_agents": len(f1.member_ids) + len(f2.member_ids),
                        "severity": "medium",
                    })

    # 3. Agent specialisation drift — agents clustering in unexpected roles
    role_counts = Counter(a.role.value for a in AGENTS.values())
    dominant = role_counts.most_common(1)
    if dominant and dominant[0][1] > len(AGENTS) * 0.5:
        patterns.append({
            "pattern": "role_concentration",
            "description": f"Over 50% of agents have role '{dominant[0][0]}'",
            "role": dominant[0][0],
            "count": dominant[0][1],
            "total_agents": len(AGENTS),
            "severity": "low",
        })

    # 4. Signal saturation — too many signals in a region
    all_sigs = list(SIGNALS.values())
    if len(all_sigs) > 20:
        patterns.append({
            "pattern": "signal_saturation",
            "description": f"{len(all_sigs)} active signals — potential noise overload",
            "signal_count": len(all_sigs),
            "avg_strength": round(statistics.mean(s.strength for s in all_sigs), 4),
            "severity": "medium",
        })

    return patterns


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

def _seed() -> None:
    seed_agents = [
        ("Alpha-Scout-01", AgentRole.SCOUT, "NAIL", ["prompt_injection", "guardrail_bypass"]),
        ("Alpha-Scout-02", AgentRole.SCOUT, "NAIL", ["tool_misuse", "supply_chain_compromise"]),
        ("Beta-Sentinel-01", AgentRole.SENTINEL, "Acme AI", ["data_exfiltration", "memory_poisoning"]),
        ("Beta-Sentinel-02", AgentRole.SENTINEL, "Acme AI", ["privilege_escalation", "identity_spoofing"]),
        ("Gamma-Responder-01", AgentRole.RESPONDER, "NAIL", ["prompt_injection", "tool_misuse", "data_exfiltration"]),
        ("Gamma-Responder-02", AgentRole.RESPONDER, "EuroBank", ["multi_agent_manipulation", "goal_hijacking"]),
        ("Delta-Analyst-01", AgentRole.ANALYST, "NAIL", AVE_CATEGORIES[:6]),
        ("Delta-Analyst-02", AgentRole.ANALYST, "GovSecure", AVE_CATEGORIES[6:12]),
        ("Epsilon-Coordinator-01", AgentRole.COORDINATOR, "NAIL", AVE_CATEGORIES[:9]),
        ("Zeta-Healer-01", AgentRole.HEALER, "NAIL", ["resource_exhaustion", "context_overflow"]),
        ("Zeta-Healer-02", AgentRole.HEALER, "HealthFirst", ["alignment_subversion", "reward_hacking"]),
        ("Eta-Scout-01", AgentRole.SCOUT, "NAIL", ["capability_elicitation", "delegation_abuse"]),
    ]

    for i, (name, role, org, specs) in enumerate(seed_agents):
        agent = SwarmAgent(
            name=name,
            role=role,
            organisation=org,
            specialisation=specs,
            fitness=round(random.uniform(0.6, 0.95), 2),
            position={"x": round(random.uniform(-100, 100), 1), "y": round(random.uniform(-100, 100), 1)},
        )
        AGENTS[agent.id] = agent

    # Seed some signals
    agent_ids = list(AGENTS.keys())
    for _ in range(8):
        emitter = AGENTS[random.choice(agent_ids)]
        sig = StigmergicSignal(
            emitter_id=emitter.id,
            signal_type=random.choice(list(SignalType)),
            category=random.choice(AVE_CATEGORIES[:8]),
            strength=round(random.uniform(0.3, 1.0), 2),
            position={"x": emitter.position["x"] + random.uniform(-10, 10),
                       "y": emitter.position["y"] + random.uniform(-10, 10)},
        )
        SIGNALS[sig.id] = sig
        emitter.signals_emitted += 1


_seed()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    active_sigs = [s for s in SIGNALS.values() if s.strength > 0.1]
    return {
        "status": "healthy",
        "service": "collective-intelligence-swarm",
        "version": "1.0.0",
        "agents": len(AGENTS),
        "active_signals": len(active_sigs),
        "formations": len([f for f in FORMATIONS.values() if f.status == FormationStatus.ACTIVE]),
        "consensus_rounds": len(CONSENSUS_ROUNDS),
    }


# ---- Agents --------------------------------------------------------------

@app.post("/v1/agents", status_code=status.HTTP_201_CREATED)
async def register_agent(data: AgentCreate):
    for cat in data.specialisation:
        if cat not in AVE_CATEGORIES:
            raise HTTPException(400, f"Invalid specialisation category: {cat}")
    agent = SwarmAgent(
        name=data.name,
        role=data.role,
        organisation=data.organisation,
        specialisation=data.specialisation,
        position=data.position,
    )
    AGENTS[agent.id] = agent
    return {"id": agent.id, "name": agent.name, "role": agent.role.value}


@app.get("/v1/agents")
async def list_agents(
    role: Optional[AgentRole] = None,
    state: Optional[AgentState] = None,
    organisation: Optional[str] = None,
):
    agents = list(AGENTS.values())
    if role:
        agents = [a for a in agents if a.role == role]
    if state:
        agents = [a for a in agents if a.state == state]
    if organisation:
        agents = [a for a in agents if a.organisation == organisation]
    return {
        "count": len(agents),
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role.value,
                "state": a.state.value,
                "organisation": a.organisation,
                "fitness": a.fitness,
                "specialisation": a.specialisation,
                "position": a.position,
                "current_formation": a.current_formation,
            }
            for a in agents
        ],
    }


@app.get("/v1/agents/{agent_id}")
async def get_agent(agent_id: str):
    if agent_id not in AGENTS:
        raise HTTPException(404, "Agent not found")
    return AGENTS[agent_id].dict()


# ---- Signals -------------------------------------------------------------

@app.post("/v1/signals/emit", status_code=status.HTTP_201_CREATED)
async def emit_signal(data: SignalEmit):
    if data.emitter_id not in AGENTS:
        raise HTTPException(404, "Emitter agent not found")
    if data.category and data.category not in AVE_CATEGORIES:
        raise HTTPException(400, f"Invalid category: {data.category}")

    sig = StigmergicSignal(
        emitter_id=data.emitter_id,
        signal_type=data.signal_type,
        category=data.category,
        strength=data.strength,
        position=data.position,
        radius=data.radius,
        data=data.data,
    )
    SIGNALS[sig.id] = sig

    emitter = AGENTS[data.emitter_id]
    emitter.signals_emitted += 1
    emitter.last_active = _now().isoformat()

    # Notify agents in radius
    nearby = _agents_in_radius(data.position, data.radius)
    for agent in nearby:
        if agent.id != data.emitter_id:
            agent.signals_received += 1

    return {
        "id": sig.id,
        "signal_type": sig.signal_type.value,
        "strength": sig.strength,
        "agents_reached": len(nearby) - 1,
    }


@app.get("/v1/signals")
async def read_signals(
    signal_type: Optional[SignalType] = None,
    category: Optional[str] = None,
    min_strength: float = Query(0.0, ge=0.0, le=1.0),
):
    sigs = [s for s in SIGNALS.values() if s.strength >= min_strength]
    if signal_type:
        sigs = [s for s in sigs if s.signal_type == signal_type]
    if category:
        sigs = [s for s in sigs if s.category == category]
    sigs.sort(key=lambda s: s.strength, reverse=True)
    return {"count": len(sigs), "signals": [s.dict() for s in sigs]}


@app.post("/v1/signals/decay")
async def decay_signals():
    """Apply one decay cycle to all signals. Remove expired signals."""
    decayed = 0
    removed = 0
    to_remove: list[str] = []

    for sid, sig in SIGNALS.items():
        sig.strength = round(max(0, sig.strength - sig.decay_rate), 4)
        decayed += 1
        if sig.strength <= 0.01:
            to_remove.append(sid)

    for sid in to_remove:
        del SIGNALS[sid]
        removed += 1

    return {"decayed": decayed, "removed": removed, "remaining": len(SIGNALS)}


# ---- Formations ----------------------------------------------------------

@app.post("/v1/formations", status_code=status.HTTP_201_CREATED)
async def create_formation(data: FormationCreate):
    if data.target_category and data.target_category not in AVE_CATEGORIES:
        raise HTTPException(400, f"Invalid target category: {data.target_category}")

    formation = Formation(
        name=data.name,
        formation_type=data.formation_type,
        target_category=data.target_category,
        target_position=data.target_position,
        min_agents=data.min_agents,
        max_agents=data.max_agents,
    )
    FORMATIONS[formation.id] = formation

    recruited: list[str] = []
    if data.recruit_from_idle:
        recruited = _recruit_for_formation(formation)

    return {
        "id": formation.id,
        "name": formation.name,
        "type": formation.formation_type.value,
        "status": formation.status.value,
        "recruited": len(recruited),
        "members": len(formation.member_ids),
        "effectiveness": formation.effectiveness,
        "leader_id": formation.leader_id,
    }


@app.get("/v1/formations")
async def list_formations(
    formation_type: Optional[FormationType] = None,
    formation_status: Optional[FormationStatus] = Query(None, alias="status"),
):
    forms = list(FORMATIONS.values())
    if formation_type:
        forms = [f for f in forms if f.formation_type == formation_type]
    if formation_status:
        forms = [f for f in forms if f.status == formation_status]
    return {
        "count": len(forms),
        "formations": [
            {
                "id": f.id,
                "name": f.name,
                "type": f.formation_type.value,
                "status": f.status.value,
                "members": len(f.member_ids),
                "effectiveness": f.effectiveness,
                "leader_id": f.leader_id,
                "target_category": f.target_category,
            }
            for f in forms
        ],
    }


@app.get("/v1/formations/{form_id}")
async def get_formation(form_id: str):
    if form_id not in FORMATIONS:
        raise HTTPException(404, "Formation not found")
    return FORMATIONS[form_id].dict()


# ---- Consensus -----------------------------------------------------------

@app.post("/v1/consensus", status_code=status.HTTP_201_CREATED)
async def initiate_consensus(data: ConsensusCreate):
    consensus = ConsensusRound(
        topic=data.topic,
        category=data.category,
        options=data.options,
        quorum_pct=data.quorum_pct,
    )

    if data.auto_vote:
        _auto_vote(consensus)

    CONSENSUS_ROUNDS[consensus.id] = consensus

    return {
        "id": consensus.id,
        "topic": consensus.topic,
        "status": consensus.status.value,
        "result": consensus.result,
        "confidence": consensus.confidence,
        "votes": len(consensus.votes),
        "total_agents": len(AGENTS),
    }


@app.get("/v1/consensus")
async def list_consensus(
    consensus_status: Optional[ConsensusStatus] = Query(None, alias="status"),
):
    rounds = list(CONSENSUS_ROUNDS.values())
    if consensus_status:
        rounds = [r for r in rounds if r.status == consensus_status]
    return {
        "count": len(rounds),
        "rounds": [
            {
                "id": r.id,
                "topic": r.topic,
                "status": r.status.value,
                "result": r.result,
                "confidence": r.confidence,
                "votes": len(r.votes),
            }
            for r in rounds
        ],
    }


@app.get("/v1/consensus/{round_id}")
async def get_consensus(round_id: str):
    if round_id not in CONSENSUS_ROUNDS:
        raise HTTPException(404, "Consensus round not found")
    return CONSENSUS_ROUNDS[round_id].dict()


# ---- Emergence -----------------------------------------------------------

@app.get("/v1/emergence")
async def detect_emergence():
    patterns = _detect_emergence()
    return {
        "patterns_detected": len(patterns),
        "patterns": patterns,
        "swarm_size": len(AGENTS),
        "active_signals": len([s for s in SIGNALS.values() if s.strength > 0.1]),
    }


# ---- Analytics -----------------------------------------------------------

@app.get("/v1/analytics")
async def swarm_analytics():
    agents = list(AGENTS.values())
    sigs = list(SIGNALS.values())
    forms = list(FORMATIONS.values())
    rounds = list(CONSENSUS_ROUNDS.values())

    by_role = Counter(a.role.value for a in agents)
    by_state = Counter(a.state.value for a in agents)
    by_org = Counter(a.organisation for a in agents)
    by_sig_type = Counter(s.signal_type.value for s in sigs)
    by_form_type = Counter(f.formation_type.value for f in forms)
    by_form_status = Counter(f.status.value for f in forms)

    avg_fitness = round(statistics.mean(a.fitness for a in agents), 4) if agents else 0.0
    avg_sig_strength = round(statistics.mean(s.strength for s in sigs), 4) if sigs else 0.0

    # Diversity index (Simpson's)
    total = len(agents)
    diversity = 0.0
    if total > 1:
        diversity = 1 - sum(
            (n / total) ** 2 for n in by_role.values()
        )
        diversity = round(diversity, 4)

    # Signal entropy
    sig_types = [s.signal_type.value for s in sigs]
    entropy = 0.0
    if sig_types:
        total_sigs = len(sig_types)
        for count in Counter(sig_types).values():
            p = count / total_sigs
            if p > 0:
                entropy -= p * math.log2(p)
        entropy = round(entropy, 4)

    consensus_success = sum(1 for r in rounds if r.status == ConsensusStatus.REACHED)

    return {
        "total_agents": len(agents),
        "by_role": dict(by_role),
        "by_state": dict(by_state),
        "by_organisation": dict(by_org),
        "avg_fitness": avg_fitness,
        "diversity_index": diversity,
        "total_signals": len(sigs),
        "by_signal_type": dict(by_sig_type),
        "avg_signal_strength": avg_sig_strength,
        "signal_entropy": entropy,
        "total_formations": len(forms),
        "active_formations": sum(1 for f in forms if f.status == FormationStatus.ACTIVE),
        "by_formation_type": dict(by_form_type),
        "by_formation_status": dict(by_form_status),
        "total_consensus_rounds": len(rounds),
        "consensus_reached": consensus_success,
        "consensus_rate": round(consensus_success / len(rounds), 4) if rounds else 0.0,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8901)
