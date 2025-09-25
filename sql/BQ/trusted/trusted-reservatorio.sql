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