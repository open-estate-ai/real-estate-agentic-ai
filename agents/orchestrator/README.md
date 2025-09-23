
cd /agents/orchestrator
uv sync

uv run python -m orchestrator.main



Test client
uv run python src/client/test_client.py



References
https://a2a-protocol.org/latest/



brew install podman
podman machine init
podman machine start
podman info


https://podman.io/docs/installation
podman build . -t orchestrator-server
podman run -p 9999:9999 orchestrator-server


podman run -p 9999:9999 --env-file ./.env orchestrator-server