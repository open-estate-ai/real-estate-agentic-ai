
cd /agents/orchestrator
uv sync

uv run python -m orchestrator.main



Test client
uv run python src/client/test_client.py
