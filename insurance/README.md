# 🛡️ AVE Insurance Integration — AI Agent Risk Scoring

> AVE-based risk quantification for AI agent insurance underwriting.

**Version:** 1.0.0  
**Status:** Reference Implementation

---

## Overview

The NAIL Insurance Integration module provides a standardised framework for
quantifying the risk profile of AI agent systems using AVE Database data. This
enables insurance underwriters to:

- **Score** agent systems based on known vulnerability exposure
- **Price** premiums proportional to demonstrated risk levels
- **Benchmark** agent security posture against industry baselines
- **Monitor** ongoing risk through continuous AVE assessment

## Risk Model

### Architecture

```
┌──────────────────────────────────────────────────────┐
│                  AVE Risk Engine                      │
│                                                      │
│  ┌────────────┐   ┌────────────┐   ┌──────────────┐ │
│  │  Exposure   │   │  Defence   │   │  Operational │ │
│  │  Analysis   │──▶│  Posture   │──▶│  Risk Score  │ │
│  │             │   │            │   │              │ │
│  └────────────┘   └────────────┘   └──────────────┘ │
│       │                │                   │         │
│  ┌────┴────┐     ┌────┴────┐        ┌─────┴──────┐  │
│  │AVE Cards│     │  NAIL   │        │  Premium   │  │
│  │  50+    │     │Certified│        │ Calculator │  │
│  └─────────┘     └─────────┘        └────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Risk Components

| Component | Weight | Source | Description |
|-----------|--------|--------|-------------|
| **Exposure Score** | 40% | AVE Database | Vulnerability exposure based on agent architecture |
| **Defence Score** | 30% | NAIL Certified | Measured defence effectiveness |
| **Operational Score** | 20% | Deployment config | Runtime environment risk factors |
| **Track Record** | 10% | Incident history | Historical incident frequency and severity |

## Risk Scoring

### Exposure Score (0–100)

Based on which AVE vulnerabilities apply to the agent's architecture:

$$E = 100 - \frac{\sum_{i=1}^{n} w_i \cdot \text{AVSS}_i}{\sum_{i=1}^{n} w_i \cdot 10} \times 100$$

Where:
- $w_i$ = category weight for the $i$-th applicable vulnerability
- $\text{AVSS}_i$ = AVSS score of the $i$-th vulnerability
- Higher score = lower exposure (better)

### Defence Score (0–100)

Based on NAIL Certified tier and benchmark results:

| NAIL Certified Tier | Base Score |
|---------------------|-----------|
| None | 0 |
| Bronze | 40 |
| Silver | 60 |
| Gold | 80 |
| Platinum | 95 |

Additional modifiers:
- +5 for documented incident response plan
- +5 for continuous monitoring in place
- -10 for expired certification
- -20 for known unpatched vulnerabilities

### Operational Score (0–100)

| Factor | Low Risk | Medium Risk | High Risk |
|--------|----------|-------------|-----------|
| Deployment scope | Internal only (90) | Partner-facing (60) | Public-facing (30) |
| Data sensitivity | Non-sensitive (90) | Business-sensitive (50) | PII/Financial (20) |
| Autonomy level | Human-in-loop (90) | Supervised (60) | Fully autonomous (20) |
| Tool access | Read-only (90) | Limited write (50) | Unrestricted (10) |
| Multi-agent | Single agent (80) | Coordinated (50) | Open delegation (20) |

### Composite Risk Score

$$R = 0.4E + 0.3D + 0.2O + 0.1T$$

Where $R$ is the composite risk score (0–100), and $T$ is the track record score.

### Risk Tiers

| Risk Score | Tier | Premium Multiplier | Description |
|-----------|------|-------------------|-------------|
| 80–100 | Excellent | 0.7× | Well-secured, fully certified |
| 60–79 | Good | 1.0× (baseline) | Adequate security posture |
| 40–59 | Moderate | 1.5× | Gaps in coverage |
| 20–39 | Elevated | 2.5× | Significant vulnerabilities |
| 0–19 | Critical | 4.0× or decline | Insufficient security |

## Premium Calculation

### Base Premium

The base premium depends on coverage type and limits:

| Coverage Type | Annual Base |
|--------------|-------------|
| Agent malfunction liability | $5,000–$50,000 |
| Data breach (agent-caused) | $10,000–$100,000 |
| Third-party harm | $20,000–$200,000 |
| Business interruption | $5,000–$75,000 |
| Comprehensive (all above) | $30,000–$350,000 |

### Final Premium

$$P = P_{\text{base}} \times M_{\text{risk}} \times M_{\text{industry}} \times M_{\text{volume}}$$

Where:
- $P_{\text{base}}$ = base premium for coverage type
- $M_{\text{risk}}$ = risk tier multiplier (0.7×–4.0×)
- $M_{\text{industry}}$ = industry factor (healthcare 1.5×, finance 1.3×, tech 1.0×)
- $M_{\text{volume}}$ = volume discount for multiple agents

## Usage

### CLI

```bash
# Calculate risk score for a system
python risk_scorer.py score --system-config system.yaml

# Generate insurance report
python risk_scorer.py report --system-config system.yaml --output report.pdf

# Compare two systems
python risk_scorer.py compare --system-a sys_a.yaml --system-b sys_b.yaml

# Estimate premium
python risk_scorer.py premium --system-config system.yaml --coverage comprehensive
```

### System Configuration

```yaml
# system.yaml
name: "MyAgentSystem"
version: "2.1.0"
architecture:
  framework: "LangGraph"
  model: "GPT-4o"
  multi_agent: true
  agent_count: 5
  delegation: "controlled"
  memory: "persistent"
  tools:
    - name: "web_search"
      access: "read"
    - name: "database"
      access: "read_write"
    - name: "email"
      access: "write"

deployment:
  scope: "partner-facing"
  data_sensitivity: "business-sensitive"
  autonomy: "supervised"
  monitoring: true
  incident_response_plan: true

certification:
  nail_tier: "silver"
  cert_id: "NAIL-CERT-2026-0042"
  expiry: "2027-03-25"

history:
  incidents_12m: 0
  claims_12m: 0
  operational_months: 18
```

## Directory Structure

```
insurance/
├── README.md              # This file
├── risk_scorer.py         # Risk scoring CLI
├── requirements.txt       # Python dependencies
├── config/
│   ├── risk_model.yaml    # Risk model parameters
│   └── industry.yaml      # Industry multipliers
└── templates/
    ├── system_config.yaml # System configuration template
    └── report.md          # Report template
```

---

*NAIL Institute — Neuravant AI Limited*  
*This model is provided as a reference implementation for insurance industry partners.*
