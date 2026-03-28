# API e RAG — Referência Completa

## Visão Geral

A API FraudFlow é uma aplicação FastAPI que fornece:

- **Coleta automatizada** de dados públicos brasileiros
- **RAG (Retrieval-Augmented Generation)** para consultas semânticas
- **Geração de regras** de fraude calibradas via LLM
- **Compliance LGPD** para datasets gerados

**URL de produção:** `https://fraudflow.abnerfonseca.com.br`

---

## Endpoints

### Health & Status

#### `GET /`

Status básico da API.

**Response:**

```json
{
  "status": "ok",
  "service": "FraudFlow Data Collection & RAG API",
  "endpoints": ["/coleta", "/rag", "/regras", "/lgpd"]
}
```

#### `GET /health`

Health check simplificado.

```json
{"status": "ok"}
```

#### `GET /llm/status`

Status do LLM configurado.

```json
{
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "fallback_order": ["gemini", "groq", "openai"]
}
```

---

### RAG — Busca Semântica + LLM

#### `POST /rag/query`

Consulta semântica na base de conhecimento com resposta sintetizada por LLM.

**Request:**

```json
{
  "query": "Quais os principais tipos de fraude PIX no Brasil?",
  "top_k": 5,
  "usar_llm": true
}
```

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `query` | string | obrigatório | Pergunta em linguagem natural |
| `top_k` | int | 5 | Documentos a retornar |
| `usar_llm` | bool | true | Sintetizar resposta via LLM |

**Response:**

```json
{
  "query": "Quais os principais tipos de fraude PIX no Brasil?",
  "contexto": [
    {
      "score": 0.79,
      "fonte": "relatorio_fraudes_pix_med_bcb",
      "parte": 8,
      "texto": "CONCLUSAO: O PIX é o principal canal de fraude..."
    }
  ],
  "resposta_llm": "Com base nos documentos, os principais tipos..."
}
```

#### `GET /rag/buscar?q=...&top_k=5`

Busca rápida sem LLM. Retorna apenas os documentos mais relevantes.

**Parâmetros query string:**
- `q` — Texto de busca
- `top_k` — Número de resultados (default: 5)

#### `POST /rag/indexar`

Indexa texto livre na base de conhecimento.

**Request:**

```json
{
  "texto": "Conteúdo do documento a indexar...",
  "fonte": "nome_da_fonte",
  "metadados": {}
}
```

#### `GET /rag/status`

Status do RAG — total de chunks e contagem por fonte.

```json
{
  "total_chunks": 52547,
  "fontes": {
    "relatorio_fraudes_pix_med_bcb": 245,
    "relatorio_dados_bancarios_sfn": 180,
    "tipologias_canais_fraudes_brasil": 156,
    "..."
  }
}
```

---

### Coleta — Coletores de Dados

#### `POST /coleta/bacen`

Coleta séries temporais do Banco Central (SGS + Olinda).

Séries coletadas:
- IPCA (série 433)
- CDI (série 11)
- SELIC (série 432)
- Inadimplência PF (série 21082)
- Poupança (série 25)
- Dados PIX via Olinda SPI

#### `POST /coleta/ibge`

Coleta dados demográficos do IBGE SIDRA v3.

Dados coletados:
- População por UF (Tabela 6579)
- Municípios por estado via BrasilAPI

#### `POST /coleta/febraban`

Extração de relatórios FEBRABAN e COAF em PDF.

Relatórios:
- Pesquisa FEBRABAN de Tecnologia Bancária 2024/2025
- Relatório de Atividades COAF 2023

#### `POST /coleta/ceps`

Coleta CEPs reais com coordenadas GPS.

Fontes:
- BrasilAPI v2 (primário)
- ViaCEP (fallback)
- 45 CEPs seed de metrópoles brasileiras expandidos para ~1.000

#### `POST /coleta/dados-gov`

Coleta datasets do portal dados.gov.br via API CKAN.

#### `POST /coleta/tudo`

Executa todos os coletores em paralelo.

#### `POST /coleta/local`

Indexa arquivos locais do diretório `/api/dados/`.

Formatos suportados:
- PDF (extração página por página via pdfplumber)
- CSV (chunking por coluna configurável)
- XLSX (conversão para texto estruturado)
- PPTX (extração de slides via python-pptx)
- ZIP (descompressão + processamento recursivo)
- TXT (chunking direto)

