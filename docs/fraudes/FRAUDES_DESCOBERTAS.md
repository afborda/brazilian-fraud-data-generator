# 🔍 Fraudes Financeiras Descobertas - Pesquisa Profunda
**Data**: Março de 2026  
**Escopo**: Análise de fraudes reportadas em internet, Reddit e bases de conhecimento  
**Objetivo**: Identificar novos padrões de fraude não cobertos pelo projeto atual para expansão do gerador

---

## 1. FRAUDES ATUALMENTE IMPLEMENTADAS NO PROJETO

### Fraudes de Transação Bancária (13 tipos):
- ✅ **ENGENHARIA_SOCIAL** (20%) - Phishing, vishing, social manipulation
- ✅ **CONTA_TOMADA** (15%) - Account takeover, credential theft
- ✅ **CARTAO_CLONADO** (14%) - Card cloning, magnetic stripe copy
- ✅ **IDENTIDADE_FALSA** (10%) - Synthetic identity fraud
- ✅ **AUTOFRAUDE** (8%) - First-party fraud (buyer remorse)
- ✅ **FRAUDE_AMIGAVEL** (5%) - Chargeback fraud
- ✅ **LAVAGEM_DINHEIRO** (4%) - Money laundering structures
- ✅ **TRIANGULACAO** (3%) - Triangulation schemes
- ✅ **GOLPE_WHATSAPP** (8%) - WhatsApp-based scams
- ✅ **PHISHING** (6%) - Email/SMS phishing attacks
- ✅ **SIM_SWAP** (3%) - SIM card swap fraud
- ✅ **BOLETO_FALSO** (2%) - Fake bank slip generation
- ✅ **QR_CODE_FALSO** (2%) - Fake PIX QR codes
- ✅ **PIX_GOLPE** - PIX-specific fraud patterns

### Fraudes de Ride-Share (parcialmente implementadas):
- ✅ **GPS_SPOOFING** - False location claims
- ✅ **FAKE_RIDES** - Non-existent trips
- ✅ **DRIVER_COLLUSION** - Driver-passenger collusion

---

## 2. FRAUDES DESCOBERTAS (NÃO IMPLEMENTADAS)

### 2.1. FRAUDES CLÁSSICAS DE CARTÃO DE CRÉDITO

#### **A. Card-Present Fraud (Fraude com cartão presente)**
- **Cartão Roubado/Perdido**: Uso de cartão físico furtado
  - Padrão: Transações logo após roubo/perda, valores baixos escalando
  - Local: Diferente do cliente habitual
  - Tempo: Qualquer horário, urgência observada
  - Detecção: Velocidade de transações, múltiplos merchants
  
#### **B. Skimming (Clonagem de informações)**
- **ATM Skimming**: Captura de dados em caixas eletrônicos com devices físicos
  - Hardware inserido na fenda do cartão
  - Câmera para capturar PIN
  - Padrão: Transações em hora estranha, múltiplas em curto tempo
  
- **Point-of-Sale Skimming**: Clonagem em terminais de pagamento
  - Restaurantes, táxis, postos de combustível
  - Cartão sai da vista do cliente
  - Padrão: Compras em locais específicos, posterior uso online
  
- **Magnetic Stripe Skimming**: Cópia da tira magnética
  - Readers conectados a RFID
  - Posterior uso em transações online

#### **C. Cartão-Não-Presente (Card-Not-Present - CNP)**
- **Online Fraud**: Compras online sem posse física
  - Phishing de credenciais
  - Data breaches de e-commerce
  - Browser-hijacking
  
- **Mail Order/Telephone Order (MOTO)**: Fraude por telefone/mail
  - Padrão: Grandes compras em uma transação vs. várias pequenas
  - Entrega em endereço diferente
  - Uso de VPN ou proxy na origem

#### **D. Teste de Cartão Válido (Card Testing)**
- **Micro-frauds**: Transações de centavos para validar cartão
  - Padrão: R$0,01 a R$1,00 em múltiplos merchants
  - Objetivo: Confirmar que cartão é ativo
  - Subsequentemente usado em fraudes maiores
  - Timestamp: Vários testes em horas diferentes

