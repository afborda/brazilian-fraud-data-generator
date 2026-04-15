# Gerador de Dados de Fraude Brasileiro

<p align="center">
  <img src="assets/Hero%20do%20README.png" alt="synthfin-data — dados sintéticos de fraude para banking brasileiro, PIX, ride-share, sinais e exportações." width="100%" />
</p>

<p align="center">
  <a href="../README.md"><img src="https://img.shields.io/badge/lang-en-B91C1C" alt="Documentação em inglês" /></a>
  <a href="./README.pt-BR.md"><img src="https://img.shields.io/badge/lang-pt--BR-15803D" alt="Documentação em português" /></a>
  <img src="https://img.shields.io/badge/version-4.18.0-0F766E" alt="Versão 4.18.0" />
  <img src="https://img.shields.io/badge/python-3.10%2B-1D4ED8" alt="Python 3.10 ou superior" />
  <img src="https://img.shields.io/badge/AUC--ROC-0.9991-0F766E" alt="AUC-ROC 0.9991" />
  <img src="https://img.shields.io/badge/qualidade-9.70%2F10-0F766E" alt="Qualidade 9.70/10" />
</p>

<p align="center">
  <strong>Dados sintéticos brasileiros para antifraude, QA e engenharia de dados.</strong><br />
  Gere datasets realistas de transações bancárias, PIX e corridas de app para treino de modelos, validação de pipelines e testes de integração.
</p>

<p align="center">
  <a href="README.md">Docs em inglês</a> · <a href="../ARCHITECTURE.md">Arquitetura</a> · <a href="CHANGELOG.md">Changelog</a>
</p>

---

## ⚡ SynthFin API — Plataforma Hospedada (Beta)

