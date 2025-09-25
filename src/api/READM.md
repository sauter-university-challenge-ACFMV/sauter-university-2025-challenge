# 📘 Documentação API de Ingestão de Dados ONS

## 1. Visão Geral e Arquitetura

Esta API foi projetada para atuar como um serviço de ingestão de dados, buscando, processando e armazenando de forma padronizada os datasets públicos do Operador Nacional do Sistema Elétrico (ONS). A arquitetura é modular e segue o princípio de separação de responsabilidades, dividida nas seguintes camadas:

* **Roteamento (Routers)**: Responsável por expor os endpoints da API, receber as requisições e invocar a camada de serviço. Utiliza o FastAPI.
* **Serviço (Services)**: Contém a lógica de negócio principal, orquestrando o fluxo de busca, processamento e armazenamento dos dados.
* **Repositório (Repositories)**: Abstrai o acesso a fontes de dados externas, como o Google Cloud Storage (GCS) e o BigQuery.

O projeto é conteinerizado com Docker, utiliza o `uv` para gerenciamento de pacotes e é configurado via variáveis de ambiente.

## 2. Fluxo de Dados Detalhado

O processo de ingestão, do início ao fim, segue os passos abaixo:

1.  **Requisição**: O cliente envia uma requisição `POST` para um dos endpoints (`/filter-parquet-files` ou `/bulk-ingest-parquet-files`) com um DTO contendo os filtros (ano, pacote, etc.).
2.  **Roteamento**: O `OnsRouter` recebe a requisição, valida o corpo com o Pydantic DTO (`DateFilterDTO`) e chama o método correspondente no `OnsService`.
3.  **Busca de Metadados (Service)**: O `OnsService` constrói a URL da API da ONS e busca os metadados do pacote solicitado para identificar os recursos (arquivos) disponíveis.
4.  **Filtragem e Seleção (Service)**: Os recursos são filtrados por ano e tipo de arquivo, priorizando `parquet`, `csv` e `xlsx`. A lógica seleciona o melhor formato disponível para cada ano dentro do intervalo solicitado.
5.  **Processamento Concorrente (Service)**: Para cada recurso selecionado, uma tarefa de download e processamento é criada e executada de forma concorrente usando `asyncio.gather`.
6.  **Download e Conversão (Service)**:
    * O conteúdo do arquivo é baixado em memória.
    * O `pandas` é utilizado para ler os dados (seja CSV, XLSX ou Parquet) e converter todas as colunas para o tipo `string`, garantindo a consistência do schema.
    * O DataFrame resultante é serializado para um buffer em formato Parquet.
7.  **Verificação de Duplicidade (Repository)**:
    * O `OnsService` extrai a data mais recente do DataFrame.
    * Ele então invoca o método `raw_table_has_value` do `GCSFileRepository`. Este método verifica no BigQuery se um registro com essa data já existe na tabela de destino, evitando o reprocessamento de dados.
8.  **Upload para GCS (Repository)**: Se os dados forem inéditos, o `OnsService` chama o método `save` do `GCSFileRepository`, que faz o upload do buffer Parquet para o bucket no GCS. A estrutura do caminho no GCS é montada de forma a organizar os arquivos por pacote, ano, mês e dia.
9.  **Resposta**: O `OnsService` compila os resultados (sucessos e falhas) em um objeto `ProcessResponse` e o retorna ao `OnsRouter`, que formata a resposta HTTP final para o cliente.

## 3. Camada de Serviço (`OnsService`)

A classe `OnsService` (`api/services/ons_service.py`) é o núcleo da aplicação, orquestrando todo o fluxo de ingestão.

### Principais Métodos

* `process_reservoir_data(filters: DateFilterDTO)`:
    * Recebe um único DTO de filtro.
    * Busca os metadados do pacote na ONS.
    * Filtra os recursos por ano e formato, selecionando a melhor opção para cada ano.
    * Cria e executa tarefas de download (`_download_parquet`) de forma concorrente.
    * Agrega os resultados e retorna um `ProcessResponse` com o resumo da operação.

