# Policy Compiler

**Phase 26 — Service 1 of 5 · Port `9905`**

Declarative policy-to-code compiler that translates natural language governance
rules into executable enforcement logic with syntax validation, semantic
analysis, conflict detection, and automated test generation.

---

## Key Capabilities

| Capability | Detail |
|-----------|--------|
| **Policy Ingestion** | Create policies with natural language rules, target_domain (access_control/data_handling/ai_governance/privacy/security/compliance), scope (global/organisation/team/service), enforcement_mode (enforce/audit/dry_run) |
| **Rule Parsing** | Parse natural language rules into structured AST: subject + action + resource + condition + effect (allow/deny/require/restrict/log); supports AND/OR/NOT operators, numeric comparisons, temporal conditions |
| **Compilation Pipeline** | 5-stage pipeline: parse → validate → optimise → compile → test; each stage produces artefacts; configurable optimisation level (0-3) |
| **Compiled Output** | 4 output formats: python_function / rego (Open Policy Agent) / json_rule / pseudocode; each includes enforcement function signature + dependencies |
| **Semantic Validation** | Detect ambiguities (vague subjects/actions), contradictions (conflicting effects for same condition), unreachable rules (shadowed by higher-priority rules), circular dependencies |
| **Conflict Detection** | Cross-policy conflict scanning: direct_contradiction / scope_overlap / precedence_ambiguity; per-conflict severity + resolution suggestion |
| **Auto-Test Generation** | Generate test cases per compiled rule: positive (should trigger), negative (should not trigger), boundary (edge conditions); expected result per test |
| **Policy Versioning** | Semantic versioning with diff between versions; changelog auto-generation from rule changes |
| **Deployment** | Deploy compiled policies to target (simulated): deployment_id + target_environment + status (pending/deployed/rolled_back) + rollback capability |
| **Analytics** | Policies by domain/scope/enforcement, compilation success rate, conflict density, test coverage |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + stats |
| `POST` | `/v1/policies` | Create policy with natural language rules |
| `GET` | `/v1/policies` | List policies (filter by domain/scope/status) |
| `GET` | `/v1/policies/{id}` | Get policy detail |
| `POST` | `/v1/policies/{id}/compile` | Compile policy through pipeline |
| `GET` | `/v1/policies/{id}/compiled` | Get compiled artefacts |
| `POST` | `/v1/policies/{id}/validate` | Semantic validation |
| `POST` | `/v1/policies/{id}/test` | Generate + run tests |
| `POST` | `/v1/policies/{id}/deploy` | Deploy compiled policy |
| `POST` | `/v1/conflicts/scan` | Cross-policy conflict scan |
| `GET` | `/v1/analytics` | Comprehensive analytics |

## Running Locally

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 9905 --reload
```

> **Production note:** Replace simulated compilation with real OPA/Cedar integration; add Git-backed policy versioning.