> **🧪 Fase de testes — acesso aberto para quem quiser experimentar.**
>
> Uma versão hospedada deste gerador está disponível em **[synthfin.com.br](https://synthfin.com.br)** — sem infraestrutura para operar, REST API inclusa, relatório de qualidade ML entregue por e-mail após cada job.
>
> **Quer testar?** Manda um e-mail para **[devabnerfonseca@gmail.com](mailto:devabnerfonseca@gmail.com)** e a gente te coloca pra rodar.
>
> **Tem dados reais de fraude para comparar?** Estamos ativamente procurando parceiros que possam compartilhar dados reais anonimizados ou agregados para validar e melhorar a qualidade das nossas distribuições sintéticas. Se você trabalha com prevenção a fraudes em banco, fintech ou processadora de pagamentos e quer colaborar — mesmo que informalmente — entre em contato. Qualquer contribuição para melhorar a capacidade de acerto dos dados é muito bem-vinda.

A API hospedada em [api.synthfin.com.br](https://api.synthfin.com.br) entrega:

- **REST API** — `POST /v2/generate` → job assíncrono → link de download
- **Relatório de Qualidade ML** — análise automática com LightGBM após cada job, grade A+→F enviada por e-mail com AUC-ROC, detalhamento por tipo de fraude e importância de features
- **Dashboard** em [app.synthfin.com.br](https://app.synthfin.com.br) — histórico de jobs, download, relatórios de qualidade
- **Streaming** — feed Server-Sent Events via `/v2/streams`
- **Webhooks** — notificação no seu endpoint quando o job concluir

```bash
# Criar um job via API
curl -X POST https://api.synthfin.com.br/v2/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"transactions","count":100000,"format":"parquet","fraud_rate":0.03}'

# Verificar status (inclui métricas de qualidade após análise)
curl https://api.synthfin.com.br/v2/jobs/{job_id} \
  -H "Authorization: Bearer YOUR_API_KEY"
# → {"status":"done","download_url":"...","quality_auc_roc":0.9347,"quality_report_url":"..."}
```

Após o job concluir, você recebe um e-mail com:
- Link para download do dataset (JSONL / CSV / Parquet)
- Link para o relatório de qualidade — HTML com grade, AUC-ROC por tipo de fraude e importância de sinais
- Alertas automáticos se algum tipo de fraude estiver `too_easy` ou `too_hard` de detectar

---

## Por que este projeto existe

Este repositório foi construído para quem precisa de um dataset sintético de fraude com contexto brasileiro realista — não apenas um gerador genérico de transações. Ele combina CPF válido, bancos brasileiros, PIX com campos BACEN, sazonalidade local, ride-share, score de fraude, schema declarativo e entrega por arquivo ou streaming.

<table>
  <tr>
    <td width="33%"><strong>Realismo brasileiro</strong><br />CPF válido, geografia nacional, perfis comportamentais, sazonalidade e sinais ligados a PIX e device.</td>
    <td width="33%"><strong>Pronto para produção</strong><br />Batch, streaming, schema mode, banco de dados, Kafka, webhook, MinIO ou S3.</td>
    <td width="33%"><strong>Foco em fraude</strong><br />25 padrões bancários, 11 fraudes de ride-share, 17 sinais de risco e 4 regras de correlação.</td>
  </tr>
</table>

---

## Como funciona — fluxo completo

### Open Source (self-hosted)

```
python generate.py --size 1GB --format parquet --fraud-rate 0.03 --seed 42 --output ./dados
```

```
generate.py
    │
    ▼
BatchRunner (multiprocessing, N workers)
    │
    ├── CustomerGenerator  →  customers.jsonl
    ├── DeviceGenerator    →  devices.jsonl
    └── TransactionGenerator
            │
            ▼
        generate_with_pipeline()
            │
            ├── 01 Temporal    (horários incomuns, sazonalidade, time_anomaly)
            ├── 02 Geo         (lat/lon IBGE, município, pesos Censo 2022)
            ├── 03 Fraud       (injetar padrão, velocidade, dest_account_age)
            ├── 04 PIX         (end_to_end_id, ISPB BACEN, pacs.008)
            ├── 05 Device      (emulator, VPN, rooted, device_age_days)
            ├── 06 Session     (janelas 1h/6h/24h/7d, valores acumulados)
            ├── 07 Risk        (fraud_risk_score: 17 sinais, 4 regras)
            └── 08 Biometric   (velocidade de digitação, pressão de toque)
                    │
                    ▼
            Registro rotulado (114+ campos)
            is_fraud · fraud_type · fraud_risk_score · fraud_signals[]
                    │
                    ▼
        Exporter (JSONL / CSV / Parquet / Arrow / DB / MinIO)
```

### Plataforma hospedada (synthfin.com.br)

```
Sua aplicação
    │
    ▼  POST /v2/generate
API (FastAPI + fila Redis)
    │
    ▼
Worker Pool (mesmo pipeline acima)
    │
    ├── Upload do dataset  →  MinIO (URL pré-assinada, TTL 48h)
    │
    └── Análise de Qualidade ML
            │
            ├── evaluate_batch() via LightGBM
            ├── Grade A+→F  (AUC-ROC + penalidade por too_easy/too_hard)
            ├── Relatório HTML  →  MinIO
            └── E-mail → você (link dataset + link relatório + grade + AUC-ROC)
    │
    ▼  GET /v2/jobs/{id}
{
  "status": "done",
  "download_url": "https://...",
  "quality_auc_roc": 0.9347,
  "quality_auc_pr": 0.8812,
  "quality_report_url": "https://...",
  "quality_analysis_id": "ana_f3a91c..."
}
```

---

## Comece rápido

```bash
pip install -r requirements.txt
```

### Geração batch

```bash
# 1 GB de transações bancárias
python generate.py --size 1GB --output ./dados

# Dataset reproduzível: seed fixo, 5% de fraude, 8 workers
python generate.py --size 2GB --fraud-rate 0.05 --seed 42 --workers 8 --output ./dados

# Dados de ride-share
python generate.py --size 500MB --type rides --output ./dados

# Bancário e ride-share juntos
python generate.py --size 1GB --type all --output ./dados

# Exportar como Parquet, CSV ou Arrow
python generate.py --size 1GB --format parquet --compression zstd --output ./dados

# Enviar direto para MinIO ou S3
python generate.py --size 5GB --output minio://fraud-data/raw --minio-endpoint http://minio:9000

# Janela de datas específica
python generate.py --size 1GB --start-date 2024-01-01 --end-date 2024-12-31 --output ./dados
```

### Streaming

```bash
pip install -r requirements-streaming.txt

# Terminal a 5 eventos/seg
python stream.py --target stdout --rate 5 --pretty

# Kafka a 100 eventos/seg
python stream.py --target kafka --kafka-server localhost:9092 --kafka-topic transactions --rate 100

# Webhook
python stream.py --target webhook --type rides --webhook-url http://api:8080/ingest --rate 50

# Redis Stream
python stream.py --target redis-stream --rate 50

# Parar após 10.000 eventos
python stream.py --target stdout --rate 20 --max-events 10000
```

### Docker

```bash
docker run --rm -v $(pwd)/output:/output \
  afborda/synthfin-data:latest \
  generate.py --size 1GB --output /output

# Streaming via Docker
docker run --rm \
  afborda/synthfin-data:latest \
  stream.py --target stdout --rate 10
```

---

## Pipeline de 8 Enrichers

Cada transação passa por um pipeline determinístico que constrói contexto realista de fraude camada por camada:

| # | Enricher | O que adiciona |
|---|----------|----------------|
| 01 | **Temporal** | Horários incomuns (22h–5h), sazonalidade por dia, flag time_anomaly |
| 02 | **Geo** | Centroide lat/lon IBGE, código município 7 dígitos, pesos Censo 2022 |
| 03 | **Fraud** | Injeção de tipo de fraude, multiplicador de valor, burst de velocidade |
| 04 | **PIX** | `end_to_end_id`, ISPB real (BACEN IF.data), status `pacs.008` / `pacs.004` |
| 05 | **Device** | `device_age_days`, `emulator_detected`, `vpn_active`, `rooted_or_jailbreak` |
| 06 | **Session** | `velocity_24h`, `new_beneficiary`, `accumulated_amount_24h`, janelas 1h/6h/7d/30d |
| 07 | **Risk** | Score 0–100 com 17 sinais (`active_call`=35, `emulator`=35, `rooted`=30...) |
| 08 | **Biometric** | `typing_speed_avg_ms`, `touch_pressure_avg`, `scroll_before_confirm` |

---

## Validação de Qualidade ML

Além da acurácia dos rótulos, o projeto inclui uma **camada de validação adversarial ML** que mede o quão detectável é a fraude gerada usando um classificador LightGBM — um sinal independente de fidelidade dos dados.

### Grades de qualidade

| Grade | AUC-ROC efetivo | Significado |
|---|---|---|
| **A+** | ≥ 0.97 | Excelente — pronto para treino em produção |
| **A** | ≥ 0.93 | Muito bom |
| **B+** | ≥ 0.89 | Bom |
| **B** | ≥ 0.85 | Aceitável |
| **C** | ≥ 0.75 | Marginal — revisar padrões de fraude |
| **D** | ≥ 0.65 | Fraco — considerar re-gerar |
| **F** | < 0.65 | Reprovado |

> O AUC-ROC efetivo desconta penalidades por tipos determinísticos (`too_easy`, peso 0.12) e estatisticamente insuficientes (`too_hard`, peso 0.05).

### Flags por tipo de fraude

| Flag | Significado |
|---|---|
| `healthy_high_signal` | Detectável e bem balanceado |
| `healthy_low_signal` | Detectável com poucos exemplos |
| `too_easy` | Sinais determinísticos — modelo decora em vez de aprender |
| `too_hard` | Poucos exemplos ou sinal fraco — AUC não confiável |

### Rodar localmente

```bash
# 1. Gerar dados de treino
python generate.py --size 50MB --fraud-rate 0.05 --seed 42 --output ./dados/treino

# 2. Treinar modelo de qualidade
python tools/train_ml.py --input ./dados/treino/*.jsonl --model-dir ./models --version v1

# 3. Analisar um batch
python tools/analyze_batch.py \
  --input ./dados/treino/transactions_00000.jsonl \
  --output ./dados/relatorio_analise.json
```

---

## 25 Padrões de Fraude Bancária

`ENGENHARIA_SOCIAL`, `PIX_GOLPE`, `CONTA_TOMADA`, `CARTAO_CLONADO`, `FRAUDE_APLICATIVO`, `BOLETO_FALSO`, `FALSA_CENTRAL_TELEFONICA`, `COMPRA_TESTE`, `MULA_FINANCEIRA`, `CARD_TESTING`, `MICRO_BURST_VELOCITY`, `WHATSAPP_CLONE`, `DISTRIBUTED_VELOCITY`, `PHISHING_BANCARIO`, `FRAUDE_QR_CODE`, `FRAUDE_DELIVERY_APP`, `MAO_FANTASMA`, `CREDENTIAL_STUFFING`, `EMPRESTIMO_FRAUDULENTO`, `GOLPE_INVESTIMENTO`, `SIM_SWAP`, `PIX_AGENDADO_FRAUDE`, `SEQUESTRO_RELAMPAGO`, `SYNTHETIC_IDENTITY`, `DEEP_FAKE_BIOMETRIA`

Catálogo completo com sinais, calibração BCB/Febraban/MJSP e exemplos: [docs/07_CATALOGO_FRAUDES.md](07_CATALOGO_FRAUDES.md)

## 11 Tipos de Fraude em Ride-Share

`GHOST_RIDE`, `GPS_SPOOFING`, `SURGE_ABUSE`, `MULTI_ACCOUNT_DRIVER`, `PROMO_ABUSE`, `RATING_FRAUD`, `SPLIT_FARE_FRAUD`, `REFUND_ABUSE`, `PAYMENT_CHARGEBACK`, `DESTINATION_DISPARITY`, `ACCOUNT_TAKEOVER_RIDE`

---

## Schema de Saída

```
./dados/
├── customers.jsonl           ← um registro por cliente
├── devices.jsonl             ← um ou mais devices por cliente
└── transactions_00000.jsonl  ← transações (um arquivo por worker)
```

<details>
<summary><strong>Transação bancária legítima (clique para expandir)</strong></summary>

```json
{
  "transaction_id": "TXN_DCB02BE69A265CDE9933",
  "customer_id": "CUST_000000002438",
  "timestamp": "2025-04-28T19:15:14.146316",
  "type": "CREDIT_CARD",
  "amount": 127.82,
  "currency": "BRL",
  "channel": "MOBILE_APP",
  "customer_state": "SP",
  "merchant_name": "Cosi",
  "merchant_category": "Restaurants",
  "mcc_code": "5812",
  "cliente_perfil": "young_digital",
  "velocity_transactions_24h": 1,
  "fraud_score": 11,
  "is_fraud": false,
  "fraud_risk_score": 0
}
```

</details>

<details>
<summary><strong>PIX fraudulento — campos BACEN, fraud_type, fraud_signals</strong></summary>

```json
{
  "transaction_id": "TXN_A3F2B1C4D5E6F7A8B9C0",
  "customer_id": "CUST_000000001711",
  "timestamp": "2025-11-05T23:45:48.844962",
  "type": "PIX",
  "amount": 1689.28,
  "customer_state": "AM",
  "pix_key_type": "CPF",
  "end_to_end_id": "E30723886202511052007B0471FE3",
  "ispb_pagador": "30723886",
  "ispb_recebedor": "90400888",
  "velocity_transactions_24h": 10,
  "accumulated_amount_24h": 11824.96,
  "fraud_score": 89,
  "is_fraud": true,
  "fraud_type": "PIX_GOLPE",
  "fraud_risk_score": 43,
  "fraud_signals": ["active_call", "amount_spike"],
  "new_beneficiary": true,
  "dest_account_age_days": 3
}
```

</details>

---

## O que já está disponível hoje

| Área | Disponível agora |
|---|---|
| Bancário | PIX, TED, DOC, boleto, saque, POS, ecommerce, campos BACEN, device, CPF válido |
| Ride-share | Uber, 99, Cabify, inDrive com motoristas, surge, distância e clima |
| Labels de fraude | 25 padrões bancários + 11 ride-share com taxa configurável |
| Score de fraude | `fraud_risk_score` 0–100 com 17 sinais e 4 regras de correlação |
| Realismo temporal | Picos trimodais, pesos por dia da semana, Black Friday, Natal, 13º e Carnaval |
| Validação ML | LightGBM adversarial, AUC por tipo, Cliff's delta, Jensen-Shannon divergence |

---

## Open Source e planos comerciais

Todo o código do gerador está neste repositório sob **licença custom non-commercial**. Uso gratuito para estudo pessoal, pesquisa acadêmica e experimentação não-comercial. Uso comercial requer licença paga — veja [LICENSE](../LICENSE).

A plataforma hospedada em **[synthfin.com.br](https://synthfin.com.br)** está em **fase de testes** e aceitando usuários. Para testar, entre em contato em **[devabnerfonseca@gmail.com](mailto:devabnerfonseca@gmail.com)**.

| Funcionalidade | Open Source (self-hosted) | Plataforma hospedada |
|---|:---:|:---:|
| Todos os geradores e formatos | ✓ | ✓ |
| 25 padrões de fraude bancária | ✓ | ✓ |
| 11 tipos de fraude ride-share | ✓ | ✓ |
| Streaming (stdout, Kafka, webhook, redis) | ✓ | ✓ |
| Workers paralelos, Docker | ✓ | ✓ |
| Escala ilimitada | ✓ | ✓ |
| API REST hospedada | – | ✓ |
| Relatório de qualidade ML por e-mail | – | ✓ |
| Dashboard de jobs | – | ✓ |
| Suporte | – | ✓ |

---

## Métricas de Qualidade

| Métrica | Valor |
|---|---|
| Score de qualidade | 9.70 / 10 |
| AUC-ROC (classificador binário) | 0.9991 |
| Throughput (8 workers, 18 cores) | ~58K eventos/s |
| Tipos de fraude cobertos | 25 bancários + 11 ride-share |
| Campos por transação | 114+ |
| Cobertura geográfica | 104 municípios, 27 estados |
| Sinais de risco | 17 sinais, 4 regras de correlação |

---

## Referência de CLI

<details>
<summary><strong>generate.py — todas as flags</strong></summary>

| Flag | Padrão | Descrição |
|---|---|---|
| `--type` | `transactions` | `transactions`, `rides` ou `all` |
| `--size` | `1GB` | Tamanho alvo: `1GB`, `500MB`, `10GB` |
| `--output` | `./output` | Diretório ou `minio://bucket/prefix` |
| `--format` | `jsonl` | `jsonl`, `json`, `csv`, `tsv`, `parquet`, `arrow`, `ipc`, `db` |
| `--fraud-rate` | `0.008` | Fração de registros de fraude (0.0–1.0) |
| `--workers` | nº de CPUs | Processos paralelos |
| `--seed` | nenhum | Seed para datasets reproduzíveis |
| `--start-date` | 1 ano atrás | `YYYY-MM-DD` |
| `--end-date` | hoje | `YYYY-MM-DD` |
| `--compression` | `zstd` | Parquet: `snappy`, `zstd`, `gzip`, `brotli`, `none` |
| `--schema` | nenhum | Arquivo de schema JSON declarativo |
| `--db-url` | nenhum | URL SQLAlchemy para formato `db` |
| `--minio-endpoint` | env | URL do endpoint MinIO/S3 |

</details>

<details>
<summary><strong>stream.py — todas as flags</strong></summary>

| Flag | Padrão | Descrição |
|---|---|---|
| `--target` | obrigatório | `kafka`, `webhook`, `stdout` ou `redis-stream` |
| `--type` | `transactions` | `transactions` ou `rides` |
| `--rate` | `10` | Eventos por segundo |
| `--max-events` | infinito | Parar após N eventos |
| `--fraud-rate` | `0.008` | Fração de eventos de fraude |
| `--seed` | nenhum | Seed aleatória |
| `--workers` | `1` | Processos paralelos |
| `--pretty` | off | JSON formatado (apenas stdout) |

</details>

---

## Mapa rápido do repositório

| Comece aqui | Para quê serve |
|---|---|
| `generate.py` | Entrada principal da geração batch |
| `stream.py` | Streaming contínuo de eventos |
| `validate_realism.py` | Medir realismo temporal, geográfico e de fraude |
| `tools/train_ml.py` | Treinar modelo de qualidade LightGBM |
| `tools/analyze_batch.py` | Análise científica (Cliff's delta, JSD, Cramér's V) |
| `schemas/` | Schemas JSON de exemplo para schema mode |
| `src/fraud_generator/enrichers/` | Pipeline de 8 enrichers |
| `src/fraud_generator/ml/` | Módulo de validação ML |
| `../ARCHITECTURE.md` | Arquitetura técnica detalhada |
| `CHANGELOG.md` | Histórico de versões |

---

## FAQ

<details>
<summary><strong>Serve só para transações bancárias?</strong></summary>

Não. O projeto gera dados bancários e de ride-share. `--type all` gera os dois no mesmo job.

</details>

<details>
<summary><strong>Posso adaptar para o meu schema?</strong></summary>

Sim. Use `--schema` com um dos arquivos em `schemas/` ou com um JSON schema próprio.

</details>

<details>
<summary><strong>Como a plataforma hospedada difere do open source?</strong></summary>

O código é o mesmo. A plataforma em [synthfin.com.br](https://synthfin.com.br) adiciona: API REST, fila de jobs, upload automático para MinIO, relatório de qualidade ML enviado por e-mail e dashboard de acompanhamento. Está em fase de testes — contato em [devabnerfonseca@gmail.com](mailto:devabnerfonseca@gmail.com).

</details>

<details>
<summary><strong>Como posso ajudar a melhorar a qualidade dos dados?</strong></summary>

Se você tem acesso a dados reais de fraude (anonimizados ou agregados) e quer colaborar para validar e melhorar as distribuições sintéticas, entre em contato em [devabnerfonseca@gmail.com](mailto:devabnerfonseca@gmail.com). Qualquer colaboração — mesmo informal — para melhorar a capacidade de acerto é muito bem-vinda.

</details>

---

## Leitura recomendada

- Docs em inglês: [README.md](README.md)
- Arquitetura: [../ARCHITECTURE.md](../ARCHITECTURE.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Catálogo de fraudes: [07_CATALOGO_FRAUDES.md](07_CATALOGO_FRAUDES.md)
