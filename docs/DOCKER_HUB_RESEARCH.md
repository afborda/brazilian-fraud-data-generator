# 🔬 Pesquisa: Publicação no Docker Hub com Versionamento

Este documento contém a pesquisa realizada sobre melhores práticas para publicar projetos no Docker Hub com versionamento profissional.

---

## 📚 Fontes Consultadas

- [Docker Hub Repositories Documentation](https://docs.docker.com/docker-hub/repos/)
- [GitHub Actions for Docker](https://docs.docker.com/build/ci/github-actions/)
- [Docker Multi-platform Builds](https://docs.docker.com/build/building/multi-platform/)

---

## 🏗️ Arquitetura de Publicação

### Docker Hub Repositories

O Docker Hub é o registro padrão para imagens Docker. Principais características:

| Recurso | Descrição |
|---------|-----------|
| **Repositórios Públicos** | Ilimitados e gratuitos |
| **Repositórios Privados** | 1 gratuito, mais com plano pago |
| **Webhooks** | Notificações automáticas após push |
| **Automated Builds** | Build automático via GitHub/Bitbucket |
| **Vulnerability Scanning** | Análise de segurança (planos pagos) |

### Estrutura de Nomes

```
<namespace>/<repository>:<tag>

Exemplos:
- afborda/brazilian-fraud-data-generator:latest
- afborda/brazilian-fraud-data-generator:v4.0.0
- afborda/brazilian-fraud-data-generator:4.0.0
```

---

## 🔄 CI/CD com GitHub Actions

### Workflow Recomendado

O fluxo ideal usa GitHub Actions com as seguintes actions oficiais:

```yaml
# Actions principais
- docker/setup-qemu-action@v3      # Emulação multi-platform
- docker/setup-buildx-action@v3    # Builder avançado
- docker/login-action@v3           # Login no Docker Hub
- docker/metadata-action@v5        # Geração automática de tags
- docker/build-push-action@v5      # Build e push
```

### Triggers Recomendados

| Evento | Ação |
|--------|------|
| Push para `main/master` | Build com tag `latest` |
| Push de tag `v*.*.*` | Build com tags semânticas |
| Pull Request | Build sem push (apenas teste) |
| Manual (workflow_dispatch) | Build sob demanda |

---

## 🏷️ Estratégia de Versionamento

### Semantic Versioning (SemVer)

Formato: `MAJOR.MINOR.PATCH`

| Componente | Quando Incrementar |
|------------|-------------------|
| **MAJOR** | Mudanças incompatíveis (breaking changes) |
| **MINOR** | Novas funcionalidades compatíveis |
| **PATCH** | Correções de bugs compatíveis |

### Tags Geradas Automaticamente

Usando `docker/metadata-action`, uma tag `v4.0.0` gera:

```
:latest        → Última versão estável
:v4.0.0        → Versão exata com prefixo v
:4.0.0         → Versão exata sem prefixo
:4.0           → Major.Minor (auto-update patch)
:4             → Major only (auto-update minor/patch)
:sha-abc1234   → Commit SHA específico
```

### Pre-releases

| Tag | Uso |
|-----|-----|
| `v4.0.0-alpha` | Versão experimental |
| `v4.0.0-beta` | Versão para testes |
| `v4.0.0-rc.1` | Release Candidate |

---

## 🖥️ Multi-Platform Builds

### Plataformas Suportadas

As mais comuns para containers de aplicação:

| Plataforma | Arquitetura | Uso |
|------------|-------------|-----|
| `linux/amd64` | x86_64 | Servidores, desktops Intel/AMD |
| `linux/arm64` | ARM 64-bit | Apple M1/M2, AWS Graviton, Raspberry Pi 4 |
| `linux/arm/v7` | ARM 32-bit | Raspberry Pi 3 e anteriores |

### Comando de Build Multi-Platform

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag afborda/brazilian-fraud-data-generator:v4.0.0 \
  --push \
  .
```

### Pré-requisitos

1. **Docker Buildx** (incluído no Docker Desktop)
2. **QEMU** para emulação de arquiteturas
3. **Containerd image store** ou builder customizado

```bash
# Instalar QEMU
docker run --privileged --rm tonistiigi/binfmt --install all

# Criar builder multi-platform
docker buildx create --name multiplatform --use
docker buildx inspect --bootstrap
```

---

## 📋 OCI Image Labels

Labels padronizados para metadados da imagem:

```dockerfile
LABEL org.opencontainers.image.title="Nome do Projeto"
LABEL org.opencontainers.image.description="Descrição"
LABEL org.opencontainers.image.authors="nome@email.com"
LABEL org.opencontainers.image.url="https://github.com/user/repo"
LABEL org.opencontainers.image.source="https://github.com/user/repo"
LABEL org.opencontainers.image.version="4.0.0"
LABEL org.opencontainers.image.created="2025-01-15T00:00:00Z"
LABEL org.opencontainers.image.revision="abc1234"
LABEL org.opencontainers.image.licenses="MIT"
```

---

## 🔐 Autenticação

### Docker Hub Access Token

1. Acessar https://hub.docker.com/settings/security
2. Criar novo Access Token com permissões:
   - **Read** - Baixar imagens
   - **Write** - Fazer push de imagens
   - **Delete** - Remover tags (opcional)

### GitHub Secrets Necessários

| Secret | Descrição |
|--------|-----------|
| `DOCKERHUB_USERNAME` | Username do Docker Hub |
| `DOCKERHUB_TOKEN` | Access Token (não a senha!) |

---

## 📊 Boas Práticas Identificadas

### Dockerfile

1. ✅ Usar imagem base específica (ex: `python:3.11-slim`)
2. ✅ Usar multi-stage builds quando possível
3. ✅ Minimizar layers combinando RUN commands
4. ✅ Usar `.dockerignore` para reduzir contexto
5. ✅ Não incluir secrets na imagem
6. ✅ Adicionar HEALTHCHECK
7. ✅ Usar labels OCI padronizados
8. ✅ Definir USER não-root quando possível

### CI/CD

1. ✅ Testar antes de fazer push
2. ✅ Usar cache para builds mais rápidos
3. ✅ Build multi-platform (amd64 + arm64)
4. ✅ Usar metadata-action para tags consistentes
5. ✅ Atualizar README do Docker Hub automaticamente
6. ✅ Executar scan de vulnerabilidades

### Versionamento

1. ✅ Seguir Semantic Versioning
2. ✅ Manter tag `latest` atualizada
3. ✅ Oferecer tags por major version (`:4`)
4. ✅ Documentar breaking changes
5. ✅ Usar CHANGELOG.md

---

## 🛠️ Ferramentas Úteis

| Ferramenta | Propósito |
|------------|-----------|
| `docker buildx` | Builds avançados e multi-platform |
| `docker scout` | Análise de vulnerabilidades |
| `dive` | Análise de layers da imagem |
| `hadolint` | Linter para Dockerfile |
| `trivy` | Scanner de segurança |

---

## 📈 Métricas e Monitoramento

O Docker Hub fornece:

- **Pull count** - Total de downloads
- **Star count** - Popularidade
- **Last pushed** - Última atualização
- **Vulnerability report** - Problemas de segurança (planos pagos)

---

## 🔗 Referências Adicionais

- [Docker Official Images Program](https://docs.docker.com/docker-hub/official_images/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [GitHub Actions Marketplace - Docker](https://github.com/marketplace?type=actions&query=docker)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [OCI Image Format Specification](https://github.com/opencontainers/image-spec)

---

## 📝 Conclusão

A publicação profissional no Docker Hub requer:

1. **Dockerfile otimizado** com labels e healthcheck
2. **CI/CD automatizado** via GitHub Actions
3. **Multi-platform builds** para compatibilidade máxima
4. **Versionamento semântico** com tags claras
5. **Documentação** sincronizada com o repositório

Estas práticas garantem que a imagem seja:
- 🔒 Segura
- 📦 Portável (multi-arch)
- 🏷️ Bem versionada
- 📖 Bem documentada
- 🔄 Automaticamente atualizada
