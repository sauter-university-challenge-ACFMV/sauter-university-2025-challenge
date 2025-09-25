# Guia de Uso da Arquitetura IaC – Sauter University 2025

> Infra em Terraform + Google Cloud com CI/CD via GitHub Actions (WIF). Este guia é para qualquer pessoa do time conseguir **entender, executar e evoluir** a fundação sem surpresas.

---

## 1) Visão geral

* **Projeto GCP:** `sauter-university-challenger`
* **Região:** `southamerica-east1`
* **IaC:** Terraform modular, com ambientes `dev` e (futuro) `prod`, backend em GCS.
* **CI/CD:** GitHub Actions autenticando por **Workload Identity Federation (WIF)** para a **Service Account do Terraform**.
* **Padrões entregues**:

  * Artifact Registry (`apps`)
  * Cloud Run base (`baseline-api`) com invoker público
  * Cloud Storage: buckets `raw/trusted/processed` (versionamento + UBLA)
  * BigQuery: datasets `bronze/silver/gold`
  * Monitoring: canal de e‑mail (Google Group) **VERIFIED**, política de teste removida
  * Budget: **BRL 300** com thresholds 50/90/100, apontando para o canal

---

## 2) Estrutura do repositório

```
src/
  infra/
    envs/
      dev/
        backend.hcl         # backend remoto (GCS)
        dev.auto.tfvars     # valores do ambiente (ex.: budget)
        main.tf             # composição dos módulos
        providers.tf        # provider google/google-beta
        variables.tf        # variáveis do env
      prod/                 # (a criar) cópia do dev com ajustes
    modules/
      artifact_registry/
      bigquery/
      cloud_run/
      cloud_storage/
      iam/
      monitoring/
      budget/
      wif/
.github/workflows/
  iac-dev.yaml             # CI: plan no PR; apply no push para main
```

**Importante**: não versionamos `.terraform/` nem state local. O `terraform.lock.hcl` **é versionado**.

---

## 3) Pré‑requisitos de acesso

### 3.1 Projeto

* Para **desenvolver/aplicar** via CI, já existe a SA: `terraform-deployer@sauter-university-challenger.iam.gserviceaccount.com` com papéis mínimos no projeto (Storage, Run, BQ, Artifact Registry etc.).
* Para **rodar local** (opcional), use `gcloud auth application-default login` e tenha, no mínimo, permissões equivalentes aos recursos que pretende criar/alterar.

### 3.2 Billing

* **Budgets** exigem permissão na **Billing Account**. Já concedemos `roles/billing.costsManager` para a SA do Terraform e para o owner do setup.
* Para quem for **criar/alterar budgets localmente**, peça este papel na billing account `012AA0-0BFB09-AC0D0F`.

---

## 4) CI/CD com WIF (GitHub Actions)

### 4.1 Secrets no repositório

Em **Settings → Secrets and variables → Actions**:

* `GCP_WIF_PROVIDER` → ex: `projects/944848021706/locations/global/workloadIdentityPools/github/providers/github`
* `GCP_TERRAFORM_SA` → `terraform-deployer@sauter-university-challenger.iam.gserviceaccount.com`

### 4.2 Workflow principal (`.github/workflows/iac-dev.yaml`)

* **Dispara em**: PRs e push na `main` com mudanças em `src/infra/**`.
* **Passos**: checkout → auth via WIF → init (GCS backend) → validate → plan (PR) → apply (somente em push para `main`).

**Fluxo esperado**

1. Crie branch feature (`feat/…`).
2. Abra **PR**. O CI roda **plan** e mostra o diff de infra.
3. Mergiou na `main` → o CI roda **apply**.

---

## 5) Executando localmente (opcional)

> Ideal para testar `validate/plan` ou investigar erros antes do PR.

```bash
cd src/infra/envs/dev
terraform init -backend-config=backend.hcl
terraform validate
terraform plan
# aplicar local? somente quando necessário
terraform apply
```

**Notas**

* Para recursos de **Budget** via user creds: defina quota project

  ```bash
  gcloud auth application-default set-quota-project sauter-university-challenger
  ```
* Providers do env incluem `user_project_override = true` e `billing_project = var.project_id` para evitar 403 da Budget API.

---

## 6) Módulos entregues (como usar/estender)

### 6.1 IAM (`modules/iam`)

* Cria as SAs básicas (terraform, runtime) e papéis de projeto.
* Para adicionar/remover papéis da SA do Terraform, ajuste o `for_each` de roles no módulo e aplique via PR.

