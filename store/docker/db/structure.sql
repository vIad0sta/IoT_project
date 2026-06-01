CREATE TABLE road_state_data (
    id         SERIAL PRIMARY KEY,
    road_state VARCHAR(255) NOT NULL,
    x          FLOAT,
    y          FLOAT,
    z          FLOAT,
    latitude   FLOAT,
    longitude  FLOAT,
    timestamp  TIMESTAMP
);

CREATE TABLE parking_data (
    id          SERIAL PRIMARY KEY,
    timestamp   TIMESTAMP    NOT NULL,
    latitude    FLOAT        NOT NULL,
    longitude   FLOAT        NOT NULL,
);

CREATE TABLE traffic_light_data (
    id             SERIAL PRIMARY KEY,
    timestamp      TIMESTAMP    NOT NULL,
    latitude       FLOAT        NOT NULL,
    longitude      FLOAT        NOT NULL,
    state          VARCHAR(10)  NOT NULL CHECK (state IN ('red', 'yellow', 'green')),
    time_remaining INTEGER      NOT NULL
);
