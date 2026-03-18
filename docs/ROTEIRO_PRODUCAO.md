# Roteiro de Produção — SynthFin
## Passo a passo completo: código pronto → API em produção

> **Estado atual**: código v4.8 completo, workflows CI/CD criados, infra automatizada.  
> O que falta é executar as etapas abaixo **uma vez** para colocar tudo no ar.

---

## Mapa de repos

| Repo GitHub | Conteúdo | Workflow |
|-------------|----------|-----------|
| `synthfin-core` (público) | Open source lib (`brazilian-fraud-data-generator`) | `docker-publish.yml` — Docker Hub público |
| `synthfin-api` (privado) | API FastAPI + Celery Worker | `deploy-product.yml` — build GHCR → VPS |
| `synthfin-web` (privado) | Landing page | `deploy-site.yml` — build GHCR → VPS |
| **`synthfin-infra`** (privado, **criar**) | VPS configs (traefik, segurança, DB) | `deploy-infra.yml` — apply configs VPS |
| `synthfin-saas` (privado) | Produto pago (billing, stripe, etc.) | — |

---

## Pré-requisitos

- [ ] Acesso ao painel OVH (VPS Value 4vCPU / 8GB — Ubuntu 24.04 LTS)
- [ ] Domínio `synthfin.com.br` — registros DNS editáveis
- [ ] Conta Docker Hub (já existe: `afborda`)
- [ ] Stripe conta ativa (para billing)

---

## FASE 1 — Adicionar workflows nos repos corretos

Os workflows do produto ficam em cada repo de produto, **não** no `synthfin-core`.

### 1.1 — `deploy-product.yml` → repo `synthfin-api`

```bash
cd ~/projetos/pessoal/synthfin-api   # ajustar path se necessário
mkdir -p .github/workflows
```

Criar `.github/workflows/deploy-product.yml`:

```yaml
name: Deploy Product (API + Worker)
on:
  push:
    branches: [main]
    paths: ['src/**', 'api/**', 'requirements*.txt', 'Dockerfile']
  workflow_dispatch:
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: afborda/synthfin-api
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12', cache: 'pip' }
      - run: pip install -r requirements.txt -r requirements-api.txt
      - run: pytest tests/ -q --tb=short
  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/setup-buildx-action@v3
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=raw,value=latest,enable={{is_default_branch}}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          port: ${{ secrets.VPS_SSH_PORT }}
          script: |
            set -euo pipefail
            cd /opt/synthfin/services
            echo "${{ secrets.GHCR_TOKEN }}" | docker login ghcr.io -u afborda --password-stdin
            docker compose pull api worker
            docker compose up -d --no-deps api worker beat
            docker image prune -af --filter "until=24h"
            sleep 8 && curl -sf http://localhost:8000/health || exit 1
            echo "✅ Deploy $(date '+%Y-%m-%d %H:%M:%S')"
```

### 1.2 — `deploy-site.yml` → repo `synthfin-web`

```bash
cd ~/projetos/pessoal/synthfin-web
mkdir -p .github/workflows
```

Criar `.github/workflows/deploy-site.yml`:

```yaml
name: Deploy Site (synthfin.com.br)
on:
  push:
    branches: [main]
  workflow_dispatch:
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: afborda/synthfin-web
jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/setup-buildx-action@v3
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=raw,value=latest,enable={{is_default_branch}}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          port: ${{ secrets.VPS_SSH_PORT }}
          script: |
            set -euo pipefail
            cd /opt/synthfin/site
            echo "${{ secrets.GHCR_TOKEN }}" | docker login ghcr.io -u afborda --password-stdin
            docker compose pull && docker compose up -d --no-deps site
            docker image prune -af --filter "until=24h"
            sleep 3 && curl -sf http://localhost:3000 || exit 1
            echo "✅ Site $(date '+%Y-%m-%d %H:%M:%S')"
```

### 1.3 Commitar e push em cada repo

```bash
# No synthfin-api:
git add .github/workflows/deploy-product.yml
git commit -m "ci: add deploy-product workflow"
git push origin main

# No synthfin-web:
git add .github/workflows/deploy-site.yml
git commit -m "ci: add deploy-site workflow"
git push origin main
```

> ⚠️ Os workflows vão falhar enquanto os secrets não estiverem configurados. Isso é esperado.

---