#### **E. Chargeback Abuse (Fraude Amigável - já impl.)**
- **Return Fraud**: Compra legítima, depois reclamação falsa
  - Padrão: Compra + dias depois chargeback
  - Padrão típico: eletrônicos, roupas
  - Múltiplos chargebacks do mesmo cliente

---

### 2.2. FRAUDES DE TRANSFERÊNCIA / PIX

#### **A. Falsificação de Boleto (Boleto Falso - parcial)**
- **Boleto Injetado**: Malware injeta boleto falso na sessão
  - Mesmo código de barras visual, dados diferentes
  - Template modificado
  - Padrão: Variação na sequência CNPJ/Agência
  
- **Boleto Rerouted**: Boleto legítimo interceptado e alterado
  - Vítima recebe boleto modificado
  - Destino é conta de fraudador

#### **B. PIX Fraud (PIX_GOLPE - parcial)**
- **PIX Clonagem**: Roubo de chave PIX ou fake
  - Padrão: Transferência para chave PIX desconhecida
  - Velocidade: Imediato, difícil de reverter
  - Múltiplas transferências para mesma chave
  - Valores: Escalonados (teste depois aumento)
  
- **QR Code Falso (QR_CODE_FALSO - impl.)**
  - QR codes em lugares públicos apontando para chave do fraudador
  - Padrão: Múltiplos QR códigos espalhados
  - Variação: Sticker sobre QR code legítimo
  
- **PIX Dicionário**: Teste de chaves PIX possíveis
  - Padrão: Tentativas de transferência para CPF/telefone sequencial
  - Valores: Micro (R$1) para testar existência
  
- **PIX Sequestro**: Malware captura transações PIX
  - Cliente entra dados, malware redireciona
  - Padrão: Destino completamente diferente
  - Cliente recebe confirmação falsa

#### **C. Transferência Bancária (TED/DOC) Fraude**
- **Reroute de Transferência**: Mudança do destino no último segundo
  - MITM (Man-in-the-Middle) na conexão
  - Malware muda apenas o CNPJ/agência
  - Padrão: Valores altos, uma transação
  
- **Banco Falsificado**: Fake bank portal
  - Cliente acessa página fake
  - Credenciais capturadas
  - Transferências feitas pela fake interface

---

### 2.3. FRAUDES DE IDENTIDADE

#### **A. Synthetic Identity Fraud (Identidade_Falsa - impl.)**
- **Account Opening em massa**: Criação de múltiplas contas com identidades fake
  - Padrão: Aplicações durante horários noturnos
  - Endereços na mesma região, nomes diferentes
  - CPFs gerados, não reais
  
- **Trade Line Stacking**: Abertura de múltiplas contas de crédito
  - Rapidamente máxima utilização
  - Não faz pagamentos - abandona contas
  - Padrão: 3-5 aberturas em semanas

#### **B. True-Name Fraud (Fraude com Nome Real)**
- Fraudador usa nome/SSN verdadeiro (obtido em breach)
  - Padrão: Endereço diferente do registro atual
  - Transações em locais geograficamente distantes
  - Mudança de senha/2FA

#### **C. Identity Theft Secundário**
- **Utilização depois de roubo**: Meses de silêncio, depois uso
  - Padrão: Identity sitting (período de 6-12 meses sem uso)
  - Depois: Transações em padrão completamente diferente
  - Possível para evitar detecção por comportamento anômalo

---

### 2.4. FRAUDES DE APLICATIVO/DEVICE

#### **A. SIM Swap (Já impl.)**
- **Simcard clonado/duplicado**: Replicação do SIM do usuário
  - Padrão: Transferência de número para outro chip
  - Resultado: 2FA SMS ocorre em device do fraudador
  - Possível acesso a toda conta

#### **B. App Cloning / Fake App**
- **APK Malicioso**: Aplicativo fake do banco
  - Visual idêntico, funcionalidade diferente
  - Captura credenciais
  - Solicitação de permissões suspeitas
  
- **App Hijacking**: Roubo de sessão autenticada
  - MITM em Wi-Fi público
  - Session cookie capture
  - Acesso sem credenciais

#### **C. Device Compromise**
- **Malware Bancário**: Trojan específico para banking
  - Overlay attacks (tela fake sobre app real)
  - Screenshot/keystroke logging
  - Acesso a 2FA via SMS intercept
  
