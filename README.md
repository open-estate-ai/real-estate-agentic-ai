# real-estate-agentic-ai

Agentic AI workflows that classify intent, plan tasks, and orchestrate
specialized real estate domain agents to produce actionable insights (search,
valuation, legal checks, verification, summarization).

## Why

Real estate questions are multi-step: users want availability + pricing +
compliance + context. A single LLM prompt is brittle. This project builds a
composable agent layer that can classify, plan, execute, and trace results
across data and model boundaries.

---

## High-Level Flow

1. User query → Orchestrator receives request
2. Intent Classifier extracts intent + slots (city, budget, purpose, etc.)
3. (Planned) Planner builds a DAG of agent tasks
4. Search Agent retrieves listings & related context (market stats, geo
  expansion)
5. Specialized agents (valuation, legal, verification) enrich / validate
6. Summarizer Agent returns structured + narrative result

Refer Architecture [here](https://open-estate-ai.github.io/real-estate-docs/architecture/overview/)

---

## Agents

| Agent | Path | Status | Description |
|-------|------|--------|-------------|
| Orchestrator | [agents/orchestrator](agents/orchestrator/README.md) | Active | Receives query, classifies intent (current) and will route tasks |
| Planner | (planned) | Planned | Build task DAG based on intent + slots |
| Search | (planned) | Planned | Listing retrieval, geo expansion, ranking |
| Valuation | (planned) | Planned | Market value & comparable analysis |
| Legal | (planned) | Planned | Compliance & registry checks |
| Verification | (planned) | Planned | Data integrity / fraud / anomaly signals |
| Summarizer | (planned) | Planned | Consolidate multi-agent outputs |

