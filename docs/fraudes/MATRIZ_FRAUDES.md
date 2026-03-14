# 🔍 Matriz de Fraudes - Quick Reference
**Data**: Março de 2026  
**Uso**: Consulta rápida de todos os tipos de fraude documentados

---

## 📋 FRAUDESIMPLEMENTADAS ✅

| ID | Nome | Tipo | Taxa Real | Taxa Projeto | Status | Padrão |
|----|------|------|-----------|-------------|--------|--------|
| 1 | ENGENHARIA_SOCIAL | Transação | 23% | 20% | ✅ IMPL | Phishing, vishing, social manipulation |
| 2 | CONTA_TOMADA | Transação | 18% | 15% | ✅ IMPL | Account takeover, HIGH velocity, unusual time |
| 3 | CARTAO_CLONADO | Transação | 16% | 14% | ✅ IMPL | Card cloning, série rápida, novo local |
| 4 | BOLETO_FALSO | Transação | 8% | 2% | ⚠️ BAIXO | Boleto injetado, fake QR code |
| 5 | PIX_GOLPE | Transação | 8% | 10% | ✅ IMPL | PIX clonagem, QR falso, chave falsa |
| 6 | PHISHING | Transação | 6% | 6% | ✅ IMPL | Email/SMS, credential steal |
| 7 | FRAUDE_AMIGAVEL | Transação | 6% | 5% | ✅ IMPL | Chargeback fraud |
| 8 | IDENTIDADE_FALSA | Transação | 7% | 10% | ✅ IMPL | Synthetic ID, fake documents |
| 9 | SIM_SWAP | Transação | 4% | 3% | ✅ IMPL | Sim card duplication |
| 10 | AUTOFRAUDE | Transação | 0% | 8% | ❌ FAKE | First-party fraud (não existe puro) |
| 11 | GOLPE_WHATSAPP | Transação | 5% | 8% | ✅ IMPL | WhatsApp scams, fake support |
| 12 | LAVAGEM_DINHEIRO | Transação | 3% | 4% | ✅ IMPL | Money laundering patterns |
| 13 | TRIANGULACAO | Transação | 2% | 3% | ✅ IMPL | Triangulation schemes |
| 14 | GPS_SPOOFING | Ride-Share | 8% | 5% | ✅ IMPL | Fake location in rides |
| 15 | FAKE_RIDES | Ride-Share | 12% | 8% | ✅ IMPL | Non-existent trips, pickup=dropoff |
| 16 | DRIVER_COLLUSION | Ride-Share | 5% | 3% | ✅ IMPL | Coordinated fraud with passenger |

---

## 📋 FRAUDES DESCOBERTAS (Não Implementadas) ❌

### Cartão de Crédito - Card Present Fraud

| ID | Nome | Categoria | Taxa Real | Viabilidade | Esforço | Impacto ML |
|----|------|-----------|-----------|-------------|---------|-----------|
| 17 | Cartão Roubado/Perdido | Card Present | 5% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 18 | ATM Skimming | Card Present | 4% | MÉDIA | 2 sem | ⭐⭐⭐⭐⭐ |
| 19 | POS Skimming | Card Present | 6% | MÉDIA | 2 sem | ⭐⭐⭐⭐⭐ |
| 20 | Magnetic Stripe Clone | Card Present | 3% | BAIXA | 2 sem | ⭐⭐⭐ |

### Cartão Não-Presente (CNP)

| ID | Nome | Categoria | Taxa Real | Viabilidade | Esforço | Impacto ML |
|----|------|-----------|-----------|-------------|---------|-----------|
| 21 | Online Fraud | CNP | 8% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 22 | MOTO Fraud | CNP | 3% | MÉDIA | 1 sem | ⭐⭐⭐ |
| 23 | Card Testing | CNP | 6% | **ALTA** | **3 dias** | **⭐⭐⭐⭐⭐** |
| 24 | Teste com VPN/Proxy | CNP | 4% | ALTA | 4 dias | ⭐⭐⭐⭐ |

### PIX / Transferência

| ID | Nome | Categoria | Taxa Real | Viabilidade | Esforço | Impacto ML |
|----|------|-----------|-----------|-------------|---------|-----------|
| 25 | PIX Dicionário | PIX | 3% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 26 | PIX Sequestro (Malware) | PIX | 4% | MÉDIA | 2 sem | ⭐⭐⭐ |
| 27 | Boleto Replicado | Transferência | 2% | ALTA | 1 sem | ⭐⭐⭐ |
| 28 | TED/DOC MITM | Transferência | 2% | MÉDIA | 1 sem | ⭐⭐⭐⭐ |

### Identidade