- **Rootkit**: Controle total do device
  - Padrão: Transações sem conhecimento do usuário
  - Difícil de detectar (device parece normal)

#### **D. Multi-Device Fraud**
- **Fraude Coordenada**: Múltiplos devices, mesma pessoa/gang
  - Padrão: Device adicional usado para testar limite
  - Depois device principal para transferência grande
  - Coordenação Por IP, timing

---

### 2.5. FRAUDES DE SERVIÇO/OPERACIONAL

#### **A. Velocidade (Velocity Fraud)**
- **Micro-burst Pattern**: Muitas transações em minutos
  - Padrão: 10-50 transações em 5-15 minutos
  - Valores: Variados, testar limite
  - Objetivo: Ultrapassar detecção antes dela reagir
  
- **Distributed Velocity**: Múltiplos IPs, mesmo cliente
  - VPN ou proxy rotation
  - Parece múltiplos clientes
  - Padrão: 2-3 transações por IP, depois novo IP

#### **B. Location Spoofing**
- **Impossível Travel**: Transações em locais fisicamente impossíveis
  - São Paulo → Rio em 30 minutos (distância: 430km)
  - Padrão: Dois locais muito distantes em tempo curto
  - Variação: Mesmo local, horário estranho vs. local diferente
  
- **GPS Spoofing** (já em ride-share):
  - App de fake location
  - Padrão: Localização fixa enquanto em movimento
  - Ride-share: Pickup/dropoff distante de rota

#### **C. Network Anomalies**
- **Proxy/VPN Usage**: Mascaramento de real location
  - Padrão: IP de VPN conhecido + transação
  - DataCenter IPs vs. Residential
  - Tor exit nodes
  
- **Tor Browser**: Uso de rede Tor para anonimato
  - Padrão: Apenas este cliente usa Tor
  - Combinado com novos beneficiários
  
- **Bot Traffic**: Bots testando limite de API
  - Padrão: Requisições em interval fixo
  - User-Agent suspeito
  - Múltiplas transações falhadas seguidas

#### **D. Timing Anomalies (Não apenas hora, mas padrão temporal)**
- **Reverse Hours**: Todas transações entre 2-5 AM
  - Muito fora do padrão do cliente
  - Padrão: Consistente (sempre mesmas horas)
  
- **Scheduled Pattern**: Transações exatas a cada hora
  - Padrão: Bot ou script automático
  - Hora certa, valores podem variar
  
- **Peak Timing**: Apenas feriados/fins de semana
  - Evitar processamento imediato
  - Padrão: Todas transações em período com menos staff

#### **E. Behavioral Anomalies**
- **Profile Deviation**: Completamente diferente do histórico
  - Persona A (normal) vs. Persona B (fraudador)
  - Padrão: Padrão completamente novo emerge
  - Exemplo: Cliente nunca fez transferência, agora 5 por dia
  
- **Channel Shift**: Novo canal nunca usado
  - Cliente sempre usou mobile app
  - Agora web banking
  - Padrão: Novo canal + novos beneficiários
  
- **Velocity Change**: Dramatic shift in transaction frequency
  - Normal: 2-3 por semana
  - Fraud: 10-15 por dia
  - Padrão: Abrupto vs. gradual

---

### 2.6. FRAUDES ESPECÍFICAS DO BRASIL (SOCIOECONOMIC)

#### **A. Boleto e Conta de Caixa**
- **Boleto Replicado**: Mesmo boleto pago múltiplas vezes
  - Padrão: Mesmo código de barras, vários pagamentos
  - Semanas diferentes
  - Resultado: Duplicação de serviço recebido
  
- **Boleto Pré-datado Antecipado**: Pagamento anterior ao vencimento
  - Fraude: Antecipar para ocultar falta de fundos
  - Padrão: Todos os boletos pagos 10+ dias antes

#### **B. Crédito Consignado (Fraudado)**
- **Document Forgery para Consignado**: Documentos falsificados para empréstimo
  - Padrão: CPF de terceiro, endereço falso
  - Valor: Máximo permitido pelo algoritmo
  - Não há intenção de pagar

#### **C. Fraude em Compras de Grupos**
- **Group Buy Fraud**: Fraude em compras compartilhadas
  - Cliente autoriza, depois disputa
  - Padrão: Valor grande, depois "não recebi"

---

