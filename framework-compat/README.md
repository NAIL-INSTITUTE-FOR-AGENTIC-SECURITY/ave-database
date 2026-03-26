# 🔌 Cross-Framework Compatibility Layer

> Universal defence adapter enabling guardrails to work across LangChain,
> CrewAI, AutoGen, LlamaIndex, and custom agent frameworks.

**Phase 13 · Item 4 · Port 8703**

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    CROSS-FRAMEWORK COMPATIBILITY LAYER                    │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ Adapter  │ Defence  │ Guard-   │ Hook     │ Config   │ Telemetry           │
│ Registry │ Unifier  │ rail     │ Manager  │ Transl-  │ Aggregator          │
│          │ (ADL)    │ Router   │          │ ator     │                     │
├──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────────┤
│                   ABSTRACT DEFENCE LANGUAGE (ADL)                         │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ LangChain│ CrewAI   │ AutoGen  │ LlamaIdx │ Custom   │ Native              │
│ Adapter  │ Adapter  │ Adapter  │ Adapter  │ Adapter  │ SDK                 │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────────┘
```

## Concepts

| Concept | Description |
|---------|-------------|
| **Abstract Defence Language (ADL)** | Framework-agnostic guardrail specification format |
| **Adapter** | Translates ADL into framework-specific hooks, middleware, or callbacks |
| **Defence Profile** | Collection of guardrails bundled for a specific use case |
| **Hook Point** | Framework lifecycle event where guardrails can inject (pre/post/error) |
| **Config Translator** | Converts between framework-native configs and ADL format |
| **Telemetry Aggregator** | Normalises guardrail metrics across frameworks |

## Supported Frameworks

| Framework | Adapter | Hook Points | Status |
|-----------|---------|-------------|--------|
| LangChain | `langchain_adapter` | callbacks, tool pre/post, chain pre/post | ✅ Full |
| CrewAI | `crewai_adapter` | task pre/post, agent lifecycle, tool exec | ✅ Full |
| AutoGen | `autogen_adapter` | message filter, code exec, reply hook | ✅ Full |
| LlamaIndex | `llamaindex_adapter` | query pre/post, retrieval filter, synth post | ✅ Full |
| Custom | `custom_adapter` | user-defined hook points via ADL schema | ✅ Full |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health |
| `GET` | `/v1/adapters` | List registered adapters |
| `GET` | `/v1/adapters/{fw}` | Adapter details for framework |
| `POST` | `/v1/defences` | Create ADL defence definition |
| `GET` | `/v1/defences` | List defences |
| `GET` | `/v1/defences/{id}` | Defence details |
| `POST` | `/v1/defences/{id}/translate` | Translate defence to framework-native config |
| `POST` | `/v1/profiles` | Create a defence profile |
| `GET` | `/v1/profiles` | List defence profiles |
| `GET` | `/v1/profiles/{id}` | Profile details |
| `POST` | `/v1/profiles/{id}/deploy` | Deploy profile to target framework |
| `GET` | `/v1/hooks/{fw}` | List available hook points for framework |
| `POST` | `/v1/validate` | Validate ADL definition |
| `GET` | `/v1/telemetry` | Aggregated cross-framework telemetry |
| `GET` | `/v1/compatibility-matrix` | Framework × defence compatibility |

## Running

```bash
pip install fastapi uvicorn pydantic
uvicorn server:app --host 0.0.0.0 --port 8703 --reload
```

Docs at http://localhost:8703/docs
