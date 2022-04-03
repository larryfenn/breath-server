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
  bme_temp REAL,
  bme_gas REAL,
  bme_hum REAL,
  bme_pressure REAL,
  bme_altitude REAL,
  pm10_std INT,
  pm25_std INT,
  pm100_std INT,
  pm10_env INT,
  pm25_env INT,
  pm100_env INT,
  03um INT,
  05um INT,
  10um INT,
  25um INT,
  50um INT,
  100um INT
);

INSERT INTO state (override, relay_state)
VALUES(0, 0)
