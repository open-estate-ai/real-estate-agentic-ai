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
| Planner | [backend/agents/planner](backend/agents/planner/README.md) | **Active** | **Analyzes queries, creates execution plans, generates child jobs** |
| Search | (planned) | Planned | Listing retrieval, geo expansion, ranking |
| Valuation | (planned) | Planned | Market value & comparable analysis |
| Legal | (planned) | Planned | Compliance & registry checks |
| Verification | (planned) | Planned | Data integrity / fraud / anomaly signals |
| Summarizer | (planned) | Planned | Consolidate multi-agent outputs |

---

## Quick Start (Local Development)

Test the planner agent locally with Tilt:

```bash
# 1. Set up environment
cp .env.tmpl .env
# Edit .env with your credentials

# 2. Start Tilt (PostgreSQL + Planner Agent)
tilt up

# 3. Test the agent
cd backend/agents/planner
python test_planner.py

# Or manually:
curl -X POST http://localhost:8081/plan \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test-1", "query": "Find 3BHK in Noida", "user_id": "user-1"}'
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

---

## Shared Infrastructure

### Database

All agents share a PostgreSQL database for job coordination:

- **Jobs Table**: Tracks all agent executions
- **Connection pooling**: SQLAlchemy with configurable pool size
- **Local dev**: PostgreSQL in Docker (via docker-compose)
- **Production**: AWS RDS

See [backend/shared/database/README.md](backend/shared/database/README.md) for details.

### Development with Tilt

Tilt provides:
- Hot-reload for code changes
- Unified dashboard for all services
- Local Kubernetes environment
- Easy debugging and logs

Access Tilt UI: http://localhost:10350

---

## Project Structure

```
real-estate-agentic-ai/
├── backend/
│   ├── agents/
│   │   └── planner/              # ✅ Active agent
│   │       ├── src/
│   │       │   ├── main.py       # FastAPI app
│   │       │   └── planner.py    # LLM-based planning logic
│   │       ├── k8s/              # Kubernetes manifests
│   │       ├── Dockerfile
│   │       ├── pyproject.toml
│   │       └── README.md
│   └── shared/
│       └── database/             # Shared DB module
│           ├── connection.py     # Connection management
│           ├── models.py         # Job model
│           ├── repository.py     # CRUD operations
│           └── migrations/       # SQL migrations
├── docker-compose.yml            # PostgreSQL service
├── Tiltfile                      # Tilt configuration
├── .env.tmpl                     # Environment template
├── QUICKSTART.md                 # Getting started guide
└── README.md                     # This file
```