### 6.2 WIF (`modules/wif`)

* Pool + Provider para OIDC do GitHub e binding `iam.workloadIdentityUser` na SA do Terraform.
* Para adicionar outro repositório, acrescente o repo no `attribute.repository` na binding (ou crie uma nova binding) e rode apply.

### 6.3 Artifact Registry (`modules/artifact_registry`)

* Repositório DOCKER `apps` na região.
* Push de imagens via Cloud Build/GitHub Actions é o próximo passo natural.

### 6.4 Cloud Run (`modules/cloud_run`)

* Serviço `baseline-api` com invocador `allUsers` (HTTP público), rodando imagem pública de hello world.
* Para **deployar sua imagem**: ajuste `containers.image` e rode apply.

### 6.5 Cloud Storage (`modules/cloud_storage`)

* Cria buckets `raw/trusted/processed` com versionamento e UBLA.
* Naming: `sauter-university-challenger-<env>-<layer>`

### 6.6 BigQuery (`modules/bigquery`)

* Datasets criados: `bronze`, `silver`, `gold`.
* Tabelas e rotinas de transformação ficam em módulos/pipelines de dados (futuro).

### 6.7 Monitoring (`modules/monitoring`)

* Canal de e‑mail (Google Group) criado e **verificado**.
* Para novos canais: criar no módulo e **verificar** via API (sendVerificationCode + verify).

### 6.8 Monitoring (`modules/logging`)

### 6.9 Budget (`modules/budget`)

* Budget **BRL 300** para o projeto, thresholds 50/90/100, notifica o canal de e‑mail.
* Para alterar valor/moeda/thresholds, edite a chamada do módulo no env.

---

## 7) Ambientes

### 7.1 `dev`

* Já configurado. Backend GCS em `gs://sauter-university-challenger-tf-state/terraform/dev`.

### 7.2 `prod` (como criar)

1. Copie `src/infra/envs/dev → prod`.
2. Ajuste `backend.hcl` (`prefix = "terraform/prod"`).
3. Crie `prod.auto.tfvars` (orçamento, e‑mail de alertas, etc.).
4. Revise papéis da SA (talvez mais restritos em prod).
5. Configure um **workflow iac-prod.yaml** (iguais passos, branch de release).

---

## 8) Troubleshooting (erros comuns enfrentados)

* **`cloudresourcemanager.googleapis.com` desabilitado** → habilitar API do projeto antes de ler dados do projeto.
* **403 em `setIamPolicy`/`run.invoker`** → SA sem papel necessário (ex.: `roles/run.developer` ou `roles/run.admin` para operações específicas).
* **Budget 400 `invalid argument`** → moeda do budget ≠ moeda da billing account **ou** projeto não vinculado à billing account **ou** billing **closed**.
* **Budget 403 com user creds** → faltou `set-quota-project` ou provider sem `user_project_override`.
* **WIF 400 atributo/condição** → claims do OIDC não batem com a condition do provider (checar `assertion.repository`, `ref`, `workflow`).
* **Git push bloqueado (>100MB)** → nunca commitar `.terraform/` nem providers; use `.gitignore` correto.

---

## 9) Comandos úteis

```bash
# Estado no backend
cd src/infra/envs/dev
terraform workspace show
terraform state list

# Url do Cloud Run
terraform output -raw cloud_run_url

# Canal de e-mail do Monitoring
gcloud beta monitoring channels list \
  --project sauter-university-challenger \
  --format='table(name,type,labels.email_address,verification_status)'
```

---

## 10) Referências (docs oficiais)

```
Terraform
- https://developer.hashicorp.com/terraform/language
- https://developer.hashicorp.com/terraform/language/settings/backends/gcs
- https://registry.terraform.io/providers/hashicorp/google/latest/docs

Google Cloud
- Workload Identity Federation + GitHub Actions: https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
- Artifact Registry (Docker): https://cloud.google.com/artifact-registry/docs/docker
- Cloud Run: https://cloud.google.com/run/docs
- Cloud Storage (security & versioning): https://cloud.google.com/storage/docs
- BigQuery datasets: https://cloud.google.com/bigquery/docs/datasets
- Monitoring channels (verify): https://cloud.google.com/monitoring/support/notification-options#verify
- Monitoring API sendVerificationCode/verify: https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.notificationChannels/sendVerificationCode
- Budgets (Billing): https://cloud.google.com/billing/docs/how-to/budgets
```

---
*Atualizado por: Adenilson e Clauderson (IaC & Governança).*
