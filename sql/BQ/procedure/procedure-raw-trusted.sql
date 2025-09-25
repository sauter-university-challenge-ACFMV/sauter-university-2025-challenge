CREATE SCHEMA IF NOT EXISTS `sauter-university-challenger.silver`;

CREATE OR REPLACE PROCEDURE `sauter-university-challenger.procedure.process_bronze_to_silver`()
OPTIONS(strict_mode=false)
BEGIN
        -- Versão melhorada com diagnóstico e filtros mais rigorosos
    -- Versão melhorada com diagnóstico e filtros mais rigorosos
  CREATE OR REPLACE TABLE `sauter-university-challenger.silver.ena-diario-por-reservatorio`
  PARTITION BY data_ingestao AS
  WITH
  -- 1) Período de análise: calcular total de dias desde 2015-01-01
  periodo_analise AS (
    SELECT
      DATE_DIFF(CURRENT_DATE(), DATE('2015-01-01'), DAY) + 1 AS total_dias_esperados
  ),
  -- 2) Contagem de dias válidos por reservatório (apenas dados não-nulos/não-NaN)
  contagem_dias_validos AS (
    SELECT
      LOWER(TRIM(CAST(nom_reservatorio AS STRING))) AS nom_reservatorio,
      COUNT(DISTINCT DATE(CAST(ena_data AS DATETIME))) AS dias_validos,
      MIN(DATE(CAST(ena_data AS DATETIME))) AS primeira_data,
      MAX(DATE(CAST(ena_data AS DATETIME))) AS ultima_data
    FROM
      `sauter-university-challenger.bronze.ena-diario-por-reservatorio`
    WHERE
      EXTRACT(YEAR FROM CAST(ena_data AS DATETIME)) >= 2015
      AND SAFE_CAST(ena_armazenavel_res_mwmed AS FLOAT64) IS NOT NULL
      AND CAST(ena_armazenavel_res_mwmed AS STRING) NOT IN ('NaN', 'nan', 'NAN', '')
      AND TRIM(CAST(ena_armazenavel_res_mwmed AS STRING)) != ''
    GROUP BY 1
  ),
  -- 3) Reservatórios com dados completos (todos os dias desde 2015-01-01)
  reservatorios_completos AS (
    SELECT
      c.nom_reservatorio,
      c.dias_validos,
      c.primeira_data,
      c.ultima_data,
      p.total_dias_esperados,
      (p.total_dias_esperados - c.dias_validos) AS dias_faltantes
    FROM
      contagem_dias_validos c
    CROSS JOIN
      periodo_analise p
    WHERE
      c.primeira_data = DATE('2015-01-01')  -- Deve começar exatamente em 2015-01-01
      AND c.dias_validos >= p.total_dias_esperados * 0.99  -- Permite até 1% de falha (mais flexível)
      -- Para ser mais rigoroso, use: AND c.dias_validos = p.total_dias_esperados
  ),
  -- 4) Tabela final com dados filtrados
  dados_finais AS (
    SELECT
      LOWER(TRIM(CAST(b.nom_reservatorio AS STRING))) AS nom_reservatorio,
      LOWER(TRIM(CAST(b.tip_reservatorio AS STRING))) AS tip_reservatorio,
      LOWER(TRIM(CAST(b.nom_bacia AS STRING))) AS nom_bacia,
      LOWER(TRIM(CAST(b.nom_subsistema AS STRING))) AS nom_subsistema,
      CAST(b.ena_data AS DATETIME) AS ena_data,
      SAFE_CAST(b.ena_armazenavel_res_mwmed AS FLOAT64) AS ena_armazenavel_res_mwmed,
      CURRENT_DATE() AS data_ingestao
    FROM
      `sauter-university-challenger.bronze.ena-diario-por-reservatorio` b
    INNER JOIN
      reservatorios_completos rc ON LOWER(TRIM(CAST(b.nom_reservatorio AS STRING))) = rc.nom_reservatorio
    WHERE
      EXTRACT(YEAR FROM CAST(b.ena_data AS DATETIME)) >= 2015
      AND SAFE_CAST(b.ena_armazenavel_res_mwmed AS FLOAT64) IS NOT NULL
      AND CAST(b.ena_armazenavel_res_mwmed AS STRING) NOT IN ('NaN', 'nan', 'NAN', '')
    ORDER BY
      b.nom_reservatorio ASC,  -- Primeiro: agrupar por reservatório
      b.ena_data ASC  -- Segundo: dentro de cada reservatório, ordem cronológica
  )
  SELECT * FROM dados_finais;


  #Reservatoiros 
  CREATE OR REPLACE TABLE `sauter-university-challenger.silver.reservatorio`
  PARTITION BY data_ingestao AS
  WITH
  dados_ordenados AS (
    SELECT
      LOWER(TRIM(CAST(nom_reservatorio AS STRING))) AS nom_reservatorio,
      LOWER(TRIM(CAST(tip_reservatorio AS STRING))) AS tip_reservatorio,
      LOWER(TRIM(CAST(nom_bacia AS STRING))) AS nom_bacia,
      CAST(dat_entrada AS DATETIME) AS dat_entrada,
      COALESCE(SAFE_CAST(val_produtibilidadeespecifica AS FLOAT64), -1000.0) AS val_produtibilidadeespecifica,
      COALESCE(SAFE_CAST(val_latitude AS FLOAT64), -1000.0) AS val_latitude,
      COALESCE(SAFE_CAST(val_longitude AS FLOAT64), -1000.0) AS val_longitude,
      CURRENT_DATE() AS data_ingestao
    FROM
      `sauter-university-challenger.bronze.raw_reservatorio`
    WHERE 
      SAFE_CAST(val_produtibilidadeespecifica AS FLOAT64) IS NOT NULL
      AND CAST(val_produtibilidadeespecifica AS STRING) NOT IN ('NaN', 'nan', 'NAN', '')
      AND TRIM(CAST(val_produtibilidadeespecifica AS STRING)) != ''
    ORDER BY 
      nom_reservatorio ASC
  )

  SELECT * FROM dados_ordenados;


END;