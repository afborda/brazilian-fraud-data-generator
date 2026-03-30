---
description: "Use when editing GitHub Actions workflows: triggers, jobs, steps, secrets, Docker builds, quality gates."
applyTo: ".github/workflows/**"
---

# CI/CD Rules

## Workflow Conventions
- Pin action versions: `actions/checkout@v4` not `@main`
- Use `concurrency` for deploy workflows to prevent parallel deploys
- Always include `actions/checkout` as first step
- Use `ubuntu-latest` runner unless architecture-specific

## Triggers
- Be specific: filter by branch (`branches: [main]`) and/or path
- Never use bare `on: push` without filters
- Deploy workflows should require manual approval or specific branch

## Secrets
- NEVER hardcode secrets in workflow files
- Reference via `${{ secrets.NAME }}`
- Document required secrets in workflow comments

## Docker Builds
- Preserve multi-platform: `linux/amd64,linux/arm64`
- Use buildx with cache for faster builds
- Tag format: `latest` + version tag

## Quality Gates
- pytest: `pytest tests/ -v --tb=short`
- Coverage: `pytest --cov=src/fraud_generator --cov-fail-under=50`
- Linting: `ruff check src/ tests/`
- Formatting: `ruff format --check src/ tests/`

## Existing Workflows (DO NOT break)
- `docker-publish.yml` — multi-platform Docker build on tag push
- `deploy-product.yml` — product deployment
- `deploy-infra.yml` — infrastructure deployment
- `deploy-site.yml` — site deployment
- `bump-synthfin-api.yml` — API version sync
