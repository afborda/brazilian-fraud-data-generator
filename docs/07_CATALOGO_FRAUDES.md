# Catálogo de Fraudes

## Visão Geral

O SynthFin simula **25 tipos de fraude bancária** e **11 tipos de fraude ride-share**, calibrados com dados públicos reais do Banco Central, FEBRABAN e COAF.

Cada tipo tem:
- **Prevalência** — % de ocorrência entre fraudes (calibrado via RAG)
- **Multiplicador de valor** — Quanto o valor da fraude difere do legítimo
- **Score base** — Score de risco base do tipo
- **Score de evidência RAG** — Confiança na calibração (0 a 1)

---

## Fraudes Bancárias (25 tipos)

### Engenharia Social e Manipulação

#### 1. ENGENHARIA_SOCIAL
**Prevalência:** 28% | **Score base:** 0.35 | **RAG:** 0.86

A fraude mais comum no Brasil. Criminoso manipula a vítima por telefone, SMS ou WhatsApp para realizar transferências voluntárias.

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Baixa |
| Velocidade | Normal |
| Horário típico | Comercial (9h-18h) |
| Canal | Mobile, telefone |
| Beneficiário novo | 85% dos casos |

#### 2. FALSA_CENTRAL_TELEFONICA
**Prevalência:** 10% | **Score base:** 0.78 | **RAG:** 0.83

Criminoso liga se passando por funcionário do banco. Convence a vítima a fornecer senhas, tokens ou realizar transferências "de segurança".

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Média |
| Beneficiário novo | 85% |
| Padrão | Ligação ativa durante transação |
| Valor típico | R$ 2.000 – R$ 20.000 |

#### 3. WHATSAPP_CLONE
**Prevalência:** 5% | **Score base:** 0.25 | **RAG:** 0.77

Criminoso clona o WhatsApp da vítima e pede dinheiro emprestado aos contatos.

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Baixa |
| Beneficiário novo | 70% |
| Padrão | Mensagens familiares a contatos |
| Valor típico | R$ 500 – R$ 5.000 |

#### 4. SEQUESTRO_RELAMPAGO
**Prevalência:** 3% | **Score base:** 0.60 | **RAG:** 0.71

Vítima é coagida fisicamente a realizar transferências múltiplas.

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Alta |
| Transações | 2-6 em sequência rápida |
| Horário | Noturno/madrugada |
| Valor total | R$ 5.000 – R$ 50.000 |

---

### Fraudes PIX

#### 5. PIX_GOLPE
**Prevalência:** 25% | **Score base:** 0.55 | **RAG:** 0.89

Fraude específica do sistema PIX. Inclui golpes do Pix errado, QR Code falso, e transferências induzidas.

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Média |
| Beneficiário novo | 65% |
| Canal | Mobile dominante |
| Valor médio | R$ 1.778 – R$ 2.979 |
| Taxa | 4,5 a 6,2 por 100K transações |

#### 6. PIX_AGENDADO_FRAUDE
**Prevalência:** 2% | **Score base:** 0.50 | **RAG:** 0.60

Exploração do Pix agendado para realizar transferências programadas fraudulentas.

#### 7. QR_CODE_ADULTERADO
**Prevalência:** 2% | **Score base:** 0.55 | **RAG:** 0.65

QR Code legítimo é substituído por um fraudulento em estabelecimentos ou boletos.

---

### Fraudes de Conta e Identidade

#### 8. CONTA_TOMADA (Account Takeover)
**Prevalência:** 15% | **Score base:** 0.75 | **RAG:** 0.82

Criminoso obtém acesso à conta da vítima via phishing, malware ou credenciais vazadas.

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Alta |
| Velocidade | Burst (5-15 transações) |
| Device | Novo/não confiável |
| IP | Diferente do habitual |

#### 9. MAO_FANTASMA (RAT Fraud)
**Prevalência:** 4% | **Score base:** 0.85 | **RAG:** 0.76

Malware de acesso remoto (RAT) controla o dispositivo da vítima. Transações ocorrem enquanto a vítima dorme.

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Alta |
| Horário | Madrugada (2h-5h) |
| Device | O próprio da vítima (RAT) |
| Controle | Remoto via trojan |

#### 10. SIM_SWAP
**Prevalência:** 3% | **Score base:** 0.80 | **RAG:** 0.73

Criminoso transfere o número de telefone da vítima para um novo SIM, ganhando acesso a SMS de autenticação.

| Característica | Valor |
|----------------|-------|
| Anomalia | Alta |
| Device | Novo após swap |
| Padrão | Troca de device + transações imediatas |

#### 11. CREDENTIAL_STUFFING
**Prevalência:** 3% | **Score base:** 0.90 | **RAG:** 0.70

