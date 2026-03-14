# 📚 Pesquisa de Mercado — Índice
> Pasta: `docs/pesquisa_mercado/`
> Criada em: 04/03/2026

## Documentos

| # | Arquivo | Conteúdo | Leitura |
|---|---------|----------|---------|
| 01 | [01_SHADOWTRAFFIC_PESQUISA.md](01_SHADOWTRAFFIC_PESQUISA.md) | O que é o ShadowTraffic, pricing oficial, pontos positivos/negativos, gaps encontrados no HN e Reddit | ~10 min |
| 02 | [02_ANALISE_COMPARATIVA.md](02_ANALISE_COMPARATIVA.md) | Tabela feature-by-feature, o que temos hoje, o que podemos ter, jornada de adoção comparada | ~15 min |
| 03 | [03_CAPACIDADE_E_ESCALABILIDADE.md](03_CAPACIDADE_E_ESCALABILIDADE.md) | Benchmark real, throughput por VPS, diagramas de capacidade, quantos usuários simultâneos a API aguenta, SLA | ~10 min |
| 04 | [04_MODELO_NEGOCIO.md](04_MODELO_NEGOCIO.md) | Tabela de planos em R$ e USD, projeção de receita, custos de infra, break-even, margem bruta | ~10 min |
| 05 | [05_HOSTED_API_GUIA_USUARIO.md](05_HOSTED_API_GUIA_USUARIO.md) | Como o usuário usa a hosted API, exemplos curl/Python/Colab, referência completa, como verificar que funciona | ~15 min |

## Resumo Executivo (TL;DR)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         NOSSA OPORTUNIDADE                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Concorrente principal:  ShadowTraffic ($399/ano, apenas Docker)        │
│                                                                          │
│  Gaps que deixaram:      ❌ sem dados brasileiros (CPF, PIX, bancos BR) │
│                          ❌ sem hosted API (prometida há 2 anos)         │
│                          ❌ sem ML-ready (campos is_fraud/fraud_type)    │
│                          ❌ sem plano mensal / sem opção BR              │
│                          ❌ sem ride-share                               │
│                                                                          │
│  Nossa posição única:    ✅ 100% foco em fraude BR                      │
│                          ✅ Hosted API = zero instalação                 │
│                          ✅ R$ 49/mês (vs R$ 2.394/ano deles)           │
│                          ✅ Parquet rotulado pronto para sklearn/spark   │
│                                                                          │
│  Capacidade técnica:                                                     │
│    Um único VPS de R$ 39/mês aguenta:                                   │
│    • 9.100 transações/segundo sustentável                               │
│    • 7.000 corridas/segundo sustentável                                 │
│    • ~60 usuários simultâneos com jobs pequenos                         │
│                                                                          │
│  Break-even:             2 clientes Starter (R$ 98) cobre infra (R$ 52) │
│  Projeção ano 1:         ~R$ 26.000 ARR com crescimento conservador     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Próximos Passos Técnicos

1. [ ] Implementar `POST /v1/generate` + `GET /v1/jobs/{id}` na FastAPI
2. [ ] Adicionar job queue com SQLite → Redis quando crescer
3. [ ] Worker que chama `generate.py` como subprocess com timeout
4. [ ] MinIO para armazenar resultados com expiração de 24h
5. [ ] Dashboard simples: registro → API key → uso mensal
6. [ ] SDK Python minimalista (`pip install bfdg`)