#### `GET /coleta/local/listar`

Lista arquivos disponíveis no diretório de dados.

#### `GET /coleta/status`

Status dos jobs de coleta em andamento.

---

### Regras — Geração de Regras de Fraude

#### `POST /regras/gerar`

Gera regras de fraude calibradas usando contexto do RAG + LLM.

**Response:**
- Diagnóstico dos padrões atuais
- Regras sugeridas com fundamentação
- Código Python para aplicar calibração

---

### LGPD — Compliance

#### `GET /lgpd/relatorio`

Relatório de compliance LGPD para o dataset completo.

Análise:
- Campos com dados pessoais (CPF, nome, endereço)
- Nível de anonimização
- Recomendações de tratamento

#### `POST /lgpd/relatorio-cliente`

Relatório LGPD para um cliente específico.

**Request:**

```json
{
  "customer_id": "CUST_000123"
}
```

---

## RAG — Como Funciona

### Indexação

```
Documento (PDF, CSV, texto)
    │
    ▼
Chunking (500 caracteres, 80 de overlap)
    │
    ▼
Embedding (paraphrase-multilingual-MiniLM-L12-v2, 384 dimensões)
    │
    ▼
Upsert no Qdrant (coleção: fraudflow-brasil)
    │
    Metadados: fonte, parte, texto original
```

### Consulta

```
Pergunta do usuário
    │
    ▼
Embedding da pergunta (mesmo modelo, 384d)
    │
    ▼
Busca por similaridade coseno no Qdrant (top_k resultados)
    │
    ▼
Documentos relevantes + scores
    │
    ▼
LLM (Gemini/Groq/OpenAI) sintetiza resposta
    │
    Prompt: "Especialista em fraudes financeiras BR"
    Instrução: citar fontes, mencionar dados numéricos
    │
    ▼
Resposta fundamentada com citações
```

### Modelo de Embedding

| Propriedade | Valor |
|-------------|-------|
| Modelo | `paraphrase-multilingual-MiniLM-L12-v2` |
| Dimensões | 384 |
| Idiomas | 50+ (inclui português) |
| Tamanho | ~120MB |
| Distância | Cosine similarity |

### Parâmetros de Chunking

| Parâmetro | Valor |
|-----------|-------|
| Tamanho do chunk | 500 caracteres |
| Overlap | 80 caracteres |
| Estratégia | Sliding window |

---

## LLM — Cadeia de Fallback

O sistema utiliza 3 providers em cadeia de fallback automática:

```
Gemini 2.5 Flash (primário)
    │ se falhar
    ▼
Groq Llama 3.3 70B (fallback)
    │ se falhar
    ▼
OpenAI GPT-4o-mini (terciário)
```

A seleção é automática:
- Se `LLM_PROVIDER=auto` (padrão): usa o primeiro com chave válida
- Se `LLM_PROVIDER=gemini`: usa Gemini, fallback para os demais
- Cada chamada que falha tenta automaticamente o próximo provider

---

## CORS

Origens permitidas:

| Origem | Propósito |
|--------|-----------|
| `https://fraudflow.abnerfonseca.com.br` | Produção |
| `https://abnerfonseca.com.br` | Site principal |
| `https://www.abnerfonseca.com.br` | Site principal (www) |
| `http://localhost:3000` | Desenvolvimento local (React) |
| `http://localhost:5173` | Desenvolvimento local (Vite) |

---

## Integração

### Python (httpx)

```python
import httpx

FRAUDFLOW_URL = "https://fraudflow.abnerfonseca.com.br"

async def consultar(pergunta: str) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{FRAUDFLOW_URL}/rag/query",
            json={"query": pergunta, "top_k": 5, "usar_llm": True}
        )
        resp.raise_for_status()
        return resp.json()
```

### JavaScript (fetch)

```javascript
const response = await fetch("https://fraudflow.abnerfonseca.com.br/rag/query", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "Quais os tipos de fraude mais comuns?",
    top_k: 5,
    usar_llm: true
  })
});
const { resposta_llm, contexto } = await response.json();
```

### cURL

```bash
curl -X POST https://fraudflow.abnerfonseca.com.br/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Taxa de fraude PIX 2024", "top_k": 3, "usar_llm": true}'
```
