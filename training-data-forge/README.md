# Synthetic Training Data Forge

**Phase 22 — Service 4 of 5 · Port `9603`**

Privacy-preserving synthetic data generation for security training with
differential privacy guarantees, fidelity scoring, and configurable
generation pipelines.

---

## Core Concepts

### Datasets
A **dataset** represents a collection of real-world samples that serve as the
statistical basis for synthetic generation. Datasets are never exposed directly —
only their statistical profile is used.

### Generation Pipelines
A **pipeline** takes a source dataset and produces synthetic records:
1. **Profile** the source (distributions, correlations, schema)
2. **Apply differential privacy** (Laplace noise with configurable ε, δ)
3. **Generate** synthetic records matching the profiled distributions
4. **Score fidelity** against the original (without leaking originals)
5. **Validate privacy** — membership inference resistance check

### Differential Privacy Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `epsilon` | 1.0 | Privacy budget — lower = more private |
| `delta` | 1e-5 | Probability of privacy breach |
| `noise_mechanism` | `laplace` | Also supports `gaussian` |
| `sensitivity` | 1.0 | Query sensitivity |

### Fidelity Metrics
- **statistical_similarity** — KL-divergence between real & synthetic distributions
- **correlation_preservation** — Pearson correlation matrix comparison
- **schema_compliance** — percentage of records matching expected schema
- **utility_score** — downstream task performance on synthetic vs real data

### Privacy Audit
Each generation run produces a **privacy audit** confirming:
- Noise was correctly applied
- No raw records leaked into output
- Membership inference attack success rate < threshold

---

## Data Model

### Pipeline States
`configured` → `profiling` → `generating` → `scoring` → `completed` | `failed`

### Generation Strategies
`statistical_sampling` | `copula_based` | `marginal_based` | `gan_simulated`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/datasets` | Register source dataset |
| `GET` | `/v1/datasets` | List datasets |
| `POST` | `/v1/pipelines` | Create generation pipeline |
| `GET` | `/v1/pipelines` | List pipelines |
| `POST` | `/v1/pipelines/{id}/run` | Execute pipeline |
| `GET` | `/v1/pipelines/{id}/output` | Retrieve synthetic records |
| `GET` | `/v1/pipelines/{id}/fidelity` | Fidelity report |
| `GET` | `/v1/pipelines/{id}/privacy-audit` | Privacy audit report |
| `GET` | `/v1/analytics` | Cross-pipeline analytics |

---

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9603
```

---

*Part of the NAIL Institute AVE Database — Phase 22: Adaptive Learning & Evolutionary Defence*