| ID | Nome | Categoria | Taxa Real | Viabilidade | Esforço | Impacto ML |
|----|------|-----------|-----------|-------------|---------|-----------|
| 29 | Account Opening em Massa | Identidade | 3% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 30 | Trade Line Stacking | Identidade | 2% | MÉDIA | 1 sem | ⭐⭐⭐ |
| 31 | True-Name Fraud | Identidade | 2% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 32 | Identity Sitting | Identidade | 1% | ALTA | 1 sem | ⭐⭐⭐ |

### Device / App

| ID | Nome | Categoria | Taxa Real | Viabilidade | Esforço | Impacto ML |
|----|------|-----------|-----------|-------------|---------|-----------|
| 33 | APK Malicioso / Fake App | Device | 3% | MÉDIA | 2 sem | ⭐⭐⭐ |
| 34 | App Hijacking | Device | 2% | MÉDIA | 2 sem | ⭐⭐⭐⭐ |
| 35 | Malware Bancário | Device | 4% | BAIXA | 3 sem | ⭐⭐⭐ |
| 36 | Rootkit | Device | 1% | BAIXA | 4 sem | ⭐⭐ |
| 37 | Multi-Device Fraud | Device | 5% | ALTA | 2 sem | ⭐⭐⭐⭐⭐ |

### Operacional / Padrões

| ID | Nome | Categoria | Taxa Real | Viabilidade | Esforço | Impacto ML |
|----|------|-----------|-----------|-------------|---------|-----------|
| 38 | Micro-Burst Velocity | Operacional | 7% | **ALTA** | **3 dias** | **⭐⭐⭐⭐⭐** |
| 39 | Distributed Velocity | Operacional | 5% | **ALTA** | **1 sem** | **⭐⭐⭐⭐** |
| 40 | **Impossible Travel** | Operacional | 8% | **ALTA** | **3 dias** | **⭐⭐⭐⭐⭐** |
| 41 | Proxy/VPN Usage | Operacional | 4% | MÉDIA | 1 sem | ⭐⭐⭐ |
| 42 | Tor Browser Pattern | Operacional | 2% | MÉDIA | 1 sem | ⭐⭐⭐ |
| 43 | Bot Traffic | Operacional | 3% | MÉDIA | 2 sem | ⭐⭐⭐ |
| 44 | Reverse Hours | Operacional | 2% | ALTA | 3 dias | ⭐⭐⭐ |
| 45 | Scheduled Pattern | Operacional | 1% | ALTA | 4 dias | ⭐⭐⭐ |
| 46 | Peak Timing | Operacional | 2% | ALTA | 3 dias | ⭐⭐⭐ |
| 47 | Profile Deviation | Operacional | 6% | MÉDIA | 2 sem | ⭐⭐⭐⭐ |
| 48 | Channel Shift | Operacional | 3% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 49 | Velocity Change | Operacional | 4% | ALTA | 1 sem | ⭐⭐⭐⭐ |

### Ride-Share (Expandido)

| ID | Nome | Categoria | Taxa Real | Viabilidade | Esforço | Impacto ML |
|----|------|-----------|-----------|-------------|---------|-----------|
| 50 | Pickup Deception | Ride-Share | 3% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 51 | Acceptance Fraud | Ride-Share | 2% | ALTA | 1 sem | ⭐⭐⭐ |
| 52 | Non-Payment | Ride-Share | 5% | ALTA | 4 dias | ⭐⭐⭐⭐ |
| 53 | Injury Claim | Ride-Share | 2% | MÉDIA | 1 sem | ⭐⭐⭐ |
| 54 | Item Left Behind Fraud | Ride-Share | 3% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 55 | Destination Disparity | Ride-Share | 2% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 56 | Coupon Stacking | Ride-Share | 3% | ALTA | 1 sem | ⭐⭐⭐⭐ |
| 57 | Promo Code Farming | Ride-Share | 4% | ALTA | 1 sem | ⭐⭐⭐⭐⭐ |
| 58 | Stolen Credit Card (Ride) | Ride-Share | 2% | ALTA | 4 dias | ⭐⭐⭐⭐ |
| 59 | Chargeback Loop (Ride) | Ride-Share | 1% | MÉDIA | 1 sem | ⭐⭐⭐ |
| 60 | Refund Abuse | Ride-Share | 4% | **ALTA** | **1 sem** | **⭐⭐⭐⭐** |
| 61 | Account Takeover (Ride) | Ride-Share | 1% | ALTA | 1 sem | ⭐⭐⭐ |

### Advanced / Coordinated

| ID | Nome | Categoria | Taxa Real | Viabilidade | Esforço | Impacto ML |
|----|------|-----------|-----------|-------------|---------|-----------|
| 62 | Fraud Rings | Advanced | 8% | ALTA | 2 sem | ⭐⭐⭐⭐⭐ |
| 63 | Cross-Border Networks | Advanced | 2% | BAIXA | 3 sem | ⭐⭐ |
| 64 | Dark Web Data Trading | Advanced | 1% | BAIXA | 2 sem | ⭐⭐ |

