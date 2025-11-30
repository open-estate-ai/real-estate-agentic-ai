# Shared Modules

Shared code for all agents: database, utils, etc.

## Setup

Add to your agent's `pyproject.toml`:

```toml
dependencies = ["real-estate-shared"]

[tool.uv.sources]
real-estate-shared = { path = "../../shared", editable = true }
```

Run: `uv sync`

## Usage

```python
from database import JobRepository, JobStatus, JobType, get_db_session, init_db
```

See [`database/README.md`](database/README.md) for database module details.
