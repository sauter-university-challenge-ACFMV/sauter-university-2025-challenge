-- External table 
CREATE OR REPLACE EXTERNAL TABLE `sauter-university-challenger.bronze.raw_reservatorio`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://sauter-university-challenger-dev-raw/reservatorio/*']
);