# Notebooks e Workflow de Calibração

## Visão Geral

A calibração do SynthFin é feita por uma sequência de 8 notebooks Jupyter que formam um pipeline reprodutível. Cada notebook representa uma etapa do processo, desde a extração de dados brutos até a validação final.

---

## Pipeline de Notebooks

```
NB01 Extração      → Descompacta e prepara dados brutos
  │
  ▼
NB02 Indexação RAG → Indexa no Qdrant (52K+ chunks, 66 fontes)
  │
  ▼
NB03 Gerar Regras  → LLM analisa RAG e propõe regras (25 tipos)
  │
  ▼
NB04 Calibrar      → Aplica regras ao synthfin-core
  │
  ▼
NB05 Cruzamento    → Compara dados reais × sintéticos
  │
  ▼
NB06 Padrões       → Análise avançada (clustering, anomalias)
  │
  ▼
NB07 Validação     → Score final (8.0/10), checkpoints V6
  │
  ▼
NB08 GolpeBR       → Indexação e análise de fraudes brasileiras
```

---

## Detalhamento por Notebook

### 01 — Extração de Dados (`01_extracao_dados.ipynb`)

**Objetivo:** Extrair e preparar dados brutos de múltiplas fontes.

**Operações:**
- Descompressão de ZIPs (`data/processed/`)
- Extração de PDFs via pdfplumber
- Leitura de CSVs e XLSX
- Conversão de PPTX para texto
- Organização em diretórios padronizados

**Fontes processadas:**
- Datasets Kaggle (fraude em cartão, transações bancárias)
- PaySim (simulação de fraude mobile money)
- Relatórios FEBRABAN e COAF
- Séries BCB
- Dados IBGE

**Output:** Arquivos limpos em `data/` organizados por fonte.

---

### 02 — Popular RAG (`02_popular_rag.ipynb`)

**Objetivo:** Indexar todos os dados extraídos no Qdrant via API.

**Operações:**
- Chama `POST /coleta/tudo` (todos os coletores em paralelo)
- Chama `POST /coleta/local` (indexar arquivos locais)
- Monitora `GET /coleta/status` até finalizar
- Verifica `GET /rag/status` para confirmar chunks indexados

**Métricas de saída:**

| Métrica | Valor |
|---------|-------|
| Total de chunks | 52.547 |
| Fontes indexadas | 66 |
| Modelo de embedding | paraphrase-multilingual-MiniLM-L12-v2 |
| Dimensões | 384 |

---

### 03 — Gerar Regras (`03_gerar_regras.ipynb`)

**Objetivo:** Usar RAG + LLM para gerar regras de fraude calibradas.

**Operações:**
- Para cada um dos 25 tipos de fraude:
  - Busca semântica no RAG por evidências
  - LLM analisa documentos e propõe prevalência
  - Calcula score de evidência RAG
- Gera `fraud_pattern_overrides.json` atualizado
- Compara valores propostos × valores anteriores

**Os 25 tipos de fraude cobertos:**

1. ENGENHARIA_SOCIAL
2. PIX_GOLPE
3. CONTA_TOMADA
4. CARTAO_CLONADO
5. FRAUDE_APLICATIVO
6. COMPRA_TESTE
7. BOLETO_FALSO
8. MULA_FINANCEIRA
9. CARD_TESTING
10. MICRO_BURST_VELOCITY
11. DISTRIBUTED_VELOCITY
12. MAO_FANTASMA
13. WHATSAPP_CLONE
14. SIM_SWAP
15. CREDENTIAL_STUFFING
16. SYNTHETIC_IDENTITY
17. SEQUESTRO_RELAMPAGO
18. FALSA_CENTRAL_TELEFONICA
19. PIX_AGENDADO_FRAUDE
20. QR_CODE_ADULTERADO
21. DEPOSITO_ENVELOPE_VAZIO
22. FRAUDE_CONSIGNADO
23. EMPRESTIMO_IDENTIDADE_FALSA
24. FRAUDE_SEGURO
25. LAVAGEM_ESTRUTURADA

---

### 04 — Calibrar Regras (`04_calibrar_regras_synthfin.ipynb`)

**Objetivo:** Aplicar as regras geradas ao SynthFin-Core e gerar novo dataset.

**Operações:**
- Salva `fraud_pattern_overrides.json` em `data/rules/`
- Executa geração: `python generate.py --seed 42 --num 270000`
- Salva snapshot de calibração em `data/calibracao/after/`
- Checkpoint V6: valida novas features implementadas

**Parâmetros de geração:**

| Parâmetro | Valor |
|-----------|-------|
| Seed | 42 |
| Registros | ~270.000 |
| Fraud rate | 0.008 (0.8%) |
| Workers | Auto (CPU count) |

---

### 05 — Análise Cruzada (`05_analise_cruzada.ipynb`)

**Objetivo:** Comparar distribuições dos dados sintéticos com dados reais públicos.

**8 dimensões de cruzamento:**

