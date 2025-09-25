# Guia de ELT no BigQuery – Sauter University 2025

> Este guia explica o processo de Engenharia de Dados ELT (Extract, Load, Transform) usando SQL no BigQuery, seguindo os padrões e organização do repositório. O objetivo é que qualquer pessoa do time consiga **entender, executar e evoluir** os pipelines de dados sem surpresas.

---

## 1) Visão geral

* **Plataforma:** Google BigQuery (BQ)
* **Organização:** SQL modular, com camadas `raw`, `trusted`, `refined` e integração com pipelines automatizados.
* **Processo:**
  * **Extract:** Dados são extraídos de fontes externas e carregados na camada `raw`.
  * **Load:** Carregamento dos dados brutos para o BigQuery, conectados em uma external table via codigo sql (BQ/raw/*.sql) , com o bucket no Cloud storage.
  * **Transform:** Transformações SQL organizadas em camadas, promovendo dados de `raw` → `trusted` → `refined`.


---

## 2) Estrutura do repositório

```
sql/
  BQ/
    daily-call/
      daily-raw-trusted.sql         # Transforma dados brutos em trusted
      daily-trusted-refined.sql     # Refina dados trusted
    procedure/
      procedure-raw-trusted.sql     # Procedures para trusted
      procedure-trusted-refined.sql # Procedures para refined
    query/
      query-refined-view-looker.sql # Views para Looker
      query-refined-view-ml.sql     # Views para ML
    raw/
      raw_reservatorio.sql          # Scripts de carga raw
      raw-ena-diario-por-reservatorio.sql
    refined/
      refined-looker.sql            # Scripts de refined
      refined-ml.sql
    trusted/
      trusted-ena-diario-por-reservatorio.sql # Scripts das trusteds individuais
      trusted-reservatorio.sql
```

- **Camadas:**
  - `raw/`: scripts de ingestão de dados brutos.
  - `trusted/`: scripts de limpeza, validação e padronização.
  - `refined/`: scripts de enriquecimento, agregação e preparação para consumo.
  - `procedure/`: procedures para automação de transformações.
  - `query/`: views e queries para consumo analítico (Looker, ML, etc).

---

## 3) Processo ELT detalhado

### 3.1 Extract & Load (Carga de dados)

- **Objetivo:** Trazer dados de fontes externas para o BigQuery na camada `raw`.
- **Como fazer:**
  - Use scripts SQL em `raw/` para criar tabelas e definir schemas.
  - Carregue dados via:
    - Console do GCP (Upload manual)
- **Exemplo:**
  ```sql
  -- raw/raw_reservatorio.sql
  CREATE OR REPLACE TABLE `projeto.dataset_raw.reservatorio` (...);
  -- Carregue os dados via GCS ou ferramenta de ingestão
  ```
  - Codigos na pasta raw.

### 3.2 Transform (Trusted)

- **Objetivo:** Limpar, validar e padronizar os dados brutos.
- **Como fazer:**
  - Use scripts em `trusted/` e `procedure/` para transformar dados de `raw` para `trusted`.
  - Scripts SQL devem:
    - Remover duplicidades
    - Corrigir tipos e formatos
    - Validar integridade
  - Procedures podem automatizar rotinas recorrentes.
- **Exemplo:**
  ```sql
  -- trusted/trusted-reservatorio.sql
  CREATE OR REPLACE TABLE `projeto.dataset_trusted.reservatorio` AS
  SELECT ... FROM `projeto.dataset_raw.reservatorio` WHERE ...;
  ```
    - Codigos na pasta trusted.

### 3.3 Transform (Refined)

- **Objetivo:** Enriquecer, agregar e preparar dados para consumo analítico.
- **Como fazer:**
  - Use scripts em `refined/`, `query/` e `procedure/` para promover dados de `trusted` para `refined`.
  - Scripts SQL devem:
    - Realizar joins, agregações, cálculos
    - Criar views para Looker/ML
  - Procedures podem automatizar pipelines de transformação.
- **Exemplo:**
  ```sql
  -- refined/refined-looker.sql
  CREATE OR REPLACE MATERIALIZED VIEW `projeto.dataset_refined.looker` AS
  SELECT ... FROM `projeto.dataset_trusted.reservatorio` JOIN ...;
  ```
    - Codigos na pasta refined.
---

## 4) Boas práticas

- **Versionamento:** Scripts SQL versionados no repositório.
- **Nomenclatura:** Use nomes claros para tabelas e datasets (`raw`, `trusted`, `refined`).
- **Reprodutibilidade:** Scripts devem ser idempotentes (podem ser rodados múltiplas vezes sem erro).
- **Automação:** Sempre que possível, use procedures e pipelines automatizados.

---

## 5) Troubleshooting (erros comuns)

- **Permissões:** Verifique se você tem permissão de escrita/leitura nos datasets.
- **Quota:** Atenção aos limites de processamento do BQ.
- **Schemas:** Mantenha schemas sincronizados entre camadas.
- **Dados faltantes:** Sempre valide a integridade após cada etapa.

---

*Atualizado por: Clauderson Branco Xavier 2025.*