* `process_reservoir_data_bulk(filters_list: List[DateFilterDTO])`:
    * Recebe uma lista de DTOs de filtro.
    * Cria uma tarefa `process_reservoir_data` para cada DTO da lista.
    * Executa todas as tarefas concorrentemente, permitindo a ingestão em massa de diferentes pacotes ou períodos.

* `_download_parquet(client: httpx.AsyncClient, download_info: DownloadInfo)`:
    * Método auxiliar que executa o fluxo de um único arquivo.
    * **Etapas**:
        1.  Baixa o conteúdo do arquivo da URL (`_fetch_bytes`).
        2.  Lê os dados para um DataFrame pandas (`_read_to_dataframe`).
        3.  Padroniza todas as colunas para string (`_convert_all_columns_to_string`).
        4.  Converte o DataFrame para um buffer em memória no formato Parquet (`_dataframe_to_parquet_buffer`).
        5.  Verifica no BigQuery se o dado já existe, consultando a última data do arquivo.
        6.  Se o dado for novo, faz o upload para o GCS (`_save_to_gcs`).
    * Retorna um `DownloadResult` detalhando o sucesso ou a falha da operação, incluindo mensagens de erro.

## 4. Camada de Repositório (`GCSFileRepository`)

A classe `GCSFileRepository` (`api/repositories/gcs_repository.py`) abstrai toda a interação com os serviços do Google Cloud.

### Autenticação

O método `_create_storage_client` implementa uma cadeia de estratégias de autenticação para se conectar ao GCP, na seguinte ordem de prioridade:

1.  **`GOOGLE_CREDENTIALS_JSON`**: Tenta carregar as credenciais a partir de uma string JSON na variável de ambiente. Ideal para ambientes de CI/CD e deployments conteinerizados (ex: Cloud Run).
2.  **`GOOGLE_APPLICATION_CREDENTIALS`**: Tenta carregar as credenciais a partir do caminho de um arquivo de chave de serviço.
3.  **`GOOGLE_CLOUD_PROJECT`**: Tenta autenticar usando o ID do projeto, contando com as credenciais do ambiente (ex: gcloud CLI local).
4.  **Credenciais Padrão**: Como última tentativa, utiliza as credenciais padrão do ambiente.

Se todos os métodos falharem, uma exceção é levantada com uma mensagem clara sobre como configurar a autenticação.

### Principais Métodos

* `save(file: IO[bytes], filename: str, _bucket_name: str | None)`:
    * Recebe um buffer de bytes e um nome de arquivo.
    * Faz o upload do arquivo para o GCS no bucket especificado (ou no bucket padrão).
    * Retorna a URL pública do objeto no GCS.

* `raw_table_has_value(package_name: str, column_name: str, last_day: str)`:
    * Primeiro, verifica se a tabela de destino existe no BigQuery com o método `_table_exists`.
    * Se a tabela existir, executa uma query `SELECT 1 ... WHERE <coluna_data> = @last_day LIMIT 1`.
    * Retorna `True` se a query retornar alguma linha (o dado já existe) e `False` caso contrário. Isso é crucial para garantir a idempotência do processo de ingestão.

## 5. Modelos de Dados (DTOs)

Os modelos em `api/models/ons_dto.py` usam Pydantic para definir as estruturas de dados e garantir a validação automática.

* **`DateFilterDTO`**: Define o contrato de entrada para os endpoints. Garante que os tipos de dados estejam corretos e permite que campos sejam opcionais.
* **`DownloadInfo`**, **`DownloadResult`**, **`ProcessResponse`**: Modelos internos usados na camada de serviço para estruturar os dados durante o fluxo de processamento, garantindo clareza e consistência entre os métodos.
* **`ApiResponse`**, **`ApiBulkResponse`**: Modelam a estrutura final das respostas JSON enviadas aos clientes, definindo um contrato claro de saída.