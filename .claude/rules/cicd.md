---
description: GitHub Actions workflows, triggers, secrets, Docker builds, quality gates
paths:
  - ".github/workflows/**"
---

# CI/CD Rules

## Workflows
- Pin action versions: `actions/checkout@v4` not `@main`
- Use `concurrency` for deploy workflows
- Always `actions/checkout` as first step
- Default runner: `ubuntu-latest`

## Triggers
- Be specific: filter by branch and/or path
- Never bare `on: push` without filters
- Deploy workflows require approval or specific branch

## Secrets
- NEVER hardcode — use `${{ secrets.NAME }}`
- Document required secrets in workflow comments

## Docker
- Multi-platform: `linux/amd64,linux/arm64`
- Use buildx with cache
- Tag: `latest` + version tag

## Existing Workflows (preserve)
- `docker-publish.yml`, `deploy-product.yml`, `deploy-infra.yml`
- `deploy-site.yml`, `bump-synthfin-api.yml`
