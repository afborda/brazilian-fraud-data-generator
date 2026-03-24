# Índice — Análise Estratégica de 19 de março de 2026

Análise completa do estado do produto, mercado de fraudes e estratégia de monetização.

---

## Documentos desta pasta

### [01_PESQUISA_MERCADO_FRAUDES_2024_2025.md](./01_PESQUISA_MERCADO_FRAUDES_2024_2025.md)
Pesquisa de mercado baseada em dados reais de 2024-2025.
- Escala das perdas no Brasil (R$10,1 bi em 2024, +17%)
- Os 8 padrões de fraude mais relevantes hoje
- O que os modelos de ML realmente precisam (Amazon FDB research)
- Análise competitiva completa (PaySim, IEEE-CIS, Gretel, MOSTLY AI)
- Gaps identificados no nosso produto com prioridade de implementação

### [02_FREE_VS_PAGO_ESTRATEGIA_SAAS.md](./02_FREE_VS_PAGO_ESTRATEGIA_SAAS.md)
Estratégia de monetização cruzada com o estado do produto.
- 5 perfis de usuário e o que cada um precisa
- Matriz completa de features por plano (Free → Enterprise)
- Raciocínio por trás de cada corte free/pago
- Features que NUNCA devem ser open source
- Estratégia de atualização contínua como moat de longo prazo

### [03_PRODUTO_PAGO_VS_OPEN_SOURCE.md](./03_PRODUTO_PAGO_VS_OPEN_SOURCE.md)
Referência direta de diferenciação — base para materiais de venda.
- Feature por feature: o que muda na qualidade do dado
- Velocity windows, clustering geográfico, device consistency
- Padrões exclusivos do produto pago
- Argumentos prontos para uso em vendas

---

## Decisões estratégicas derivadas desta análise

```
1. Velocity windows completas (1h/6h/7d/30d)
   → Implementar AGORA. Bloqueia vendas para times de ML.
   → Somente Pro+. Não vai para o open source.

2. Clustering geográfico por cliente
   → Implementar AGORA. Maior fonte de ruído nos dados.
   → Somente Pro+.

3. Grafo de mulas estruturado
   → Implementar próximas 4 semanas.
   → Somente Team+. Diferencial para GNN fraud detection.

4. Impossible travel
   → Implementar junto com clustering geo.
   → Somente Pro+.

5. Atualização mensal de padrões
   → Processo a implementar. Principal argumento de retenção.
   → Diferencia pago de open source de forma permanente.
```

---

## Contexto

Esta análise foi realizada em 19/03/2026 com base em:
- Leitura completa do código-fonte do gerador e da API
- Pesquisa em fontes primárias (Banco Central, Febraban, arXiv)
- Análise de competidores e datasets públicos
- Cruzamento com documentação interna existente (TURNOS_IMPLEMENTACAO.md, MATRIZ_FRAUDES.md, RISCO_COMMODITY.md, PLANOS_PAGOS_IA.md)
