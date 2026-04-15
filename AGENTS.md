# synthfin-data — Agent Registry

## Orchestration

The **orchestrator** agent is the default entry point. It analyzes any request and dispatches to the best specialist. Use it when you're unsure which agent to pick, or for multi-domain tasks.

## Agent Routing Table

| User wants to... | Agent | Threshold |
|-------------------|-------|-----------|
| **Default / unclear / multi-domain** | `orchestrator` | 0.90 |
| Create, validate, calibrate fraud patterns | `fraud-pattern-engineer` | 0.95 |
| Run quality benchmarks, analyze distributions | `data-quality-analyst` | 0.90 |
| Explore codebase, impact analysis, health check | `synthfin-explorer` | 0.90 |
| Generate pytest tests, audit coverage | `test-generator` | 0.90 |
| Create/update CI/CD workflows, quality gates | `ci-cd-specialist` | 0.95 |
| Diagnose bottlenecks, optimize, fix OOM | `performance-optimizer` | 0.95 |
| Create/audit config modules, weight normalization | `config-architect` | 0.90 |
| Update CHANGELOG, bump version, audit docs | `documentation-keeper` | 0.90 |

## Routing Signals

Quick keyword matching for dispatch:

| Keywords | → Agent |
|----------|---------|
| fraud, pattern, enricher, signal, PIX, risk, injection | fraud-pattern-engineer |
| quality, benchmark, AUC-ROC, distribution, schema, KS-test | data-quality-analyst |
| explore, understand, architecture, impact, health, overview | synthfin-explorer |
| test, pytest, coverage, fixture, conftest, unit | test-generator |
| workflow, CI/CD, pipeline, pre-commit, lint, gate, deploy | ci-cd-specialist |
| slow, memory, OOM, profile, optimize, speed, WeightCache | performance-optimizer |
| config, bank, merchant, weight, *_LIST, *_WEIGHTS, get_*() | config-architect |
| changelog, version, bump, docs, INDEX, governance | documentation-keeper |

## Platform Usage

### VS Code Copilot
- Agents appear in the **mode selector dropdown** (not via `@`)
- Select `orchestrator` as default, or pick a specialist directly
- Prompts (slash commands): `/generate-tests`, `/version-bump`, `/new-fraud-pattern`, `/quality-report`

### Claude Code
- Invoke via CLI: `/agent:orchestrator` (default) or `/agent:test-generator` (direct)
- Commands: `/testing/generate-tests`, `/docs/version-bump`, `/fraud/new-fraud-pattern`, `/quality/quality-report`

## Multi-Agent Patterns

| Scenario | Agents (in order) |
|----------|-------------------|
| Add feature + test it | specialist → test-generator |
| Change + benchmark + changelog | specialist → data-quality-analyst → documentation-keeper |
| Full project health report | synthfin-explorer + data-quality-analyst + test-generator (parallel) |
| New config + wire to enricher | config-architect → fraud-pattern-engineer |
| Optimize + verify quality | performance-optimizer → data-quality-analyst |
| New workflow + update docs | ci-cd-specialist → documentation-keeper |

## Agent Files

### VS Code Copilot (`.github/`)

| Agent | File |
|-------|------|
| orchestrator | `.github/agents/orchestrator.agent.md` |
| fraud-pattern-engineer | `.github/agents/fraud-pattern-engineer.agent.md` |
| data-quality-analyst | `.github/agents/data-quality-analyst.agent.md` |
| synthfin-explorer | `.github/agents/synthfin-explorer.agent.md` |
| test-generator | `.github/agents/test-generator.agent.md` |
| ci-cd-specialist | `.github/agents/ci-cd-specialist.agent.md` |
| performance-optimizer | `.github/agents/performance-optimizer.agent.md` |
| config-architect | `.github/agents/config-architect.agent.md` |
| documentation-keeper | `.github/agents/documentation-keeper.agent.md` |

### Claude Code (`.claude/agents/`)

| Agent | File |
|-------|------|
| orchestrator | `.claude/agents/orchestration/orchestrator.md` |
| fraud-pattern-engineer | `.claude/agents/fraud/fraud-pattern-engineer.md` |
| data-quality-analyst | `.claude/agents/quality/data-quality-analyst.md` |
| synthfin-explorer | `.claude/agents/exploration/synthfin-explorer.md` |
| test-generator | `.claude/agents/testing/test-generator.md` |
| ci-cd-specialist | `.claude/agents/cicd/ci-cd-specialist.md` |
| performance-optimizer | `.claude/agents/performance/performance-optimizer.md` |
| config-architect | `.claude/agents/config/config-architect.md` |
| documentation-keeper | `.claude/agents/documentation/documentation-keeper.md` |
