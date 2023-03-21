DROP TABLE IF EXISTS state;
DROP TABLE IF EXISTS air_quality_log;

CREATE TABLE state (
  time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  override INT,
  relay_state INT
 );

CREATE TABLE air_quality_log (
  time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  id TEXT,
  rco2 INT,
  pm02 INT,
  tvoc_index INT,
  nox_index INT,
  atmp REAL,
  rhum INT
);

INSERT INTO state (override, relay_state)
VALUES(0, 0)
