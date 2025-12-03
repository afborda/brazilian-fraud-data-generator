# 🇧🇷 Brazilian Fraud Data Generator

<div align="center">

[![en](https://img.shields.io/badge/lang-en-red.svg)](./README.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](./README.pt-BR.md)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Faker](https://img.shields.io/badge/Faker-pt__BR-green)
![License](https://img.shields.io/badge/License-MIT-blue)
[![Stars](https://img.shields.io/github/stars/afborda/brazilian-fraud-data-generator?style=social)](https://github.com/afborda/brazilian-fraud-data-generator)

**Gerador de dados sintéticos de transações bancárias brasileiras para estudos de Data Engineering e Machine Learning**

[🚀 Quick Start](#-quick-start) •
[📊 Dados Gerados](#-dados-gerados) •
[⚙️ Parâmetros](#️-parâmetros) •
[🎯 Casos de Uso](#-casos-de-uso)

</div>

---

## 📋 Sobre

Este projeto gera **dados sintéticos realistas** de transações bancárias brasileiras, incluindo:

- ✅ **Clientes** com CPF, nome, endereço, renda (Faker pt_BR)
- ✅ **Dispositivos** (smartphones, tablets, desktops com fabricantes reais)
- ✅ **Transações** (PIX, cartão crédito/débito, TED, boleto, saque)
- ✅ **Fraudes** (8 tipos diferentes com distribuição realista)
- ✅ **Geolocalização** correlacionada com estado do cliente
- ✅ **Bancos** reais brasileiros com market share realista
- ✅ **MCCs** com valores típicos por categoria
- ✅ **Padrões temporais** (mais transações em horário comercial)

### 🎯 Por que foi criado?

Estudando **Data Engineering**, precisei de um dataset grande e realista para:
- Testar pipelines Apache Spark em escala
- Praticar arquitetura Medallion (Bronze → Silver → Gold)
- Treinar modelos de detecção de fraude
- Simular cenários de Big Data (50GB+)

Não encontrei datasets brasileiros de qualidade, então criei este gerador!

---

## 🚀 Quick Start

### Instalação

```bash
# Clone o repositório
git clone https://github.com/afborda/brazilian-fraud-data-generator.git
cd brazilian-fraud-data-generator

# Instale as dependências
pip install -r requirements.txt
```

### Gerar dados

```bash
# Gerar 1GB de dados (teste rápido)
python3 generate.py --size 1GB

# Gerar 10GB de dados
python3 generate.py --size 10GB --workers 4

# Gerar 50GB de dados (recomendado para Big Data)
python3 generate.py --size 50GB --workers 8

# Gerar dados reproduzíveis (mesmo seed = mesmos dados)
python3 generate.py --size 1GB --seed 42
```

### Resultado

```
output/
├── customers.json      # 100K clientes brasileiros
├── devices.json        # 300K dispositivos
└── transactions_*.json # Arquivos de ~128MB cada (JSON Lines)
```

---

## ⚙️ Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--size` | `1GB` | Tamanho total dos dados (ex: `1GB`, `10GB`, `50GB`) |
| `--workers` | `CPU cores` | Número de processos paralelos |
| `--fraud-rate` | `0.007` | Taxa de fraude (0.7% = ~7 a cada 1000) |
| `--output` | `./output` | Diretório de saída |
| `--customers` | `100000` | Número de clientes a gerar |
| `--devices` | `3x customers` | Número de dispositivos a gerar |
| `--days` | `730` | Dias de histórico (padrão 2 anos) |
| `--start-date` | - | Data inicial (YYYY-MM-DD) |
| `--end-date` | - | Data final (YYYY-MM-DD) |
| `--seed` | - | Seed para reprodutibilidade |
| `--quiet` | - | Modo silencioso (JSON output) |
| `--customers-only` | - | Gerar apenas clientes e dispositivos |

### Exemplos

```bash
# Teste rápido (500MB, 2 workers)
python3 generate.py --size 500MB --workers 2

# Produção (50GB, máximo de workers, 1% fraude)
python3 generate.py --size 50GB --workers 10 --fraud-rate 0.01

# Período específico
python3 generate.py --size 5GB --start-date 2024-01-01 --end-date 2024-06-30

# Reproduzível (sempre gera os mesmos dados)
python3 generate.py --size 1GB --seed 42

# Para scripts/CI (saída JSON)
python3 generate.py --size 1GB --quiet

# Customizado (20GB, 200K clientes)
python3 generate.py --size 20GB --customers 200000 --output ./meus_dados
```

---

## 📊 Dados Gerados

### 👥 Clientes (`customers.json`)

```json
{
  "customer_id": "CUST_00000001",
  "nome": "Maria Silva Santos",
  "cpf": "123.456.789-00",
  "email": "maria.silva@email.com.br",
  "telefone": "(11) 98765-4321",
  "data_nascimento": "1985-03-15",
  "endereco": {
    "logradouro": "Rua das Flores, 123",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01310-100"
  },
  "renda_mensal": 5500.00,
  "profissao": "Analista de Sistemas",
  "conta_criada_em": "2018-06-01T10:30:00",
  "tipo_conta": "DIGITAL",
  "status_conta": "ATIVA",
  "limite_credito": 22000.00,
  "score_credito": 750,
  "nivel_risco": "BAIXO",
  "banco_codigo": "260",
  "banco_nome": "Nubank",
  "agencia": "0001",
  "numero_conta": "123456-7"
}
```

### 📱 Dispositivos (`devices.json`)

```json
{
  "device_id": "DEV_00000001",
  "customer_id": "CUST_00000001",
  "tipo": "SMARTPHONE",
  "fabricante": "Samsung",
  "modelo": "Galaxy S23",
  "sistema_operacional": "Android 14",
  "fingerprint": "a1b2c3d4e5f6789...",
  "primeiro_uso": "2023-01-15",
  "is_trusted": true,
  "is_rooted_jailbroken": false
}
```

### 💳 Transações (`transactions_*.json`)

```json
{
  "transaction_id": "TXN_000000000000001",
  "customer_id": "CUST_00000001",
  "session_id": "SESS_000000000001",
  "device_id": "DEV_00000001",
  "timestamp": "2024-03-15T14:32:45.123456",
  "tipo": "PIX",
  "valor": 150.00,
  "moeda": "BRL",
  "canal": "APP_MOBILE",
  "ip_address": "177.45.123.89",
  "geolocalizacao_lat": -23.550520,
  "geolocalizacao_lon": -46.633308,
  "merchant_id": "MERCH_012345",
  "merchant_name": "Carrefour",
  "merchant_category": "Supermercados",
  "mcc_code": "5411",
  "mcc_risk_level": "low",
  "numero_cartao_hash": null,
  "bandeira": null,
  "tipo_cartao": null,
  "parcelas": null,
  "entrada_cartao": null,
  "cvv_validado": null,
  "autenticacao_3ds": null,
  "chave_pix_tipo": "CPF",
  "chave_pix_destino": "a1b2c3d4e5f6...",
  "banco_destino": "341",
  "distancia_ultima_transacao_km": 5.23,
  "tempo_desde_ultima_transacao_min": 45,
  "transacoes_ultimas_24h": 3,
  "valor_acumulado_24h": 450.00,
  "horario_incomum": false,
  "novo_beneficiario": false,
  "status": "APROVADA",
  "motivo_recusa": null,
  "fraud_score": 12.5,
  "is_fraud": false,
  "fraud_type": null
}
```

---

## 🏦 Bancos Suportados

Os bancos são selecionados com peso proporcional ao market share real:

| Código | Banco | Tipo | Peso |
|--------|-------|------|------|
| 001 | Banco do Brasil | Público | 15% |
| 341 | Itaú Unibanco | Privado | 15% |
| 104 | Caixa Econômica | Público | 14% |
| 237 | Bradesco | Privado | 12% |
| 033 | Santander | Privado | 10% |
| 260 | Nubank | Digital | 10% |
| 077 | Banco Inter | Digital | 5% |
| 336 | C6 Bank | Digital | 4% |
| 290 | PagBank | Digital | 3% |
| ... | +7 outros | ... | ... |

---

## 🚨 Tipos de Fraude

O gerador inclui **8 tipos de fraude** com distribuição baseada em dados reais:

| Tipo | Descrição | % do Total |
|------|-----------|------------|
| `ENGENHARIA_SOCIAL` | Golpes por telefone/WhatsApp | ~25% |
| `CONTA_TOMADA` | Account takeover | ~20% |
| `CARTAO_CLONADO` | Cartão físico/dados clonados | ~18% |
| `IDENTIDADE_FALSA` | Documentos falsos | ~12% |
| `AUTOFRAUDE` | Cliente alega fraude falsa | ~10% |
| `FRAUDE_AMIGAVEL` | Fraude por conhecidos | ~7% |
| `LAVAGEM_DINHEIRO` | Transações de lavagem | ~5% |
| `TRIANGULACAO` | Fraude com intermediários | ~3% |

---

## 📈 Realismo dos Dados

### Distribuição de Transações
- **PIX**: 45% (domina no Brasil desde 2021)
- **Cartão de Crédito**: 25%
- **Cartão de Débito**: 15%
- **Boleto**: 8%
- **TED**: 4%
- **Saque**: 3%

### Canais
- **App Mobile**: 60%
- **Web Banking**: 25%
- **ATM**: 8%
- **Agência**: 5%
- **WhatsApp Pay**: 2%

### Padrões Temporais
- Mais transações entre 8h-20h
- Pico às 12h-14h e 18h-20h
- Madrugada (0h-6h) marcada como `horario_incomum`

### Valores por Categoria (MCC)
- **Fast Food**: R$ 15-100
- **Supermercados**: R$ 15-800
- **Combustível**: R$ 50-500
- **Eletrônicos**: R$ 100-8.000
- **Joalherias**: R$ 200-15.000

---

## 📈 Performance

Testado em VPS com 8 cores / 24GB RAM:

| Tamanho | Arquivos | Tempo | Velocidade |
|---------|----------|-------|------------|
| 1 GB | 8 | ~1 min | 17 MB/s |
| 10 GB | 80 | ~8 min | 21 MB/s |
| 50 GB | 400 | ~35 min | 24 MB/s |

> 💡 **Dica:** Use `--workers` igual ao número de cores da CPU para máxima performance

---

## 🎯 Casos de Uso

### 1️⃣ Estudar Apache Spark

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("FraudAnalysis").getOrCreate()

# Ler transações
df = spark.read.json("output/transactions_*.json")
df.printSchema()
df.show()

# Análise de fraudes
df.filter("is_fraud = true").groupBy("fraud_type").count().show()
```

### 2️⃣ Treinar modelo de ML

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Carregar dados
df = pd.read_json("output/transactions_00000.json", lines=True)

# Features
features = ['valor', 'fraud_score', 'transacoes_ultimas_24h', 
            'valor_acumulado_24h', 'horario_incomum', 'novo_beneficiario']
X = df[features]
y = df['is_fraud']

# Treinar
model = RandomForestClassifier()
model.fit(X, y)
```

### 3️⃣ Pipeline Medallion

```
Raw (JSON) → Bronze (Parquet) → Silver (Limpo) → Gold (Agregado)
   51 GB   →      5 GB        →      5.4 GB    →     2 GB
                              90% compressão!
```

### 4️⃣ Dashboards de BI

Conecte Metabase, PowerBI ou Tableau para criar dashboards de:
- Taxa de fraude por estado
- Tipos de fraude mais comuns
- Análise temporal de transações
- Top merchants suspeitos

---

## 📁 Estrutura do Projeto

```
brazilian-fraud-data-generator/
├── 📄 README.md          # Documentação
├── 📄 requirements.txt   # Dependências (faker)
├── 📄 generate.py        # Script principal
├── 📄 LICENSE            # MIT License
├── 📂 examples/          # Exemplos de uso
│   └── README.md
└── 📂 output/            # Dados gerados (gitignore)
    ├── customers.json
    ├── devices.json
    └── transactions_*.json
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! 

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Ideias para contribuir:
- [ ] Adicionar mais tipos de transação (DOC, débito automático)
- [ ] Exportar para CSV/Parquet
- [ ] Adicionar validação de CPF com dígito verificador
- [ ] Suporte a outros países da América Latina

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

**Abner Fonseca**
- LinkedIn: [linkedin.com/in/abnerfonseca](https://www.linkedin.com/in/abner-fonseca-25658b67)
- GitHub: [@afborda](https://github.com/afborda)

---

## ⭐ Gostou?

Se este projeto te ajudou, deixa uma ⭐ no repositório!

---

<div align="center">

**Feito com ❤️ para a comunidade de Data Engineering brasileira**

</div>
