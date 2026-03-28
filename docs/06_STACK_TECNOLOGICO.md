# Stack Tecnológico

## Linguagens

| Linguagem | Uso | Versão |
|-----------|-----|--------|
| **Python** | Todo o backend, gerador, API, notebooks, scripts | 3.10+ (synthfin), 3.11 (API), 3.13 (VPS) |

---

## SynthFin-Core — Dependências

### Core (Geração de Dados)

| Pacote | Versão | Função |
|--------|--------|--------|
| **faker** | ≥22 | Dados fake pt-BR (nomes, endereços, empresas) |
| **pandas** | 2.2+ | Manipulação de DataFrames |
| **numpy** | ≥1.26 | Operações numéricas, distribuições |
| **pyarrow** | — | Formato Parquet e Arrow IPC |
| **numba** | — | JIT compilation para cálculos intensivos |

### Compressão

| Pacote | Função |
|--------|--------|
| **zstandard** | Compressão Zstandard (zstd) |
| **python-snappy** | Compressão Snappy |
| gzip (stdlib) | Compressão gzip (built-in) |

### Object Storage

| Pacote | Função |
|--------|--------|
| **boto3** | Upload para MinIO/S3 |

### Streaming

| Pacote | Função |
|--------|--------|
| **kafka-python** | Produção de eventos para Apache Kafka |
| **httpx** / **requests** | Webhooks HTTP |

### Exportação

| Pacote | Função |
|--------|--------|
| **SQLAlchemy** | Exportação para bancos de dados via ORM |

### Cache

| Pacote | Função |
|--------|--------|
| **redis** | Cache de índices pré-computados (opcional) |

### Validação

| Pacote | Função |
|--------|--------|
| **setuptools** | Build backend (pyproject.toml) |

---

## FraudFlow API — Dependências

### Framework Web

| Pacote | Versão | Função |
|--------|--------|--------|
| **FastAPI** | 0.111.0 | Framework web async |
| **uvicorn** | 0.30.1 | Servidor ASGI high-performance |
| **pydantic-settings** | 2.3.0 | Configuração via environment variables |

### HTTP Client

| Pacote | Versão | Função |
|--------|--------|--------|
| **httpx** | 0.27.0 | HTTP client async para coletores |

### Extração de Dados

| Pacote | Versão | Função |
|--------|--------|--------|
| **pdfplumber** | 0.11.1 | Extração de texto de PDFs |
| **openpyxl** | 3.1.3 | Leitura de arquivos XLSX |
| **python-pptx** | 1.0.2 | Extração de texto de PPTX |
| **pandas** | 2.2.2 | Manipulação de CSVs e DataFrames |

### Embeddings e Vector Store

| Pacote | Versão | Função |
|--------|--------|--------|
| **sentence-transformers** | 3.0.1 | Modelo de embedding multilingual |
| **qdrant-client** | 1.9.1 | Cliente para Qdrant vector store |

### LLM Providers

| Pacote | Versão | Função |
|--------|--------|--------|
| **google-genai** | ≥1.0.0 | Google Gemini API |
| **groq** | ≥0.9.0 | Groq API (Llama) |
| **openai** | 1.35.0 | OpenAI API |

---

## Infraestrutura

### Containers Docker

| Serviço | Imagem | Função |
|---------|--------|--------|
| **fraudflow-data-api** | `python:3.11-slim` (custom build) | API FastAPI + coletores + RAG |
| **fraudflow-qdrant** | `qdrant/qdrant:v1.9.2` | Vector store para embeddings |
| **fraudflow-jupyter** | `jupyter/scipy-notebook:python-3.11` | JupyterLab para análise |

### Orquestração

| Ferramenta | Função |
|------------|--------|
| **Docker Compose** | Orquestração dos 3 serviços |
| **Traefik** | Reverse proxy com Let's Encrypt SSL |

### Reverse Proxy e SSL

| Componente | Versão | Função |
|------------|--------|--------|
| **Traefik** | v2.10 | Reverse proxy HTTP/HTTPS |
| **Let's Encrypt** | — | Certificados SSL automáticos |

Middlewares Traefik configurados:
- **rate-limit** — 100 req/s, burst 50
- **security-headers** — HSTS, XSS protection, nosniff

### DNS

| Provedor | Função |
|----------|--------|
| **Cloudflare** | DNS management para `abnerfonseca.com.br` |

---

## Qdrant — Vector Store

