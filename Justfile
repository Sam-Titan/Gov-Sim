set shell := ["bash", "-cu"]

default:
    @just --list

setup:
    cd backend && uv sync
    cd frontend && pnpm install
    @if [ -d .git ]; then lefthook install; else echo "No .git yet: run just setup again after git init to install hooks."; fi

dev:
    #!/usr/bin/env bash
    set -m
    (cd backend && uv run uvicorn app.main:app --reload --port 8000) &
    (cd frontend && pnpm dev) &
    trap 'kill 0' EXIT
    wait

check:
    cd backend && uv run ruff check . && uv run ruff format --check . && uv run ty check
    cd frontend && pnpm exec biome check . && pnpm exec tsc --noEmit

test:
    cd backend && uv run pytest -q
    cd frontend && pnpm exec vitest run

e2e:
    cd frontend && pnpm exec playwright test

gen-api:
    cd backend && uv run python -m scripts.export_openapi ../frontend/openapi.json
    cd frontend && pnpm exec openapi-ts

data:
    cd backend && uv run python -m scripts.download_public && uv run python -m scripts.build_data

train:
    cd backend && uv run python -m scripts.train