Bots testam credenciais vazadas em massa contra sistemas bancários.

| Característica | Valor |
|----------------|-------|
| Velocidade | Burst extremo (20-100 tentativas) |
| Pattern | Automatizado (bot) |
| Success rate | Baixo (1-3%) |

#### 12. SYNTHETIC_IDENTITY
**Prevalência:** 2% | **Score base:** 0.20 | **RAG:** 0.65

Identidade fabricada combinando dados reais e fictícios. Conta fica dormente por meses antes de ativação.

| Característica | Valor |
|----------------|-------|
| Score inicial | Muito baixo (parece legítimo) |
| Dormancy | Meses sem atividade |
| Ativação | Burst de crédito/transações |

---

### Fraudes de Cartão

#### 13. CARTAO_CLONADO
**Prevalência:** 14% | **Score base:** 0.65 | **RAG:** 0.85

Dados do cartão são copiados (skimming, data breach) e usados em transações não presenciais.

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Média |
| Padrão | Escalação progressiva |
| Geolocalização | Distante do habitual |
| Entry mode | E-commerce, contactless |

#### 14. CARD_TESTING
**Prevalência:** 7% | **Score base:** 0.75 | **RAG:** 0.78

Teste de cartões roubados com micro-transações antes de compras grandes.

| Característica | Valor |
|----------------|-------|
| Fase 1 | Micro (R$ 1-5) — teste de validade |
| Fase 2 | Pequena (R$ 10-30) — teste de limite |
| Fase 3 | Grande (R$ 500+) — compra real |
| MCC típico | Grocery, e-commerce |

#### 15. COMPRA_TESTE
**Prevalência:** 8% | **Score base:** 0.50 | **RAG:** 0.74

Transações de valor mínimo para verificar se o cartão está ativo.

| Característica | Valor |
|----------------|-------|
| Valor | R$ 1 – R$ 30 |
| Velocidade | Burst |
| Anomalia | Nenhuma (valores micro) |

---

### Fraudes de Velocidade

#### 16. MICRO_BURST_VELOCITY
**Prevalência:** 5% | **Score base:** 0.80 | **RAG:** 0.72

Múltiplas transações em intervalo muito curto (minutos).

| Característica | Valor |
|----------------|-------|
| Volume | 10-50 transações |
| Janela | 5-15 minutos |
| Device | Novo |

#### 17. DISTRIBUTED_VELOCITY
**Prevalência:** 4% | **Score base:** 0.78 | **RAG:** 0.68

Fraude distribuída usando rotação de dispositivos para evitar detecção de velocidade.

| Característica | Valor |
|----------------|-------|
| Pattern | 2-3 transações por device |
| Rotação | Múltiplos devices |
| Objetivo | Evitar regras de velocity |

---

### Fraudes Financeiras Complexas

#### 18. FRAUDE_APLICATIVO
**Prevalência:** 12% | **Score base:** 0.60 | **RAG:** 0.80

Uso de apps falsos, proxy/VPN, ou dispositivos comprometidos.

| Característica | Valor |
|----------------|-------|
| Anomalia device | Alta |
| Indicadores | Proxy, VPN, emulador |

#### 19. BOLETO_FALSO
**Prevalência:** 8% | **Score base:** 0.40 | **RAG:** 0.81

Boleto adulterado com dados bancários do criminoso.

| Característica | Valor |
|----------------|-------|
| Beneficiário novo | 90% |
| Anomalia de valor | Baixa (parece legítimo) |
| Canal | E-mail, WhatsApp |

#### 20. MULA_FINANCEIRA
**Prevalência:** 6% | **Score base:** 0.70 | **RAG:** 0.75

Conta usada como intermediária para lavagem de dinheiro. Padrão passthrough: recebe e repassa rapidamente.

| Característica | Valor |
|----------------|-------|
| Anomalia de valor | Alta |
| Padrão | Passthrough (recebe → envia) |
| Velocidade | Rápida (minutos entre receber e enviar) |

#### 21. DEPOSITO_ENVELOPE_VAZIO
**Prevalência:** 1% | **Score base:** 0.45 | **RAG:** 0.55

Depósito em caixa eletrônico de envelope vazio, gerando crédito provisório.

#### 22. FRAUDE_CONSIGNADO
**Prevalência:** 2% | **Score base:** 0.50 | **RAG:** 0.62

Contratação de empréstimo consignado usando dados de terceiros.

#### 23. EMPRESTIMO_IDENTIDADE_FALSA
**Prevalência:** 2% | **Score base:** 0.55 | **RAG:** 0.58

Solicitação de crédito com identidade fabricada ou roubada.

#### 24. FRAUDE_SEGURO
**Prevalência:** 1% | **Score base:** 0.45 | **RAG:** 0.52

Sinistro fraudulento em seguros vinculados a contas bancárias.