| Propriedade | Valor |
|-------------|-------|
| Versão | 1.9.2 |
| Porta REST | 6333 |
| Porta gRPC | 6334 |
| Coleção | `fraudflow-brasil` |
| Dimensões | 384 |
| Distância | Cosine |
| Chunks indexados | 52.547 |
| Fontes | 66 |

---

## Modelo de Embedding

| Propriedade | Valor |
|-------------|-------|
| Modelo | `paraphrase-multilingual-MiniLM-L12-v2` |
| Provider | Sentence Transformers (Hugging Face) |
| Dimensões | 384 |
| Idiomas suportados | 50+ (português, inglês, espanhol, etc.) |
| Tamanho | ~120MB |
| Pré-download | Sim (no Docker build, evita download no runtime) |

---

## LLMs Utilizados

### Cadeia de Fallback

```
1. Gemini 2.5 Flash (Google) — primário
2. Llama 3.3 70B (Groq) — fallback
3. GPT-4o-mini (OpenAI) — terciário
```

| Provider | Modelo | Uso |
|----------|--------|-----|
| **Google Gemini** | gemini-2.5-flash | Síntese RAG, geração de regras |
| **Groq** | llama-3.3-70b-versatile | Fallback automático se Gemini falhar |
| **OpenAI** | gpt-4o-mini | Fallback terciário |

---

## Fontes de Dados Públicos

| Fonte | API/Método | Dados |
|-------|-----------|-------|
| **BCB SGS** | REST API | IPCA, CDI, SELIC, inadimplência, poupança |
| **BCB Olinda** | REST API | Estatísticas PIX |
| **IBGE SIDRA** | REST API v3 | População por UF |
| **BrasilAPI** | REST API v2 | CEPs + coordenadas GPS |
| **ViaCEP** | REST API | CEPs (fallback) |
| **dados.gov.br** | CKAN API | Datasets abertos |
| **FEBRABAN** | PDF download | Pesquisa Tecnologia Bancária |
| **COAF** | PDF download | Relatório de Atividades |

---

## Ferramentas de Validação

| Ferramenta | Função |
|------------|--------|
| `_validate_generated.py` | Score geral (13 seções) |
| `verify_calibration.py` | 9 overrides aplicados |
| `_benchmark_evolucao.py` | Comparação before/after |
| `validate_realism.py` | Score de realismo (10 dimensões) |
| `check_schema.py` | Validação de schema de output |
| `tstr_benchmark.py` | Train Synthetic Test Real (LR/RF/XGBoost) |
| `privacy_metrics.py` | Métricas de privacidade |
| `qde_filter.py` | Quality, Diversity, Exclusivity filter |

---

## Testes

| Framework | Função |
|-----------|--------|
| **pytest** | Test runner |

| Tipo | Contagem | Localização |
|------|----------|-------------|
| Unit tests | ~170 | `tests/unit/` |
| Integration tests | ~24 | `tests/integration/` |
| **Total** | **194 pass, 0 fail, 9 skip** | |

### Suítes de teste

| Arquivo | Cobertura |
|---------|-----------|
| `test_compression.py` | Estratégias de compressão |
| `test_correlations.py` | Correlações de fraude |
| `test_enricher_pipeline.py` | Pipeline de enriquecimento |
| `test_fraud_contextualization.py` | Contextualização de fraude |
| `test_output_schema.py` | Schema de saída |
| `test_phase_1_optimizations.py` | Otimizações fase 1 |
| `test_phase_2_optimizations.py` | Otimizações fase 2 |
| `test_score.py` | Score de risco (17+4 sinais) |
| `test_session_context.py` | Estado de sessão |
| `test_phase_2_1_endtoend.py` | End-to-end pipeline |
| `test_workflows.py` | Workflows batch/MinIO/schema |

---

## Portas e Serviços

| Porta | Serviço | Protocolo |
|-------|---------|-----------|
| 80 | Traefik (redirect HTTPS) | HTTP |
| 443 | Traefik (SSL) | HTTPS |
| 6333 | Qdrant REST | HTTP |
| 6334 | Qdrant gRPC | gRPC |
| 8000 | FraudFlow API | HTTP |
| 8888 | JupyterLab | HTTP |

---

## Domínio e SSL

| Propriedade | Valor |
|-------------|-------|
| Domínio principal | `abnerfonseca.com.br` |
| Subdomínio API | `fraudflow.abnerfonseca.com.br` |
| Certificado | Let's Encrypt (automático via Traefik) |
| DNS | Cloudflare |
| Protocolo | HTTPS (TLS 1.3) |
