# ⚛️ Quantum-Enhanced Agentic AI Security

> First empirical evidence that quantum optimization finds superior defence
> parameters for multi-agent AI systems.

---

## Overview

The NAIL Institute runs quantum experiments on the **NVIDIA DGX Spark**
(arm64, 128 GB unified memory) using PennyLane + cuQuantum GPU simulation
to explore quantum advantages in agentic AI security.

## Experiments

| # | Experiment | Qubits | Key Result | Status |
|---|-----------|--------|------------|--------|
| 1 | [QAOA Threshold Optimizer](./results/phase1_qaoa_optimization.md) | 20 | **+3.1% fitness**, +17.6% accuracy over GA | ✅ Complete |
| 2a | [Hybrid QNN Classifier](./results/phase2a_hybrid_qnn.md) | 8 | **84.2% accuracy**, 100% on 3/6 pathology classes | ✅ Complete |
| 2b | [Quantum Kernel SVM](./results/phase2b_quantum_kernel.md) | 8 | 54.2% (quantum kernel underperformed) | ✅ Complete |
| 3 | [Robustness Certification](./results/phase3_robustness_cert.md) | 12 | **Gold certified** (99% CI: 97.4%–100%) | ✅ Complete |
| 4 | [QAOA Multi-Agent Coordinator](./results/phase4_qaoa_coordinator.md) | 20 | Optimal 6-agent × 8-task allocation | ✅ Complete |
| 5 | [Quantum Risk Scoring](./results/phase5_risk_scoring.md) | 6 | **85% accuracy** on 4-tier risk classification | ✅ Complete |

## Key Finding

The QAOA optimizer discovered that **`memory_decay_rate` and `alert_cooldown` are
strongly correlated** — faster memory decay needs longer alert cooldowns to prevent
cascade false positives. The GA's crossover/mutation operators had no mechanism to
discover this inter-parameter correlation. The quantum circuit's entangling layers
found it in 150 gradient steps.

## Hardware

| Component | Version |
|-----------|---------|
| Platform | NVIDIA DGX Spark |
| Architecture | arm64, 128 GB unified memory |
| CUDA | 12.9 |
| cuQuantum | 26.01.0 |
| PennyLane | 0.44.1 |
| Lightning GPU | 0.44.0 |
| Qubit capacity | ~33 (state vector), 40+ (tensor network) |

## Publications

- 📄 [**Research Paper**](./paper/quantum_enhanced_defence_optimization.md) — Full arXiv-style paper
- 📊 [**Experiment Results**](./results/) — Individual experiment summaries
- 🖼️ [**Visualizations**](./visualizations/) — Convergence plots, comparison charts
- ⚙️ [**Staging Config**](./staging/quantum_thresholds.json) — Deployable quantum-optimized thresholds

## Citation

```bibtex
@article{leigh2026quantum,
  title   = {Quantum-Enhanced Defence Parameter Optimization for Multi-Agent AI Systems},
  author  = {Leigh, Dillman},
  journal = {NAIL Institute Technical Report},
  year    = {2026},
  note    = {Available at https://github.com/NAIL-INSTITUTE-FOR-AGENTIC-SECURITY/ave-database/tree/main/quantum}
}
```

## License

All quantum research content is licensed under [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/).
