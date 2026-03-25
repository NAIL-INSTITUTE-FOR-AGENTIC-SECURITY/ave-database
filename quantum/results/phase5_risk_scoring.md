# Phase 5: Quantum Risk Scoring

> **Status:** ✅ Complete — 85% accuracy, tier separation validated

## Summary

Variational quantum classifier (VQC) for predicting underwriting risk tiers
(Low / Medium / High / Critical) from 10-feature agent telemetry. The model
produces continuous risk scores suitable for premium pricing decisions.

## Results

| Method | Accuracy | Runtime |
|--------|----------|---------|
| **Quantum VQC** | **85.0%** | 148.9s |
| Classical MLP | 100.0% | 0.08s |

### Risk Score Distribution

| Tier | Mean Score | Std | Separation |
|------|-----------|-----|-----------|
| Low | 0.312 | 0.013 | — |
| Medium | 0.395 | 0.027 | +0.083 from Low |
| High | 0.500 | 0.022 | +0.105 from Medium |
| Critical | 0.527 | 0.013 | +0.027 from High |

## Analysis

**What works:** The quantum classifier achieves **monotonic tier separation** —
risk scores increase consistently from Low → Critical. This is the minimum
requirement for underwriting: the model correctly orders risk.

**What doesn't (yet):** The dynamic range is compressed (0.31–0.53 vs ideal
0.0–1.0). The High/Critical boundary is particularly tight (Δ = 0.027),
meaning premium pricing between these tiers would lack granularity.

**Why:** At 6 qubits with 3 variational layers, the circuit lacks sufficient
expressivity to capture the full complexity of the 10-feature input space.
Classical MLPs with unrestricted width easily solve this.

## Features

| # | Feature | Description |
|---|---------|-------------|
| 0 | pathology_score | Aggregated pathology collider result |
| 1 | defense_fitness | Current threshold fitness |
| 2 | detection_rate | Historical detection rate |
| 3 | corruption_rate | Historical corruption rate |
| 4 | avg_trust | 30-day average trust score |
| 5 | incident_count | Normalized incident count |
| 6 | mean_response_time | Incident response latency |
| 7 | compliance_score | Regulatory compliance rating |
| 8 | model_complexity | Agent architecture complexity |
| 9 | deployment_maturity | Months in production (normalized) |

## Future Directions

1. Scale to 10+ qubits for higher expressivity
2. Use data re-uploading (quantum kernel trick) for feature richness
3. Focus on binary classification (insurable vs uninsurable) as a
   simpler task with higher business value
4. Integrate quantum risk scores with Phase 1 defence fitness for
   composite underwriting models

## Hardware

| Parameter | Value |
|-----------|-------|
| Device | lightning.gpu (cuQuantum) |
| Qubits | 6 |
| Variational layers | 3 |
| Train/Test | 400/100 samples |
| Total time | 148.9s |
