# SynthFin — Criador e Equipe

## Abner Borda Fonseca

**Criador e único desenvolvedor do SynthFin.**

Engenheiro de software com mais de 6 anos de experiência em sistemas de alta escala, atualmente atuando como **Senior Information Security Specialist na SAP**. Transicionou de Mobile Engineering para Data Engineering e Segurança da Informação, com foco em detecção de fraudes financeiras e arquitetura de dados.

### Experiência relevante ao SynthFin

- **SAP** — Senior Information Security Specialist (2026–atual): segurança em ambiente enterprise de grande escala
- **Cast Group** — Engenheiro Mobile Sênior no App Banco do Brasil (2022–2026): apps com milhões de usuários, integração com APIs de alto volume transacional em ambiente fintech real
- **Boa Vista / Equifax** — Analista de Sistemas Pleno (2021–2022): produtos de score de crédito, ambiente data-driven com dados financeiros brasileiros reais
- **TargetTrust** — Instrutor Técnico (2021–2023): TypeScript avançado, engenharia de software moderna

### Por que o SynthFin foi criado

Não existem datasets brasileiros de qualidade para Machine Learning em detecção de fraude. Os dados disponíveis são anonimizados, fora do contexto brasileiro (sem PIX, sem CPF, sem ISPBs BACEN), ou insuficientes para treinar modelos robustos.

Com experiência em dados financeiros reais na Boa Vista/Equifax e apps bancários de alta escala no Banco do Brasil, Abner construiu um gerador tecnicamente preciso e juridicamente seguro (dados sintéticos, não dados reais).

### Conquistas técnicas

Pipeline de detecção de fraudes construído com dados do SynthFin:

| Métrica | Resultado |
|---|---|
| Dados processados | 51.2M transações (51 GB) |
| Throughput | ~85.000 transações/segundo |
| Compressão | 90% (51 GB JSON → 5 GB Parquet) |
| Recall do modelo | 89.88% |
| Valor protegido (simulado) | R$ 14.1 bilhões |

Arquitetura Medallion: `Raw JSON → Bronze (Parquet) → Silver (Clean) → Gold (Aggregated)`

### Stack técnico

**Data & ML:** Python, Apache Spark, Databricks, Delta Lake, Kafka, PySpark
**Bancos de dados:** PostgreSQL, MongoDB, Redis, MinIO
**Backend:** FastAPI, Node.js, TypeScript
**Frontend:** React Native, React.js, Angular
**AI & Automação:** LLMs, LangChain, N8N, Agentes de IA
**DevOps:** Docker, GitHub Actions, Traefik

### Projetos públicos

- **synthfin-core** — github.com/afborda/synthfin-core
- **spark-medallion-fraud-detection** — pipeline completo com Spark e arquitetura Medallion

### Contato

- **Email:** devabnerfonseca@gmail.com
- **GitHub:** github.com/afborda
- **Licenciamento comercial:** devabnerfonseca@gmail.com
- **Plataforma:** synthfin.com.br

### Sobre o projeto

O SynthFin é desenvolvido e mantido inteiramente por Abner. Toda a infraestrutura — API FastAPI, frontend Next.js, pipeline de dados, knowledge base RAG, ML Assistant — foi projetada e implementada por ele. Para questões técnicas, parcerias ou licenciamento, contate diretamente pelo email acima.