## FASE 2 — Popular o repo `synthfin-infra` (já existe no GitHub)

> Repo já criado em: [github.com/afborda/synthfin-infra](https://github.com/afborda/synthfin-infra)  
> Conteúdo local gerado em: `~/projetos/pessoal/brazildata-infra/`

### 2.1 Atualizar domínio e nomes nos arquivos de config

```bash
cd ~/projetos/pessoal/brazildata-infra

# Trocar synthlab.io → synthfin.com.br
grep -rl "synthlab\.io" . | xargs sed -i 's/synthlab\.io/synthfin.com.br/g'

# Trocar brazildata → synthfin (user VPS, paths, nomes de containers)
grep -rl "brazildata" . | xargs sed -i 's/brazildata/synthfin/g'
```

### 2.2 Inicializar git e conectar ao repo remoto

```bash
git init
git add .
git commit -m "feat: setup inicial VPS OVH — security/traefik/services/monitoring/backup"

git remote add origin git@github.com:afborda/synthfin-infra.git
git branch -M main
git push -u origin main
```

### 2.3 Adicionar o `deploy-infra.yml` no repo

```bash
mkdir -p .github/workflows
```

Criar `.github/workflows/deploy-infra.yml`:

```yaml
name: Deploy Infra (configs/security)
on:
  push:
    branches: [main]
    paths:
      - 'security/**'
      - 'traefik/**'
      - 'services/**'
      - 'monitoring/**'
      - 'backup/**'
  workflow_dispatch:
    inputs:
      component:
        description: 'Component (all, traefik, services, monitoring)'
        required: false
        default: 'all'
        type: choice
        options: [all, traefik, services, monitoring]
concurrency:
  group: infra-deploy
  cancel-in-progress: false
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          port: ${{ secrets.VPS_SSH_PORT }}
          script: |
            set -euo pipefail
            cd /opt/synthfin-infra
            git pull origin main
            COMPONENT="${{ github.event.inputs.component || 'all' }}"
            [[ "$COMPONENT" == "all" || "$COMPONENT" == "traefik" ]] && \
              docker compose -f traefik/docker-compose.traefik.yml up -d
            [[ "$COMPONENT" == "all" || "$COMPONENT" == "services" ]] && \
              docker compose -f services/docker-compose.services.yml up -d
            [[ "$COMPONENT" == "all" || "$COMPONENT" == "monitoring" ]] && \
              docker compose -f monitoring/docker-compose.monitoring.yml up -d
            [[ "$COMPONENT" == "all" ]] && \
              sudo systemctl reload fail2ban 2>/dev/null || true
            bash security/audit-security.sh
            echo "✅ Infra deploy $(date '+%Y-%m-%d %H:%M:%S')"
```

```bash
git add .github/workflows/deploy-infra.yml
git commit -m "ci: add deploy-infra workflow"
git push origin main
```

---

## FASE 3 — Criar chave SSH dedicada para CI/CD

> Nunca usar a chave pessoal nos secrets do CI.

```bash
# Na sua máquina local
ssh-keygen -t ed25519 -C "synthfin-cicd" -f ~/.ssh/id_ed25519_synthfin -N ""

# Chave pública — será copiada para a VPS (FASE 5)
cat ~/.ssh/id_ed25519_synthfin.pub

# Chave privada — será o valor do secret VPS_SSH_KEY
cat ~/.ssh/id_ed25519_synthfin
```

---

## FASE 4 — Configurar secrets no GitHub

Adicionar em cada repo: **Settings → Secrets and variables → Actions → New repository secret**

### Secrets necessários por repo

| Secret | `synthfin-api` | `synthfin-web` | `synthfin-infra` |
|--------|:-:|:-:|:-:|
| `VPS_HOST` | ✅ | ✅ | ✅ |
| `VPS_USER` | ✅ | ✅ | ✅ |
| `VPS_SSH_KEY` | ✅ | ✅ | ✅ |
| `VPS_SSH_PORT` | ✅ | ✅ | ✅ |
| `GHCR_TOKEN` | ✅ | ✅ | ✅ |
| `DOCKERHUB_USERNAME` | ✅ | — | — |
| `DOCKERHUB_TOKEN` | ✅ | — | — |

### Valores

| Secret | Valor |
|--------|-------|
| `VPS_HOST` | IP do painel OVH → VPS → IPv4 |
| `VPS_USER` | `synthfin` (criado pelo `setup.sh`) |
| `VPS_SSH_KEY` | conteúdo da chave privada: `cat ~/.ssh/id_ed25519_synthfin` |
| `VPS_SSH_PORT` | `2222` |
| `GHCR_TOKEN` | Personal Access Token — ver abaixo |
| `DOCKERHUB_USERNAME` | `afborda` |
| `DOCKERHUB_TOKEN` | token Docker Hub — ver abaixo |

### Criar GHCR_TOKEN

1. GitHub → **Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. **Generate new token (classic)**
3. Permissões: `write:packages`, `read:packages`
4. Expiração: 1 ano
5. Copiar e salvar como secret `GHCR_TOKEN` nos 3 repos

### Criar DOCKERHUB_TOKEN

1. [hub.docker.com](https://hub.docker.com) → Account Settings → **Security → New Access Token**
2. Nome: `synthfin-ci`
3. Permissões: Read & Write
4. Salvar como `DOCKERHUB_TOKEN` (só no `synthfin-api`)

---

---

## FASE 5 — Provisionar a VPS (setup inicial)

> Executar **uma única vez** na VPS virgem.

### 5.1 Acessar a VPS inicial (ainda como root na porta 22)

```bash
ssh root@<IP_DA_VPS>
```

### 5.2 Adicionar a chave SSH do CI à VPS

```bash
# Na VPS, como root
mkdir -p ~/.ssh
echo "ssh-ed25519 AAAA... synthfin-cicd" >> ~/.ssh/authorized_keys
# (colar o conteúdo de ~/.ssh/id_ed25519_synthfin.pub da sua máquina)
```

### 5.3 Criar o arquivo .env na VPS

```bash
git clone https://github.com/afborda/synthfin-infra.git /opt/synthfin-infra
cd /opt/synthfin-infra
cp .env.example .env
nano .env
```

**Preencher no `.env`:**

```env
DOMAIN=synthfin.com.br
EMAIL=seu-email@synthfin.com.br
POSTGRES_PASSWORD=<senha forte — mín 32 chars>
REDIS_PASSWORD=<outra senha forte>
MINIO_ROOT_PASSWORD=<outra senha forte>
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
API_SECRET_KEY=<jwt secret mín 32 chars>
GHCR_TOKEN=ghp_...
SSH_PORT=2222
ADMIN_SSH_KEY="ssh-ed25519 AAAA... synthfin-cicd"
```

### 5.4 Rodar o setup automatizado

```bash
bash /opt/synthfin-infra/setup.sh
```

O script instala e configura automaticamente:
1. Hardening do OS (usuário `synthfin`, sudo, timezone)
2. SSH na porta 2222 (key-only, sem root login)
3. UFW firewall (deny all → allow 2222/80/443)
4. fail2ban (jails SSH + Traefik + API abuse)
5. Kernel sysctl (SYN cookies, ASLR, anti-spoofing)
6. Auto-updates de segurança
7. Docker CE + Docker Compose
8. Traefik com SSL Let's Encrypt automático
9. PostgreSQL, Redis, MinIO, API, Worker, Beat
10. Landing page (site)
11. Prometheus + Grafana
12. Cron de backup diário (4h da manhã)

> ⚠️ **CRITICAL**: Antes de fechar o terminal root, abrir **nova aba** e testar:
> ```bash
> ssh -p 2222 synthfin@<IP_DA_VPS>
> ```
> Se funcionar → pode fechar o root. Se não funcionar → **não feche** e investigue.

---

## FASE 6 — Configurar DNS

No painel do seu registrador (`synthfin.com.br`), adicionar os registros A:

| Tipo | Nome | Valor | TTL |
|------|------|-------|-----|
| `A` | `@` | `<IP_DA_VPS>` | 300 |
| `A` | `api` | `<IP_DA_VPS>` | 300 |
| `A` | `dash` | `<IP_DA_VPS>` | 300 |
| `A` | `minio` | `<IP_DA_VPS>` | 300 |
| `AAAA` | `@` | `<IPV6_DA_VPS>` | 300 |
| `CNAME` | `www` | `synthfin.com.br` | 300 |

Verificar propagação:

```bash
dig api.synthfin.com.br +short
# deve retornar o IP da VPS
```

---

## FASE 7 — Verificar que tudo funciona

### 7.1 Health checks manuais

```bash
curl -sf https://api.synthfin.com.br/health
curl -sf https://synthfin.com.br
# SSL — https://www.ssllabs.com/ssltest/analyze.html?d=synthfin.com.br
```

### 7.2 Audit de segurança

```bash
ssh -p 2222 synthfin@<IP_DA_VPS>
bash /opt/synthfin-infra/security/audit-security.sh
```

Esperado: todos ✅, zero ❌.

### 7.3 Testar pipeline CI/CD de ponta a ponta

```bash
cd ~/projetos/pessoal/synthfin-api
echo "# ci test" >> README.md
git add -A && git commit -m "test: trigger deploy pipeline"
git push origin main
# Acompanhar em github.com/afborda/synthfin-api/actions
```

---

## FASE 8 — Configurar Stripe webhook

1. Stripe Dashboard → **Developers → Webhooks → Add endpoint**
2. URL: `https://api.synthfin.com.br/webhooks/stripe`
3. Eventos: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
4. Copiar o **Signing secret** gerado

```bash
ssh -p 2222 synthfin@<IP_DA_VPS>
nano /opt/synthfin-infra/.env
# atualizar STRIPE_WEBHOOK_SECRET=whsec_...
cd /opt/synthfin/services
docker compose restart api worker beat
```

---

## Checklist final

```
FASE 1 — Workflows
  [ ] deploy-product.yml adicionado ao synthfin-api + push feito
  [ ] deploy-site.yml adicionado ao synthfin-web + push feito

FASE 2 — synthfin-infra
  [x] Repo criado no GitHub (privado) ✅ github.com/afborda/synthfin-infra
  [ ] sed para trocar synthlab.io → synthfin.com.br e brazildata → synthfin
  [ ] git init + remote + push inicial
  [ ] deploy-infra.yml adicionado + push

FASE 3 — Chave SSH
  [ ] id_ed25519_synthfin criada (separada da pessoal)

FASE 4 — Secrets GitHub
  [ ] VPS_HOST, VPS_USER, VPS_SSH_KEY, VPS_SSH_PORT nos 3 repos
  [ ] GHCR_TOKEN nos 3 repos (synthfin-api, synthfin-web, synthfin-infra)
  [ ] DOCKERHUB_USERNAME, DOCKERHUB_TOKEN só no synthfin-api

FASE 5 — VPS
  [ ] Chave SSH CI adicionada ao root da VPS
  [ ] .env preenchido com todas as variáveis
  [ ] setup.sh concluído sem erros
  [ ] SSH porta 2222 testado ANTES de fechar sessão root

FASE 6 — DNS
  [ ] A records para synthfin.com.br e subdomínios (api, dash, minio)
  [ ] Propagação confirmada com: dig api.synthfin.com.br +short

FASE 7 — Validação
  [ ] https://api.synthfin.com.br/health → 200
  [ ] https://synthfin.com.br carrega
  [ ] SSL A+ no SSL Labs
  [ ] audit-security.sh → zero ❌
  [ ] Pipeline CI/CD testado com commit no synthfin-api

FASE 8 — Stripe
  [ ] Webhook configurado para api.synthfin.com.br
  [ ] Signing secret atualizado no .env + API reiniciada
```

---

## Troubleshooting rápido

| Problema | Causa provável | Solução |
|----------|---------------|---------|
| Pipeline falha em "Deploy to VPS" | Secret VPS_SSH_KEY incorreto | Recriar secret com conteúdo exato da chave privada (incluindo `-----BEGIN...-----`) |
| SSL não emite | DNS não propagou ou porta 80 bloqueada | Aguardar DNS, verificar `ufw status` |
| API não responde | Container não subiu | `ssh -p 2222 synthfin@VPS` → `docker logs synthfin-api --tail=50` |
| Pipeline falha em "Run Tests" | Dependência faltando | Verificar `requirements.txt` e `requirements-api.txt` |
| `ghcr.io` pull falha na VPS | GHCR_TOKEN expirado ou sem permissão | Renovar token com `write:packages` |

---

*Arquivos de referência:*  
*— Infra local: `~/projetos/pessoal/synthfin-infra/` (após rename de brazildata-infra)*  
*— Spec CI/CD: `docs/documentodeestudos/SynthLab_CICD_Pipelines.md`*  
*— Spec infra: `docs/documentodeestudos/brazildata-infra-README.md`*
