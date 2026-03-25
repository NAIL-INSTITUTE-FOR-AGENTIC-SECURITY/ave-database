# Phase 2b: Quantum Kernel Anomaly Detector

> **Status:** ✅ Complete — Quantum kernel underperformed classical; documented for transparency

## Summary

Quantum kernel SVM using ZZFeatureMap for pathology classification.
The quantum kernel measures similarity in exponentially large Hilbert space
and feeds to a classical SVM. At this scale, the quantum kernel did not
provide an advantage.

## Results

| Method | Accuracy | Runtime |
|--------|----------|---------|
| Quantum Kernel SVM | **54.2%** | 116.8s |
| Hybrid QNN (Phase 2a) | 84.2% | 949.6s |
| Classical NN | 96.7% | 6.2s |

### Per-Class Performance

| Class | Precision | Recall | F1 |
|-------|-----------|--------|----|
| Normal | 0.83 | 0.25 | 0.38 |
| Goal Drift | 0.36 | 0.90 | 0.51 |
| Memory Corruption | 0.70 | 0.70 | 0.70 |
| EDoS Attack | 0.79 | 0.55 | 0.65 |
| Prompt Injection | 0.52 | 0.70 | 0.60 |
| Sleeper Agent | 1.00 | 0.15 | 0.26 |

## Why It Underperformed

1. **Training data:** Only 100 samples for kernel matrix computation.
   Quantum kernels need sufficient data to build a meaningful Gram matrix.

2. **Feature map choice:** The ZZFeatureMap may not be optimal for this
   telemetry distribution. IQP or hardware-efficient maps may perform better.

3. **Class overlap:** Goal Drift's high recall (0.90) but low precision (0.36)
   suggests the quantum kernel over-generalizes certain feature regions.

## Future Directions

- Increase training size to 500+ samples
- Test alternative feature maps (IQP, hardware-efficient)
- Explore quantum kernel alignment techniques
- Focus on binary anomaly detection (normal vs. attack) rather than 6-class

## Hardware

| Parameter | Value |
|-----------|-------|
| Device | lightning.gpu (cuQuantum) |
| Qubits | 8 |
| Train/Test | 100/120 samples |
| Total time | 116.8s |
