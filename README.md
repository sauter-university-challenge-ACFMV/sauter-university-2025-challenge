# Sauter Challenger — Plataforma de Dados e ML/Agentes na Google Cloud

> Monorepo para a solução do desafio Sauter: ingestão dos dados de ENA (ONS), exposição via API REST em Python, visualização analítica e, a critério do time, **Trilho A (Modelo Preditivo)** ou **Trilho B (Multi‑Agente com RAG)**. Infraestrutura como código em Terraform, deploy em Cloud Run, observabilidade, FinOps e CI/CD com Workload Identity Federation (WIF).

---

## Objetivos do projeto

1. **Implementar a arquitetura** proposta (GCP) com boas práticas de engenharia de dados e software.  
2. **Ingestão** dos dados da ONS (ENA/Reservatórios): `https://dados.ons.org.br/dataset/ear-diario-por-reservatorio`.  
3. **API REST (Python)** para servir dados por **data específica** e **intervalo histórico**.  
4. Escolher um dos trilhos e entregar:
   - **A. Modelo preditivo** do volume de água (ENA) com acurácia mínima de **70%**, versionamento e serving em Cloud Run; ou
   - **B. Multi‑Agente (ADK + Gemini)** com **RAG**: orquestrador + agente ENA + agente Sauter (conteúdo do site `https://sauter.digital`), com respostas “Lúcidas” e citações.
5. **Dashboard analítico** (Looker Studio) justificando a escolha de gráficos.
6. **FinOps**: Budget **R$ 300** com alertas (mentores + equipe).
7. **Qualidade**: testes unitários e de integração **≥ 85%** de cobertura; documentação e docstrings; CI/CD com canário/rollback.

---

## Stack técnica

- **Infra**: Terraform, Workload Identity Federation, Artifact Registry, Cloud Run, Cloud Storage, BigQuery, Cloud Monitoring/Logging, Budget & Alerts.  
- **Aplicação**: Python 3.11+, FastAPI, Uvicorn, Pydantic, pytest/coverage, ruff, mypy.  
- **Dados**: ingestão ONS (requests/httpx), GCS (parquet/csv), BigQuery (tabelas externas, Trusted/Processed, views), DQ.  
- **ML (Trilho A)**: BigQuery para features, Prophet/ARIMA/XGBoost, versão e serving.  
- **Agentes (Trilho B)**: ADK + Gemini, RAG com índice em BQ/GCS, orquestração de agentes.  
- **BI**: Looker Studio.

---

## Estrutura do repositório

```text
/
├── .github/workflows/       # CI/CD pipeline (ci.yml configurado)
├── docs/img                  # ADRs, arquitetura, API spec, justificativa de gráficos
├── src/
│   ├── api/                 # API em desenvolvimento + arquivos temporários CI
│   │   ├── main.py          # Arquivo principal (a ser implementado pela equipe)
│   │   ├── requirements.txt # Dependências Python + ferramentas de qualidade
│   │   └── tests/           # Testes temporários para pipeline CI
│   └── infra/
│       ├── envs/{dev,hml,prod}/
│       └── modules/{bq,cloudrun,artifact,budget,iam,gcs,monitoring,logging}/
│
├── data/
│   ├── ingest/              # Ingestão ONS por data (--date) e histórico
│   ├── modeling/            # Trusted/Processed (DDL, views), partições e clustering
│   └── quality/             # Regras DQ, relatórios e tabelas de violações
├── ml/
│   ├── specs/               # Métricas, contratos de features, referência do target
│   ├── training/            # Notebooks/pipelines de treino e validação
│   └── serving/             # Empacotamento de artefatos e load do modelo
├── dashboards/              # Definições/descrições Looker Studio
├── runbooks/                # Operação: SLOs, incidentes, rollback, custo
├── Dockerfile               # Containerização da API (temporário na raiz)
└── pyproject.toml           # Configurações globais (ruff, mypy, pytest)
```

