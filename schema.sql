DROP TABLE IF EXISTS state;
DROP TABLE IF EXISTS air_quality_log;

CREATE TABLE state (
  time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  override INT,
  relay_state INT
 );

CREATE TABLE air_quality_log (
  time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  scd_co2 REAL,
  scd_temp REAL,
  scd_hum REAL,
  pm25_env INT,
  aq_25um INT
);

INSERT INTO state (override, relay_state)
VALUES(0, 0)