---

## 🎯 TOP 10 POR IMPLEMENTAR (Ordem de Prioridade)

| Rank | ID | Nome | Taxa | Esforço | Impacto | ETA |
|------|----|----|------|---------|--------|-----|
| 🥇 1 | 40 | **Impossible Travel** | 8% | 3 dias | ⭐⭐⭐⭐⭐ | Semana 1 |
| 🥇 2 | 38 | **Card Testing** | 6% | 3 dias | ⭐⭐⭐⭐⭐ | Semana 1 |
| 🥇 3 | 39 | **Distributed Velocity** | 5% | 1 sem | ⭐⭐⭐⭐ | Semana 2 |
| 🥈 4 | 62 | **Fraud Rings** | 8% | 2 sem | ⭐⭐⭐⭐⭐ | Semana 3-4 |
| 🥈 5 | 23 | **Card Testing** | 6% | 3 dias | ⭐⭐⭐⭐⭐ | Semana 1 |
| 🥈 6 | 57 | **Promo Code Farming (Ride)** | 4% | 1 sem | ⭐⭐⭐⭐⭐ | Semana 3 |
| 🥉 7 | 60 | **Refund Abuse** | 4% | 1 sem | ⭐⭐⭐⭐ | Semana 2 |
| 🥉 8 | 37 | **Multi-Device Fraud** | 5% | 2 sem | ⭐⭐⭐⭐⭐ | Semana 4-5 |
| 🥉 9 | 47 | **Profile Deviation** | 6% | 2 sem | ⭐⭐⭐⭐ | Semana 4 |
| 🥉 10 | 18 | **POS/ATM Skimming** | 10% | 2 sem | ⭐⭐⭐⭐⭐ | Semana 5 |

---

## 🔧 MELHORIAS ESTRUTURAIS (Não fraudes, mas padrões)

| Melhoria | Impacto ML | Esforço | Prioridade |
|----------|-----------|--------|-----------|
| **Geoloc Clustering** | ⭐⭐⭐⭐⭐ | 1 sem | 🔴 CRÍTICO |
| **Sazonalidade Mensal** | ⭐⭐⭐⭐⭐ | 1 sem | 🔴 CRÍTICO |
| **Picos Intra-Dia** | ⭐⭐⭐⭐ | 3 dias | 🔴 CRÍTICO |
| **Device Consistency** | ⭐⭐⭐⭐ | 1 sem | 🟠 ALTO |
| **Merchant Clustering** | ⭐⭐⭐⭐ | 1 sem | 🟠 ALTO |
| **Channel Preference** | ⭐⭐⭐ | 3 dias | 🟡 MÉDIO |
| **Account Ramp-Up** | ⭐⭐⭐ | 1 sem | 🟡 MÉDIO |

---

## 📊 RESUMO POR CATEGORIAS

### Completude Atual

```
Cartão Clássico        [████░░░░░░] 40% (4 de 10)
PIX/Transferência      [██░░░░░░░░] 20% (2 de 10)
Identidade             [██░░░░░░░░] 25% (2 de 8)
Device/App             [█░░░░░░░░░] 10% (1 de 9)
Operacional            [███░░░░░░░] 25% (3 de 12)
Ride-Share             [███░░░░░░░] 30% (3 de 10)
---
TOTAL                  [███░░░░░░░] 22% (14 de 64)
```

### Gap de Implementação

**Onde estamos deixando de cobrir:**
- ❌ Cartão clássico (Skimming, CNP, testing)
- ❌ PIX avançado (Dicionário, sequestro)
- ❌ Padrões operacionais (Velocity distribuída, Impossible travel, Ring)
- ❌ Ride-share (Passenger fraud, Promo abuse, refund)

**Onde estamos bem cobertos:**
- ✅ Engenharia social
- ✅ Conta tomada
- ✅ PIX básico

---

## 🎓 COMO USAR MATRIZ

1. **Para decidir próxima fraude**: Verifique TOP 10 por implementar
2. **Para comparar com realidade**: Veja "Taxa Real" vs "Taxa Projeto"
3. **Para priorizar por impacto ML**: Ordene por ⭐ de Impacto ML
4. **Para estimar timeline**: Olhe coluna "Esforço" (em semanas ou dias)
5. **Para roadmap**: Veja seção TOP 10, respeitando dependências

---

## 📝 LEGENDA

| Símbolo | Significado |
|---------|-----------|
| ✅ IMPL | Implementado e funcionando |
| ⚠️ BAIXO | Implementado mas taxa muito baixa |
| ❌ NÃO | Não implementado |
| ❌ FAKE | Implementado mas não existe na realidade |
| ALTA | Fácil de implementar e realista |
| MÉDIA | Moderadamente complexo |
| BAIXA | Muito complexo ou pouco valor |
| ⭐ | 1-5 stars de impacto em ML (5 = muito importante) |

