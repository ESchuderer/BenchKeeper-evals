FROM docker.io/library/node:22.23.3-bookworm-slim@sha256:efd0ab5780c2d9ab1f0f869571a00d5edb17793bff4cce4a2792e3eb0ffc7562
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates bubblewrap socat ripgrep && rm -rf /var/lib/apt/lists/*
USER node