| Dimensão | O que compara |
|----------|---------------|
| Valor | Distribuição de valores vs. ticket médio real |
| Canal | Mix de canais (PIX/cartão/TED) vs. estatísticas BCB |
| Perfil | Distribuição de perfis comportamentais |
| Geográfico | SP+RJ+MG = 38.2% vs. concentração real |
| Temporal | Horários de pico vs. padrões reais |
| Fraude | Rate de fraude vs. estatísticas BCB (4-6 por 100K) |
| Merchant | Distribuição de MCCs vs. dados de mercado |
| Beneficiário | Novos beneficiários em fraude |

---

### 06 — Padrões Avançados (`06_padroes_avancados.ipynb`)

**Objetivo:** Análise estatística avançada dos dados gerados.

**Técnicas:**
- **Clustering** — Agrupamento de transações fraudulentas por similaridade
- **Anomaly Detection** — Identificação de outliers via isolation forest
- **Temporal Patterns** — Curvas temporais de fraude (horário, dia da semana, mês)
- **Network Analysis** — Grafos de relacionamento entre contas
- **Distribution Fitting** — Ajuste de distribuições (Pareto, log-normal)
- **Velocity Analysis** — Padrões de velocidade de transação
- **Geographic Clustering** — Hotspots geográficos de fraude

**7 padrões avançados identificados:**
1. Burst de velocidade em horário madrugada
2. Contas mula com padrão passthrough
3. Escalação de valor em card testing
4. Rotação de dispositivos em fraude distribuída
5. Concentração geográfica de engenharia social
6. Sazonalidade de fraude (pico em dezembro/janeiro)
7. Correlação device novo + beneficiário novo

---

### 07 — Validação e Calibração Final (`07_validacao_calibracao_final.ipynb`)

**Objetivo:** Validação final com scorecard completo.

**Seções de validação (V6):**
1. Carregamento e overview do dataset
2. Distribuição de fraudes (25 tipos, prevalências)
3. Ratio fraude/legítima (target: 5×)
4. Score de realismo (target: 8.0/10)
5. Cobertura geográfica (27 estados)
6. Análise temporal (horários de pico)
7. Validação PIX (campos BACEN)
8. Perfis comportamentais (7 perfis)
9. Checkpoints V6 (novas features)

**Métricas finais:**

| Métrica | Valor | Target |
|---------|-------|--------|
| Score geral | 8.0/10 | ≥ 7.5 |
| Ratio fraude/legítima | 5.09× | ≥ 3× |
| Tipos de fraude | 25 | ≥ 20 |
| Estados | 27 | 27 |
| SP+RJ+MG | 38.2% | 35-45% |
| Colunas | 117 | ≥ 100 |

---

### 08 — GolpeBR Análise RAG (`08_golpebr_analise_rag.ipynb`)

**Objetivo:** Indexar e analisar dados do portal GolpeBR sobre fraudes brasileiras.

**Operações:**
- Coleta de tipologias de golpes via web
- Indexação no RAG com metadados
- Análise de padrões emergentes
- Comparação com tipos já cobertos pelo SynthFin

---

## Notebooks Auxiliares

### `analise_dados_coletados.ipynb`

Análise exploratória dos dados coletados pelos collectors. Estatísticas descritivas, distribuições, completude.

### `exportar_para_rag.py`

Script auxiliar para exportar dados processados direto para o RAG via API.

---

## Scripts de Suporte

| Script | Função |
|--------|--------|
| `baixar_fraudes_pix.py` | Download de estatísticas BCB de fraudes PIX |
| `baixar_transacoes_pix.py` | Download de agregados de transações PIX |
| `baixar_ranking_reclamacoes_bcb.py` | Ranking de reclamações BCB por banco |
| `baixar_alianca_nacional_fraudes.py` | Tipologias da Aliança Nacional |
| `enriquecer_rag_score.py` | Boost do score RAG com documentos densos |
| `indexar_academicos_rag.py` | Indexação de papers acadêmicos |
| `indexar_demographics_rag.py` | Indexação de dados demográficos |
| `indexar_golpebr_rag.py` | Indexação de dados GolpeBR |
| `gerar_narrativa_fraudes.py` | Geração de narrativas via LLM |
| `gerar_relatorio_bancos_sfn.py` | Relatório do Sistema Financeiro Nacional |
| `gerar_relatorio_geo.py` | Relatório de padrões geográficos |
| `listar_fontes_indexadas.py` | Lista todas as fontes no RAG |
| `table_rag.py` | Extração de tabelas de PDFs |
| `exportar_para_rag.py` | Exportação direta para Qdrant |

---

## Acessando o JupyterLab

O JupyterLab roda na porta 8888 do servidor.

**URL:** `http://<servidor>:8888`

**Token:** Configurado via variável de ambiente `JUPYTER_TOKEN`.

**Diretórios montados:**
- `/home/jovyan/notebooks` → Notebooks
- `/home/jovyan/data` → Dados processados
- `/home/jovyan/dados` → Dados brutos
- `/home/jovyan/scripts` → Scripts auxiliares
