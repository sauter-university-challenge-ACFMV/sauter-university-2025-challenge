-- External table
CREATE OR REPLACE EXTERNAL TABLE `sauter-university-challenger.bronze.raw_ena-diario-por-reservatorio`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://sauter-university-challenger-dev-raw/ena-diario-por-reservatorio/*']
);