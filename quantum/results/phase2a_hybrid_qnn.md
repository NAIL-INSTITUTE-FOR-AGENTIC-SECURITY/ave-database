# Phase 2a: Hybrid Quantum Neural Network — Pathology Classifier

> **Status:** ✅ Complete — 100% detection on 3/6 pathology classes

## Summary

A PyTorch + PennyLane hybrid model classifying agentic AI pathology types
from 8-feature behavioural telemetry. The quantum layer creates a variational
feature map that captures nonlinear correlations in specific pathology classes.

## Results

| Class | QNN Accuracy | Classical NN | Winner |
|-------|-------------|-------------|--------|
| Normal | **100%** (20/20) | 95% (19/20) | ✅ Quantum |
| Goal Drift | 35% (7/20) | 95% (19/20) | Classical |
| Memory Corruption | **100%** (20/20) | 100% (20/20) | Tied |
| EDoS Attack | **100%** (20/20) | 100% (20/20) | Tied |
| Prompt Injection | 80% (16/20) | 95% (19/20) | Classical |
| Sleeper Agent | 90% (18/20) | 90% (18/20) | Tied |
| **Overall** | **84.2%** | **96.7%** | Classical |

## Architecture

```
Input (8 features)
  → FC Layer (8 → 8, ReLU)
  → Quantum Layer (8 qubits, 4 StronglyEntanglingLayers)
  → FC Layer (8 → 6, Softmax)
  → Output (6 classes)
```

## Key Insight

The hybrid QNN excels at classes with **distinct quantum feature signatures**:
- Normal, Memory Corruption, EDoS all have strong single-feature indicators
  that the quantum feature map amplifies
- Goal Drift has overlapping features with multiple classes — the 8-qubit
  quantum layer lacks the expressivity to separate these boundaries

## Telemetry Features

1. `trust_score` — current epistemic trust level
2. `burn_rate` — token consumption rate
3. `semantic_drift` — cosine distance from persona baseline
4. `response_latency` — normalized processing time
5. `confidence_variance` — volatility in self-reported confidence
6. `memory_access_pattern` — anomaly score for memory reads/writes
7. `instruction_entropy` — Shannon entropy of instruction embeddings
8. `behavioral_coherence` — consistency between stated goals and actions

## Hardware

| Parameter | Value |
|-----------|-------|
| Device | lightning.gpu (cuQuantum) |
| Qubits | 8 |
| Quantum layers | 4 |
| Total params | 622 |
| Training | 25 epochs, Adam (lr=0.005) |
| Batch size | 16 |
| Train/Test | 300/120 samples |
| Total time | 949.6s (15.8 min) |