#### 25. LAVAGEM_ESTRUTURADA
**Prevalência:** 2% | **Score base:** 0.65 | **RAG:** 0.70

Fragmentação de valores grandes em múltiplas transações abaixo do limite de reporte.

| Característica | Valor |
|----------------|-------|
| Padrão | Structuring (smurfing) |
| Valor por transação | Abaixo de R$ 10.000 |
| Volume | Múltiplas contas/beneficiários |

---

## Fraudes Ride-Share (11 tipos)

| # | Tipo | Descrição |
|---|------|-----------|
| 1 | **GHOST_RIDE** | Corrida fantasma — motorista marca como concluída sem passageiro |
| 2 | **GPS_SPOOFING** | Adulteração de GPS para inflar distância/tarifa |
| 3 | **SURGE_ABUSE** | Exploração de surge pricing artificial |
| 4 | **PROMO_ABUSE** | Uso de múltiplas contas para cupons de desconto |
| 5 | **DRIVER_COLLUSION** | Conluio motorista-passageiro para fraude |
| 6 | **FAKE_ACCOUNT** | Conta de motorista ou passageiro falsa |
| 7 | **PAYMENT_FRAUD** | Pagamento com cartão roubado/contestado |
| 8 | **CANCEL_ABUSE** | Cancelamentos estratégicos para penalizar motorista |
| 9 | **RATING_MANIPULATION** | Manipulação de avaliações |
| 10 | **MULTI_APP_FRAUD** | Fraude coordenada entre múltiplos apps |
| 11 | **IDENTITY_SWAP** | Troca de motorista (pessoa diferente do cadastro) |

---

## Distribuição de Prevalências

### Top 10 Fraudes por Prevalência

```
ENGENHARIA_SOCIAL      ████████████████████████████  28%
PIX_GOLPE              █████████████████████████     25%
CONTA_TOMADA           ███████████████               15%
CARTAO_CLONADO         ██████████████                14%
FRAUDE_APLICATIVO      ████████████                  12%
FALSA_CENTRAL_TEL.     ██████████                    10%
BOLETO_FALSO           ████████                       8%
COMPRA_TESTE           ████████                       8%
CARD_TESTING           ███████                        7%
MULA_FINANCEIRA        ██████                         6%
```

*Nota: Prevalências somam >100% pois representam proporções relativas, normalizadas em runtime.*

---

## Schema de Override (fraud_pattern_overrides.json)

Cada tipo de fraude no arquivo de overrides contém:

```json
{
  "TIPO_FRAUDE": {
    "prevalence": 0.28,
    "amount_multiplier": [4.0, 14.0],
    "fraud_score_base": 0.35,
    "prev_synthfin_original": 0.20,
    "score_evidencia_rag": 0.86,
    "pareto_shape": 1.5,
    "pareto_scale": 500.0,
    "_nota": "Fonte: BCB+FEBRABAN — 28-35% das fraudes reportadas"
  }
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `prevalence` | float | Proporção entre fraudes (0.28 = 28%) |
| `amount_multiplier` | [min, max] | Multiplicador sobre valor médio legítimo |
| `fraud_score_base` | float | Score de risco base (0 a 1) |
| `prev_synthfin_original` | float | Valor original antes da calibração |
| `score_evidencia_rag` | float | Confiança da evidência RAG (0 a 1) |
| `pareto_shape` | float | Shape da distribuição Pareto de valores |
| `pareto_scale` | float | Scale da distribuição Pareto |
| `_nota` | string | Citação da fonte de dados |

---

## Fontes de Calibração

| Fonte | Dados Utilizados |
|-------|-----------------|
| BCB PIX Fraud Stats | Taxa de fraude PIX (4-6 por 100K), valores médios |
| BCB SGS | Inadimplência, CDI, SELIC (correlação com fraude) |
| FEBRABAN Banking Tech | Mix de canais, adoção digital, volume por tipo |
| COAF Activity Reports | Tipologias de lavagem, operações suspeitas |
| IBGE Demographics | Concentração por UF (SP 30%, RJ 12%, MG 9%) |
| Aliança Nacional | Tipologias de golpes emergentes |
| GolpeBR | Padrões de fraude consumer-facing |
| Dados acadêmicos | Papers sobre detecção de fraude |

---

## Score de Evidência RAG

O score de evidência RAG indica a confiança na calibração:

| Faixa | Significado |
|-------|-------------|
| 0.85 – 1.00 | Excelente — múltiplas fontes convergentes |
| 0.70 – 0.84 | Bom — fontes parciais mas confiáveis |
| 0.50 – 0.69 | Moderado — extrapolação de dados limitados |
| < 0.50 | Baixo — estimativa sem forte evidência |

**Score médio atual: 0.807**