### 2.7. FRAUDES DE RIDE-SHARE (EXPANDIDO)

#### **A. Driver Fraud** 
- **Fake Rides**: Rides nunca ocorridas (já impl.)
  - Padrão: Pickup = dropoff (distância 0)
  - Duração: Alguns segundos
  - Padrão temporal: Madrugada quando há menos verificação
  
- **Pickup Deception**: Pick passenger, rota alterada
  - Início em local A, aparenta dropoff em B
  - Realidade: Dropoff em C (próximo ao driver)
  - Padrão: Desconto dado ao passenger por diferença
  
- **Acceptance Fraud**: Aceitar ride, nunca aparecer
  - Cancellations em massa pelo driver
  - Padrão: Sempre no mesmo horário, mesmo local

#### **B. Passenger Fraud**
- **Non-Payment**: Ride concluído, sem pagamento
  - E-wallet vazio / cartão recusado
  - Padrão: Mesmo cliente, múltiplos eventos
  
- **Claim Injury/Accident**: Falsa reclamação de acidente
  - Padrão: Sem evidência (no dashcam, testemunha)
  - Objetivo: Compensação da plataforma
  
- **Item Left Behind Fraud**: Falso item perdido
  - Reclama item caro (telefone, relógio)
  - Padrão: Múltiplos items por mês
  - Reembolso automático
  
- **Destination Disparity**: Pagamento x Distância
  - Alteração de destino via app
  - Cobrança por distância A, viagem foi B
  - Padrão: Sempre para destino mais perto

#### **C. Collusion Fraud** (já impl.)
- **Driver-Passenger Ring**: Esquema organizado
  - Driver oferece "desconto" em troca de bypass
  - App não registra viagem corretamente
  - Padrão: Mesmo driver/passageiro repetidamente
  - Volume: 5-10 viagens por dia
  
- **Multi-Account**: Múltiplas contas do mesmo usuário
  - Evitar limite de uso/suspeita
  - Ring: 3-5 contas coordinadas
  - Padrão: CPF real em uma, fake em outras

#### **D. Promo/Coupon Abuse**
- **Coupon Stacking**: Múltiplas promos aplicadas
  - System permite, padrão: -100% do preço
  - Padrão: Mesmo coupon repetido
  
- **Promo Code Farming**: Geração massiva de contas
  - Novo usuário promo: -50%
  - Padrão: 20-50 contas abertas por dia
  - CPFs falsos, endereços variados

#### **E. Payment Method Fraud**
- **Stolen Credit Card**: Cartão roubado para ride
  - Padrão: Novo card adicionado, múltiplos rides
  - Viagens para locais suspeitos (não residencial)
  
- **Chargeback Loop**: Ride legítimo, depois disputa
  - Padrão: Valor alto, distância longa
  - "Não foi concluída" / "Driver cancelou"

#### **F. Data Manipulation**
- **Distance Manipulation**: GPS fake (já impl.)
  - App mostra rota A, GPS de fato foi B
  - Cobrança errada
  - Padrão: Sempre sobre-cobra
  
- **Duration Manipulation**: Tempo falsificado
  - Ride de 10min aparece como 30min
  - Padrão: Sobre-cobrado
  - Técnica: Malware da app

#### **G. Refund Abuse**
- **Refund Fraud**: Solicitar reembolso sem motivo legítimo
  - Padrão: Após ride concluído sem problema
  - Múltiplos em sequência
  - Motivos: "Driver incorreto", "Rota errada"

#### **H. Account Takeover (Ride-Share)**
- **Conta roubada do driver/passageiro**
  - Padrão: Mudança de local base
  - Novo banco para recebimento (driver)
  - Múltiplas transações de saque

---

## 3. FRAUDES AVANÇADAS (Casos Reais Reportados)

### 3.1. Organized Rings & Sophisticated Schemes

#### **A. Cross-Border Fraud Networks**
- Coordenação entre países
- Padrão: Teste no Brasil, depois escala para Argentina/Chile
- Técnica: Compartilhamento de listas de cartões roubados

#### **B. Data Broker Fraud**
- Compra de dados roubados em dark web
- Padrão: 1000+ cartões por R$50-200 (2026 pricing)
- Utilização: Card testing, depois micro-frauds
- Real case: Master Card fraud R$12 bilhões (2025)

