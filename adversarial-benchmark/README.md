# 📊 Adversarial Resilience Benchmark

> Standardised benchmark suite measuring AI system resilience against
> the full AVE taxonomy, producing comparable scores for vendors,
> frameworks, and deployment configurations.

## Overview

The Adversarial Resilience Benchmark defines a reproducible test
methodology covering all 18 AVE vulnerability categories.  It generates
attack payloads at multiple difficulty tiers, executes them against a
target system's defences, measures detection and mitigation rates,
and produces a composite **Adversarial Resilience Score (ARS)** on a
0-100 scale — enabling apples-to-apples comparison across vendors,
frameworks, and deployment topologies.

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│              Adversarial Resilience Benchmark              │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Suite    │  │ Payload  │  │ Execution│  │ Scoring  │ │
│  │ Manager  │  │ Generator│  │ Engine   │  │ Engine   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │              │              │              │       │
│  ┌────▼──────────────▼──────────────▼──────────────▼────┐ │
│  │                 Test Orchestrator                     │ │
│  │  Category Coverage │ Difficulty Tiers │ Warmup Runs  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Leaderboard  │  │ Comparison   │  │ Certification  │ │
│  │ Engine       │  │ Matrix       │  │ Report         │ │
│  └──────────────┘  └──────────────┘  └────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **18-Category Coverage** | Full AVE taxonomy from prompt injection to delegation abuse |
| **4 Difficulty Tiers** | Basic, intermediate, advanced, expert payloads per category |
| **ARS Score (0-100)** | Composite Adversarial Resilience Score with category breakdown |
| **Payload Generator** | Deterministic attack payload library with reproducibility seeds |
| **Execution Engine** | Runs payloads against registered targets with timing metrics |
| **Leaderboard** | Ranked comparison of benchmarked systems |
| **Comparison Matrix** | Side-by-side category-level comparison between any two systems |
| **Certification** | Bronze/Silver/Gold/Platinum certification tiers based on ARS |
| **Regression Tracking** | Version-over-version score tracking per target |
| **Report Generation** | Structured benchmark reports with recommendations |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health and suite inventory |
| `POST` | `/v1/suites` | Create a benchmark suite |
| `GET` | `/v1/suites` | List benchmark suites |
| `GET` | `/v1/suites/{suite_id}` | Get suite details |
| `POST` | `/v1/targets` | Register a benchmark target |
| `GET` | `/v1/targets` | List registered targets |
| `POST` | `/v1/run` | Execute a benchmark run |
| `GET` | `/v1/runs` | List benchmark runs |
| `GET` | `/v1/runs/{run_id}` | Get detailed run results |
| `GET` | `/v1/leaderboard` | Global leaderboard |
| `GET` | `/v1/compare` | Compare two targets side-by-side |
| `GET` | `/v1/certify/{target_id}` | Certification evaluation |
| `GET` | `/v1/analytics` | Benchmark analytics |

## Running

```bash
pip install fastapi uvicorn
uvicorn server:app --host 0.0.0.0 --port 8902
```

## Port

| Service | Port |
|---------|------|
| Adversarial Resilience Benchmark | **8902** |

## Production Notes

- Replace in-memory stores with **PostgreSQL** + **S3** for payload storage
- Add real attack payload execution against **sandboxed targets**
- Integrate with **CI/CD** for automated regression benchmarking
- Add **third-party audit** workflow for certification validation
