# Pipeline CI/CD Multi-Ambiente

Pipeline CI/CD única para deploy em múltiplos ambientes (dev, staging, prod) usando GitHub Actions, Terraform e AWS ECS.

## Como Funciona

A pipeline executa 3 jobs principais:

1. **validate**: Valida o código Terraform
2. **build**: Constrói e publica a imagem Docker no ECR
3. **deploy-{env}**: Faz deploy no ambiente escolhido

### Fluxo de Deploy

```
Push/Tag → Validate → Build → Deploy
                              ↓
                    Sincroniza variáveis (GitHub → AWS SSM)
                              ↓
                    Terraform apply/destroy
                              ↓
                    Atualiza serviço ECS
                              ↓
                    Notificação WhatsApp
```

### Controle de Concorrência

A pipeline usa `concurrency.group: deploy-all-environments` para garantir que apenas um deploy execute por vez, evitando sobreposição.

## Estrutura do Código

### `.github/workflows/deploy.yml`
Define a pipeline GitHub Actions com jobs para validação, build e deploy. Usa apenas 3 variáveis globais: `ENVIRONMENT`, `AWS_REGION`, `TERRAFORM_ACTION`.

### `terraform/main.tf`
Cria a infraestrutura AWS:
- ECS Cluster e Service (Fargate)
- Application Load Balancer (ALB)
- Security Groups
- IAM Roles
- CloudWatch Logs

### `scripts/sync_variables.py`
Sincroniza variáveis do GitHub Secrets para AWS SSM Parameter Store. Lê variáveis com prefixo `{ENV}_` e cria/atualiza parâmetros no SSM.

### `scripts/deploy_ecs.py`
Atualiza a task definition do ECS com nova imagem Docker e força novo deployment. Aguarda o deployment completar antes de finalizar.

### `scripts/notify_whatsapp.py`
Envia notificações via WhatsApp usando Twilio quando o deploy falha ou tem sucesso.

## Configuração

### Secrets do GitHub (obrigatórias)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM`
- `TWILIO_WHATSAPP_TO`
- `ECR_REPOSITORY_NAME`

### Secrets por Ambiente (opcional)
- `DEV_DATABASE_URL`, `DEV_API_KEY`, etc.
- `STAGING_DATABASE_URL`, `STAGING_API_KEY`, etc.
- `PROD_DATABASE_URL`, `PROD_API_KEY`, etc.

## Uso

### Deploy Automático
- Push para `develop` → Deploy DEV
- Push para `main` → Deploy STAGING
- Tag `v*` → Deploy PROD

### Deploy Manual
1. Actions → Deploy Multi-Ambiente → Run workflow
2. Escolha: Environment, Terraform Action (apply/destroy), AWS Region
3. Execute

A URL do ALB será exibida nos logs após o deploy.