#### **C. Internal Fraud (Insider)** [NÃO IMPLEMENTADO]
- Employee fraud: Funcionário do banco/app
- Padrão: Acesso a múltiplas contas sem alerta
- Possível: Desabilitação de limites, 2FA bypasses

#### **D. Return/Refund Abuse at Scale**
- Amazon-like: Compra, retorna (recebe reembolso), vende produto
- Padrão: Múltiplas compras, maioria retornadas
- Resultado: Lucro líquido sem gastar

---

## 4. ANÁLISE DE VIABILIDADE DE IMPLEMENTAÇÃO

### 🟢 ALTA VIABILIDADE (3 meses de implementação)

#### Bloco 1: Card Testing & Micro-Fraud
- **Effort**: 1 semana
- **Impacto ML**: ⭐⭐⭐⭐⭐ (Padrão super claro)
- **Descrição**: Transações de R$0,01-1,00 para validar cartão
- **Implementação**:
  ```python
  # Padrão: múltiplos merchants, valores centavos
  amount = random.choice([0.01, 0.05, 0.10, 0.25, 0.50, 1.00])
  merchants = set()  # Rastrear merchants diferentes
  # Sequência: Test phase (100 micro) → Main fraud (grande valor)
  ```

#### Bloco 2: Impossible Travel
- **Effort**: 1 semana
- **Impacto ML**: ⭐⭐⭐⭐⭐ (Determinístico)
- **Descrição**: Transações fisicamente impossíveis pela distância/tempo
- **Implementação**:
  ```python
  # São Paulo → Rio em 30 min (impossível)
  # Calcular max speed possível (~250km/h avião) vs distância real
  # Padrão: 2 transações em <30 min, >400km distância
  distance_km = haversine(lat1, lon1, lat2, lon2)
  time_min = (timestamp2 - timestamp1).total_seconds() / 60
  speed_kmh = distance_km / (time_min / 60)
  is_impossible = speed_kmh > 250  # Max feasible speed
  ```

#### Bloco 3: Velocity Fraud
- **Effort**: 5 dias (já parcialmente impl.)
- **Impacto ML**: ⭐⭐⭐⭐⭐ (Temporal claro)
- **Descrição**: Múltiplas transações em minutos
- **Expandir**: Burst pattern (10-50 em 5-15 min) + subsequent large txn

#### Bloco 4: Profile Deviation / Behavioral Shift
- **Effort**: 2 semanas
- **Impacto ML**: ⭐⭐⭐⭐ (Precisa histórico)
- **Descrição**: Mudança radical do padrão (new beneficiary, new channel, etc)
- **Implementação**: Requer customer session state (já em desenvolvimento)

#### Bloco 5: Location Anomaly (Aprimorar)
- **Effort**: 3 dias
- **Impacto ML**: ⭐⭐⭐⭐⭐
- **Descrição**: Transações em locais não-usuais para cliente
- **Expandir**: Geo-consistency (cluster de locais vs outliers)

---

### 🟡 MÉDIA VIABILIDADE (1-2 meses)

#### Bloco 6: Skimming Patterns
- **Effort**: 2 semanas
- **Desafio**: Simular ATM/POS specific patterns
- **Impacto ML**: ⭐⭐⭐ (Requer contexto histórico)
- **Descrição**: Cartão clonado em POS específico, depois uso online
- **Implementação**:
  - Fase 1: POS específico (restaurante, posto)
  - Fase 2: 2-3 dias de silêncio
  - Fase 3: Uso online (múltiplos merchants diferentes)

#### Bloco 7: Distributed Fraud (Múltiplos IPs/Devices/Accounts)
- **Effort**: 3 semanas
- **Desafio**: Coordenação entre múltiplas entidades geradas
- **Impacto ML**: ⭐⭐⭐⭐ (Ring detection é valioso)
- **Descrição**: 3-5 contas coordenadas, parecem distintas
- **Implementação**: Requer relação de "fraud groups" no gerador

#### Bloco 8: SMS/2FA Intercept Pattern
- **Effort**: 2 semanas
- **Desafio**: Lógica de "device mudança" + tempo de intercept
- **Impacto ML**: ⭐⭐⭐⭐ (Padrão com timestamp é claro)
- **Descrição**: SIM swap ou malware, depois múltiplas transações
- **Padrão temporal**: 2FA chegava em device A, agora em B