### Por que esta estrutura?
- **Serviços desacoplados**: `services/api` e `services/predictor` são deploys independentes (menos conflito de PR e rollback cirúrgico).  
- **Infra como 1a classe**: `gcs`, `monitoring` e `logging` são módulos explícitos (observabilidade e custo não são “efeitos colaterais”).  
- **Dados em camadas**: separação entre ingestão, modelagem e qualidade; BQ fica limpo e auditável.  
- **Documentação central**: `/docs` concentra ADRs e specs; `/runbooks` cobre operação.  
- **CI/CD versionado**: Workflows na raiz com WIF; sem credenciais estáticas.

---

## Fluxo de alto nível

1. **Ingestão** baixa arquivos da ONS por data (`--date=YYYY-MM-DD`) e escreve em **GCS** particionado: `gs://.../ena/ano=YYYY/mes=MM/dia=DD/*.parquet`.  
2. **BigQuery** lê via **tabelas externas** e popula **Trusted/Processed**, com regras de **Data Quality** (valores negativos, datas futuras, duplicidades).  
3. **API REST** expõe `GET /v1/ena/...` por data e histórico;  
   - **Trilho A**: `GET /v1/predictions/...` serve previsões do modelo versionado;  
   - **Trilho B**: `POST /v1/agents/query` chama o orquestrador (ENA + Sauter/RAG).  
4. **Dashboards** consomem views otimizadas (`vw_*`).  
5. **SRE/FinOps**: Cloud Monitoring/Logging + budget R$300 com alertas.

---

## Endpoints (resumo)

- `GET /healthz` — healthcheck.  
- `GET /metrics` — métricas Prometheus.  
- `GET /v1/ena/reservatorios/{id}/daily?date=YYYY-MM-DD`  
- `GET /v1/ena/reservatorios/{id}/historico?start_date&end_date`  
- **Trilho A**: `GET /v1/predictions/reservatorios/{id}?date=YYYY-MM-DD`  
- **Trilho B**: `POST /v1/agents/query` → `{question}` retorna `{answer, agent_used, citations}`

Documentação completa via **OpenAPI** em `/docs` da API.

---

## Pré‑requisitos

- Python 3.11+  
- Terraform 1.6+ e `gcloud` CLI  
- Conta de faturamento e projeto GCP  
- Permissões para criar Workload Identity Federation (ou suporte de um admin)

---

## Como subir a infraestrutura (Terraform)

1. Configure variáveis e backend remoto em `src/infra/envs/dev`.  
2. Execute:
   ```bash
   cd src/infra/envs/dev
   terraform init
   terraform plan -out plan.tfplan
   terraform apply plan.tfplan
   ```
3. Módulos que serão aplicados: `bq`, `cloudrun`, `artifact`, `budget`, `iam`, `gcs`, `monitoring`, `logging`.  
4. No final, você terá:
   - Projeto com APIs habilitadas;  
   - Repositório no **Artifact Registry**;  
   - Serviços base no **Cloud Run**;  
   - **Budget** R$300 com e‑mails dos mentores;  
   - Buckets GCS e datasets BigQuery prontos.

> **WIF (GitHub Actions):** o módulo `iam` cria pool/provedor e vincula o repositório ao `sa-cicd` para deploy sem chaves.

---


## Como rodar a API usando Docker

Você pode rodar a API facilmente usando Docker e Docker Compose, sem precisar instalar dependências Python localmente.

### 1. Build e start com Docker Compose

No diretório raiz do projeto, execute:

```bash
docker-compose up --build
```

Isso irá:
- Construir a imagem Docker da API (usando o Dockerfile em `src/api/`)
- Subir o container `fastapi_university` na porta 8000
- Mapear o código-fonte local para dentro do container (hot reload/desenvolvimento)

### 2. Acessar a API

