-- Primeiro, criar o dataset gold se não existir
CREATE SCHEMA IF NOT EXISTS `sauter-university-challenger.gold`;

-- Procedure para processar dados Silver para Gold
CREATE OR REPLACE PROCEDURE `sauter-university-challenger.procedure.process_silver_to_gold`()
BEGIN
  
 CREATE OR REPLACE MATERIALIZED VIEW `sauter-university-challenger.gold.dados_reservatorios_completo` AS
    SELECT
    ena.nom_reservatorio,
    ena.tip_reservatorio,
    ena.nom_bacia,
    ena.nom_subsistema,
    ena.ena_data,
    ena.ena_armazenavel_res_mwmed,
    res.dat_entrada,
    res.val_produtibilidadeespecifica,
    res.val_latitude,
    res.val_longitude,

    CONCAT(CAST(res.val_latitude AS STRING), ", ", CAST(res.val_longitude AS STRING)) AS coordenadas,
   
    -- Cálculo do volume do reservatório
    CASE
        WHEN res.val_produtibilidadeespecifica != 0
             AND res.val_produtibilidadeespecifica IS NOT NULL
        THEN ena.ena_armazenavel_res_mwmed / res.val_produtibilidadeespecifica
        ELSE NULL
    END AS volume_reservatorio
    FROM
        `sauter-university-challenger.silver.dados_ena_diarios` ena
    INNER JOIN
        `sauter-university-challenger.silver.dados_reservatorios_diarios` res
        ON ena.nom_reservatorio = res.nom_reservatorio;



    CREATE OR REPLACE MATERIALIZED VIEW `sauter-university-challenger.gold.dados_ML` AS
    SELECT
        ena.nom_reservatorio,
        ena.ena_data,

        -- Cálculo do volume do reservatório
        CASE
            WHEN res.val_produtibilidadeespecifica != 0
                AND res.val_produtibilidadeespecifica IS NOT NULL
            THEN ena.ena_armazenavel_res_mwmed / res.val_produtibilidadeespecifica
            ELSE NULL
        END AS volume_reservatorio
    FROM
        `sauter-university-challenger.silver.dados_ena_diarios` ena
    INNER JOIN
        `sauter-university-challenger.silver.dados_reservatorios_diarios` res
        ON ena.nom_reservatorio = res.nom_reservatorio;

END;