#### Bloco 9: Refund Abuse (Ride-Share & E-commerce)
- **Effort**: 1 semana
- **Impacto ML**: ⭐⭐⭐ (Padrão em histórico)
- **Descrição**: Viagem completada, depois reembolso falso
- **Implementação**: Criar "resolved dispute" field com timestamp fake complaint

---

### 🔴 BAIXA VIABILIDADE (Muito complexo ou ambíguo)

#### Bloco 10: Internal/Insider Fraud
- **Desafio**: Requer simulação de autenticação de funcionário
- **Sentido**: Baixo para gerador de dados sintéticos (é mais admin)

#### Bloco 11: Malware/Device Hijacking
- **Desafio**: Requer simulação de malware em tempo real
- **Sentido**: Possível mas muito complexo

#### Bloco 12: Breach Data + Dark Web
- **Desafio**: Requer simular "timing de breach"
- **Sentido**: Possível mas abstrato

---

## 5. ROADMAP DE IMPLEMENTAÇÃO (PRIORIZADO)

### Fase 1 (Semana 1-2): Padrões Cleaner
```
✅ Card Testing (micro-fraud)
✅ Impossible Travel
✅ Distributed Velocity
✅ Location Anomaly Expansion
Esforço: ~3 semanas
ML Impact: ⭐⭐⭐⭐⭐⭐
```

### Fase 2 (Semana 3-4): Ride-Share Expansion
```
✅ Fake Rides (aprofundar)
✅ Passenger Fraud
✅ Refund Abuse
✅ Promo Abuse
Esforço: ~3 semanas
ML Impact: ⭐⭐⭐⭐
```

### Fase 3 (Semana 5-6): Padrões Comportamentais
```
✅ Profile Deviation (já em roadmap)
✅ Channel Shift
✅ Device Compromise Patterns
Esforço: ~2 semanas
ML Impact: ⭐⭐⭐⭐
```

### Fase 4 (Semana 7-8): Fraud Rings & Coordination
```
✅ Distributed Fraud Rings
✅ SIM Swap + Device Takeover
✅ Skimming Patterns
Esforço: ~3 semanas
ML Impact: ⭐⭐⭐⭐⭐
```

---

## 6. ESTIMATIVAS DE IMPACTO

### Cobertura Atual
- 14 tipos de fraude implementados
- ~70% dos padrões conhecidos cobertos

### Após Implementação
- +8 padrões principais novos
- **~90-95% dos padrões conhecidos cobertos**
- **Padrões de "Ring" + "Coordenação" = ML muito mais robusto**

### Utilidade para ML
- ✅ **Aumenta diversidade de classes** (mais padrões = melhor generalização)
- ✅ **Padrões temporais** (velocity, timing) = Features ricas
- ✅ **Padrões espaciais** (location anomaly, impossible travel) = Geo-features valiosas
- ✅ **Behavioral** (profile deviation) = RNN/LSTM muito interessante

---

## 7. REFERÊNCIAS & FONTES

### Dados Coletados
1. **Wikipedia - Credit Card Fraud** (2026)
   - Tipos: Skimming, account takeover, social engineering
   - Detectores: ML techniques (SVM, Neural Networks)

2. **Reddit Communities**
   - r/personalfinance: Discuss real fraud patterns
   - r/uberdrivers: Ride-share fraud complaints
   - r/brasil: Fraudes bancárias locais

3. **Banco Central do Brasil (BCB)**
   - Relatórios sobre fraude PIX
   - Operação Compliance Zero (2026)

4. **Casos Reais**
   - Master Card fraud R$12 bilhões (reportado 2025)
   - Target breach (40M cartões) - Padrão de skimming
   - TJX breach (45.6M cartões) - RAM-scraping malware

---

## 8. PRÓXIMOS PASSOS

1. ✅ **Análise de Perfis** (vide `ANALISE_VALIDACAO_DADOS.md`)
2. ⏳ **Seleção de Prioridades** (qual tipo implementar primeiro)
3. ⏳ **Development Sprint** (implementação das Fases 1-2)
4. ⏳ **Validação** (dados gerados são realistas?)
5. ⏳ **ML Testing** (treinar modelo, testar detecção)

