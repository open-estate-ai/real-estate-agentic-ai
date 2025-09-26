
## Search Listings Agent

Specialized real estate search service that finds property listings based on  
user criteria. Receives search parameters and returns structured property  
candidates with detailed information. This is the local development setup for  
the Search Listings Agent inside the `real-estate-agentic-ai` monorepo.

### What it does (current state)

* Starts an HTTP server (A2A protocol) on port 9001
* Exposes an agent card with search-specific metadata
* Processes search payloads with property criteria (type, budget, location, etc.)
* Returns up to 25 high-quality property candidates with structured data
* Handles edge cases like missing budget or vague location terms

### Planned (next)

* Integration with real property data providers (99acres, MagicBricks, etc.)
* Advanced filtering and ranking algorithms
* Geospatial search capabilities
* Price trend analysis integration

---

## Quick Start (Local)

From repo root or this directory:

```sh
cd agents/search_listings
uv sync
uv run python -m search_listings.main
```

Server will start on: <http://localhost:9001/>

### Test Client

```sh
uv run python src/client/test_client.py
```

---

## Environment Variables

Copy the example file and edit if needed:

```sh
cp .env.tmpl .env
```

Variables (current minimal):

* OPENAI_API_KEY – required for search agent LLM processing

The code loads `.env` automatically.

---

## Podman / Container Run

Build image:

```sh
podman build . -t search-listings-server
```

Run container (no env):

```sh
podman run -p 9001:9001 search-listings-server
```

Run with env file:

```sh
podman run -p 9001:9001 --env-file ./.env search-listings-server
```

If Podman not installed:

```sh
brew install podman
podman machine init
podman machine start
podman info
```

---

## Project Layout

```text
agents/search_listings/
    Containerfile
    pyproject.toml
    uv.lock
    src/
        search_listings/
            main.py        # Entry point (uvicorn startup)
            agent.py       # Search listings logic
            config.py      # Env var validation
            executor.py    # Wiring request handling to agent
            models/search.py
        client/test_client.py
```

---

## A2A Protocol Reference

Docs: <https://a2a-protocol.org/latest/>

---

## Troubleshooting

* Missing OPENAI_API_KEY → set it in `.env`
* Port already in use → change `port` in `main.py` or free 9001
* Dependency issues → remove `.venv` and re-run `uv sync`
* Timeout errors → check search complexity, increase client timeout
* No search results → verify search criteria format and data sources

---

## License

See repository root for license information.