Acesse a API em: [http://localhost:8000](http://localhost:8000)

Documentação automática (OpenAPI): [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Parar os containers

Para parar e remover os containers:

```bash
docker-compose down
```

### 4. Variáveis de ambiente (opcional)

Se necessário, defina variáveis de ambiente no serviço `api` do `docker-compose.yml` usando a chave `environment:`.

Exemplo:

```yaml
services:
   api:
      # ...
      environment:
         - BQ_PROJECT=seu-projeto
         - BQ_DATASET=seu-dataset
         - GCS_BUCKET_RAW=seu-bucket
         - API_AUTH_MODE=apikey
```

---

## Como rodar a API localmente (dev)

> ⚠️ Use Python 3.12 ou inferior para desenvolvimento local. Recomenda-se instalar com [pyenv](https://github.com/pyenv/pyenv) ou usar o Python do sistema. Versões superiores podem causar incompatibilidades.

```bash
cd src/api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# API será implementada pela equipe - por enquanto só estrutura para CI
```

Variáveis de ambiente comuns:
```bash
BQ_PROJECT=...
BQ_DATASET=...
GCS_BUCKET_RAW=...
API_AUTH_MODE=iam|apikey
```

### Validação local (antes de fazer PR)
```bash
# Lint e formatação
ruff check src/
ruff format src/

# Type checking  
mypy src/ --config-file=pyproject.toml

# Testes com cobertura
cd src/api && pytest tests/ --cov=. --cov-fail-under=85

# Build Docker
docker build -t university-api .
```

---

## Pipeline CI/CD

### CI - Continuous Integration
- **Lint + formatação:** `ruff` verifica estilo e organiza imports
- **Type checking:** `mypy` valida anotações de tipo  
- **Testes + cobertura:** `pytest` com cobertura mínima de **85%**
- **Docker build:** valida containerização da aplicação

### CD - Continuous Deployment
- **Deploy automático:** Push para `main` → Build → Artifact Registry → Cloud Run
- **Rollback manual:** Actions → "CD - Deploy to Cloud Run" → escolher `rollback` + revisão
- **Versionamento:** `v1234567` baseado no commit SHA
- **Health check:** Verificação automática do endpoint `/health`

### Configurações centralizadas
- **`.github/workflows/ci.yml`**: pipeline de validação em PRs
- **`.github/workflows/cd.yml`**: pipeline de deploy para produção
- **`pyproject.toml`**: configurações de ruff, mypy e pytest  
- **Critério de aceite:** < 10 minutos, todos os checks verdes

---

## Testes e qualidade

- **Unitários e integração mockada** com `pytest` e `pytest-cov` (alvo ≥ **85%**).  
- Lint com **ruff** e type-check com **mypy**.  
- **GitHub Actions** executa: lint → type → testes → build → cobertura → deploy canário.

---

## Observabilidade e FinOps

- **SLO Cloud Run**: p95 < 500 ms; erro < 1%.  
- Dashboards de **Monitoring** para latência, taxa de erro, QPS e custo diário.  
- **Budget** R$300 com thresholds 50/80/100%, e‑mails dos mentores + equipe.  
- Logs estruturados em JSON, rastreio por `trace_id`.

---

## Decisão de trilho (A ou B)

- **A — Modelo preditivo**: baseline (ARIMA/Prophet/XGBoost), features em BQ (lags, sazonalidade), registro de modelo em GCS, endpoint `/v1/predictions`.  
- **B — Multi‑Agente**: índice RAG (corpus do site + ENA histórica), agentes `ena` e `sauter`, orquestrador que roteia por intenção, avaliação com conjunto de perguntas.

> A escolha e a justificativa devem ser registradas em um **ADR** em `/docs/adr/`.

---

## Padrões de contribuição

- **Branching**: trunk‑based, PRs curtos a partir de `feat/<area>-<descricao>`.  
- **Commits**: Conventional Commits.  
- **Proteções**: `main` protegida; PR exige CI verde e cobertura ≥ 85%.

---

## Licença

Definir conforme necessidade do curso/equipe (ex.: MIT).

---

## Autores e contato

Adenilson, Clauderson, Felipe, Mari e Raylandson — Equipe Sauter Challenger.
