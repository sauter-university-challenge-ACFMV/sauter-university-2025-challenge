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
    `sauter-university-challenger.silver.ena-diario-por-reservatorio` ena
INNER JOIN
    `sauter-university-challenger.silver.reservatorio` res
    ON ena.nom_reservatorio = res.nom_reservatorio;