# Framework Integration Guides

Hardening guides for popular agentic-AI frameworks, mapped to AVE cards.

## Guides

| Framework | Guide | Key AVE Cards |
|-----------|-------|---------------|
| LangChain | [LangChain Hardening Guide](langchain.md) | AVE-0001, 0009, 0014, 0030, 0032, 0037 |
| CrewAI | [CrewAI Hardening Guide](crewai.md) | AVE-0002, 0005, 0021, 0025, 0027, 0046 |
| AutoGen | [AutoGen Hardening Guide](autogen.md) | AVE-0007, 0012, 0024, 0039, 0040, 0043 |
| LlamaIndex | [LlamaIndex Hardening Guide](llamaindex.md) | AVE-0009, 0019, 0022, 0034, 0044, 0045 |

## Quick-Start

```python
# Install the NAIL AVE toolkit to validate your pipeline
pip install nail-ave-toolkit

from nail_ave_toolkit import scan_pipeline

# Point at your framework code
results = scan_pipeline("./my_agent_app/", framework="langchain")
print(results.summary())
```

## Contributing

Found a gap? Open a PR against [`research/framework-guides/`](https://github.com/NAIL-INSTITUTE-FOR-AGENTIC-SECURITY/ave-database/tree/main/research/framework-guides).
