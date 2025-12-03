# 🇧🇷 Brazilian Fraud Data Generator

<div align="center">

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

- ✅ **Clientes** com CPF, nome, endereço (Faker pt_BR)
- ✅ **Dispositivos** (smartphones, tablets, desktops)
- ✅ **Transações** (PIX, cartão, TED, boleto)
- ✅ **Fraudes** (8 tipos diferentes com taxa configurável)
- ✅ **Geolocalização** brasileira real
- ✅ **Bancos** reais (códigos BACEN)

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
python generate.py --size 1GB

# Gerar 10GB de dados
python generate.py --size 10GB --workers 4

# Gerar 50GB de dados (recomendado para Big Data)
python generate.py --size 50GB --workers 8
```

### Resultado

```
data/
├── customers.json      # 100K clientes brasileiros
├── devices.json        # 300K dispositivos
└── transactions_*.json # Arquivos de 128MB cada
```

---

## ⚙️ Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--size` | `1GB` | Tamanho total dos dados (ex: `1GB`, `10GB`, `50GB`) |
| `--workers` | `CPU cores` | Número de processos paralelos |
| `--fraud-rate` | `0.007` | Taxa de fraude (0.7% = ~7 a cada 1000) |
| `--output` | `./data` | Diretório de saída |
| `--customers` | `100000` | Número de clientes a gerar |
| `--devices-per-customer` | `3` | Dispositivos por cliente |

### Exemplos

```bash
# Teste rápido (500MB, 2 workers)
python generate.py --size 500MB --workers 2

# Produção (50GB, máximo de workers, 1% fraude)
python generate.py --size 50GB --workers 10 --fraud-rate 0.01

# Customizado (20GB, 200K clientes)
python generate.py --size 20GB --customers 200000 --output ./meus_dados
```

---

## 📊 Dados Gerados

### 👥 Clientes (`customers.json`)

```json
{
  "customer_id": "CUST_00000001",
  "nome": "Maria Silva Santos",
  "cpf": "123.456.789-00",
  "data_nascimento": "1985-03-15",
  "email": "maria.silva@email.com.br",
  "telefone": "(11) 98765-4321",
  "endereco": {
    "logradouro": "Rua das Flores, 123",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01310-100"
  },
  "renda_mensal": 5500.00,
  "score_credito": 750,
  "banco_principal": "341",
  "conta_desde": "2018-06-01"
}
```

### 📱 Dispositivos (`devices.json`)

```json
{
  "device_id": "DEV_00000001",
  "customer_id": "CUST_00000001",
  "tipo": "SMARTPHONE",
  "fabricante": "Samsung",
  "modelo": "Galaxy S21",
  "sistema_operacional": "Android 13",
  "fingerprint": "a1b2c3d4e5f6...",
  "primeiro_uso": "2023-01-15",
  "is_trusted": true
}
```

### 💳 Transações (`transactions_*.json`)

```json
{
  "transaction_id": "TXN_000000000000001",
  "customer_id": "CUST_00000001",
  "device_id": "DEV_00000001",
  "timestamp": "2024-03-15T14:32:45",
  "tipo": "PIX",
  "valor": 150.00,
  "moeda": "BRL",
  "canal": "APP_MOBILE",
  "ip_address": "177.45.123.89",
  "geolocalizacao_lat": -23.550520,
  "geolocalizacao_lon": -46.633308,
  "merchant_name": "Supermercado Extra",
  "merchant_category": "Supermercados",
  "mcc_code": "5411",
  "chave_pix_tipo": "CPF",
  "chave_pix_destino": "123.456.789-00",
  "banco_destino": "341",
  "fraud_score": 12.5,
  "is_fraud": false,
  "fraud_type": null,
  "status": "APROVADA"
}
```

---

## 🚨 Tipos de Fraude

O gerador inclui **8 tipos de fraude** baseados em cenários reais:

| Tipo | Descrição | % do Total |
|------|-----------|------------|
| `CARTAO_CLONADO` | Cartão físico/dados clonados | ~15% |
| `CONTA_TOMADA` | Account takeover | ~15% |
| `IDENTIDADE_FALSA` | Documentos falsos | ~12% |
| `ENGENHARIA_SOCIAL` | Golpes por telefone/WhatsApp | ~18% |
| `LAVAGEM_DINHEIRO` | Transações de lavagem | ~10% |
| `AUTOFRAUDE` | Cliente alega fraude falsa | ~12% |
| `FRAUDE_AMIGAVEL` | Fraude por conhecidos | ~10% |
| `TRIANGULACAO` | Fraude com intermediários | ~8% |

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
df = spark.read.json("data/transactions_*.json")
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
df = pd.read_json("data/transactions_00000.json", lines=True)

# Features
X = df[['valor', 'fraud_score', 'transacoes_ultimas_24h']]
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
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 generate.py           # Script principal
├── 📄 LICENSE
├── 📂 generators/
│   ├── customers.py         # Gerador de clientes
│   ├── devices.py           # Gerador de dispositivos
│   └── transactions.py      # Gerador de transações
└── 📂 data/                  # Dados gerados (gitignore)
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
- [ ] Gerar dados de cartões de crédito
- [ ] Adicionar padrões temporais realistas
- [ ] Suporte a outros países da América Latina

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

**Abner Fonseca**
- LinkedIn: [linkedin.com/in/abnerfonseca](https://linkedin.com/in/abnerfonseca)
- GitHub: [@afborda](https://github.com/afborda)

---

## ⭐ Gostou?

Se este projeto te ajudou, deixa uma ⭐ no repositório!

---

<div align="center">

**Feito com ❤️ para a comunidade de Data Engineering brasileira**

</div>
