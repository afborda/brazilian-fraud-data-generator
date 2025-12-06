# 🐳 Guia de Publicação no Docker Hub

Este documento contém instruções completas para publicar o **Brazilian Fraud Data Generator** no Docker Hub com versionamento semântico.

## 📋 Pré-requisitos

1. Conta no [Docker Hub](https://hub.docker.com/)
2. Repositório no GitHub (já configurado)
3. Docker Desktop ou Docker Engine instalado localmente

---

## 🔐 Configuração dos Secrets no GitHub

### Passo 1: Criar Token de Acesso no Docker Hub

1. Acesse [Docker Hub Security Settings](https://hub.docker.com/settings/security)
2. Clique em **New Access Token**
3. Defina um nome descritivo: `github-actions-brazilian-fraud`
4. Selecione permissões: **Read, Write, Delete**
5. Copie o token gerado (você só verá uma vez!)

### Passo 2: Adicionar Secrets no GitHub

1. Vá para seu repositório no GitHub
2. Acesse **Settings** → **Secrets and variables** → **Actions**
3. Clique em **New repository secret**
4. Adicione os seguintes secrets:

| Nome | Valor |
|------|-------|
| `DOCKERHUB_USERNAME` | `afborda` (seu username) |
| `DOCKERHUB_TOKEN` | O token criado acima |

---

## 🏷️ Estratégia de Versionamento

Usamos **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`

### Formato de Tags

| Tag | Quando Usar |
|-----|-------------|
| `v4.0.0` | Release estável |
| `v4.0.0-beta` | Versão beta para testes |
| `v4.0.0-rc.1` | Release Candidate |
| `v4.1.0-alpha` | Versão alpha (experimental) |

### Tags Docker Geradas Automaticamente

Quando você cria a tag `v4.0.0`, o workflow gera:

```
afborda/brazilian-fraud-data-generator:latest
afborda/brazilian-fraud-data-generator:v4.0.0
afborda/brazilian-fraud-data-generator:4.0.0
afborda/brazilian-fraud-data-generator:4.0
afborda/brazilian-fraud-data-generator:4
afborda/brazilian-fraud-data-generator:sha-abc1234
```

---

## 🚀 Como Publicar uma Nova Versão

### Método 1: Via Git Tag (Recomendado)

```bash
# 1. Certifique-se que está no branch principal
git checkout main

# 2. Atualize o código e faça commit
git add .
git commit -m "feat: nova funcionalidade X"

# 3. Crie uma tag com a versão
git tag -a v4.0.0 -m "Release v4.0.0 - Descrição das mudanças"

# 4. Push do código e da tag
git push origin main
git push origin v4.0.0
```

### Método 2: Via GitHub Releases (Interface Web)

1. Vá para **Releases** no seu repositório
2. Clique em **Draft a new release**
3. Em **Choose a tag**, digite `v4.0.0` e selecione "Create new tag on publish"
4. Preencha o título e descrição
5. Clique em **Publish release**

O GitHub Actions será acionado automaticamente!

---

## 🔧 Build e Push Manual (Local)

Se precisar fazer build manualmente:

### Build Single-Platform

```bash
# Build apenas para sua arquitetura
docker build -t afborda/brazilian-fraud-data-generator:v4.0.0 \
  --build-arg VERSION=4.0.0 \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  .

# Push
docker push afborda/brazilian-fraud-data-generator:v4.0.0
```

### Build Multi-Platform

```bash
# Criar builder multi-platform (uma vez)
docker buildx create --name multiplatform --use

# Build e push para múltiplas arquiteturas
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag afborda/brazilian-fraud-data-generator:v4.0.0 \
  --tag afborda/brazilian-fraud-data-generator:latest \
  --build-arg VERSION=4.0.0 \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --push \
  .
```

---

## 📦 Estrutura de Tags no Docker Hub

Após a publicação, os usuários podem usar:

```bash
# Sempre a última versão estável
docker pull afborda/brazilian-fraud-data-generator:latest

# Versão específica
docker pull afborda/brazilian-fraud-data-generator:v4.0.0

# Major version (auto-update minor/patch)
docker pull afborda/brazilian-fraud-data-generator:4
```

---

## ✅ Checklist de Publicação

Antes de criar uma nova release:

- [ ] Código testado e funcionando
- [ ] README.md atualizado
- [ ] CHANGELOG.md atualizado com mudanças
- [ ] Versão no Dockerfile atualizada (opcional, ARG cuida disso)
- [ ] Dependências em requirements.txt atualizadas
- [ ] Nenhum arquivo sensível no repositório

---

## 🔍 Verificando a Publicação

### No Docker Hub

1. Acesse https://hub.docker.com/r/afborda/brazilian-fraud-data-generator
2. Verifique a aba **Tags** para ver todas as versões
3. Confira se o README foi sincronizado

### Testando a Imagem Publicada

```bash
# Pull da imagem
docker pull afborda/brazilian-fraud-data-generator:latest

# Verificar labels
docker inspect afborda/brazilian-fraud-data-generator:latest --format '{{json .Config.Labels}}' | jq

# Testar execução
docker run --rm afborda/brazilian-fraud-data-generator:latest generate.py --help

# Gerar dados de teste
docker run --rm -v $(pwd)/output:/output \
  afborda/brazilian-fraud-data-generator:latest \
  generate.py --num-transactions 1000 --num-customers 100
```

---

## 🐛 Troubleshooting

### Build falha no GitHub Actions

1. Verifique os logs em **Actions** → **Workflow runs**
2. Confirme que os secrets estão configurados
3. Verifique se o token do Docker Hub não expirou

### Imagem não aparece no Docker Hub

1. Aguarde alguns minutos (propagação)
2. Verifique se o workflow completou com sucesso
3. Confirme que não foi um pull request (PRs não fazem push)

### Multi-platform build falha localmente

```bash
# Instale QEMU para emulação
docker run --privileged --rm tonistiigi/binfmt --install all

# Recrie o builder
docker buildx rm multiplatform
docker buildx create --name multiplatform --use
docker buildx inspect --bootstrap
```

---

## 📚 Recursos Adicionais

- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [GitHub Actions for Docker](https://docs.docker.com/build/ci/github-actions/)
- [Semantic Versioning](https://semver.org/)
- [OCI Image Spec](https://github.com/opencontainers/image-spec)
