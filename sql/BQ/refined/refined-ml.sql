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
    `sauter-university-challenger.silver.ena-diario-por-reservatorio` ena
INNER JOIN
    `sauter-university-challenger.silver.reservatorio` res
    ON ena.nom_reservatorio = res.nom_reservatorio;