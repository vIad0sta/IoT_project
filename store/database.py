from sqlalchemy import (
    Column, DateTime, Float, Integer, MetaData, String, Table,
    create_engine,
)

from config import (
    POSTGRES_DB, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER,
)

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine   = create_engine(DATABASE_URL)
metadata = MetaData()

road_state_data = Table(
    "road_state_data", metadata,
    Column("id",         Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("x",          Float),
    Column("y",          Float),
    Column("z",          Float),
    Column("latitude",   Float),
    Column("longitude",  Float),
    Column("timestamp",  DateTime),
)

parking_data = Table(
    "parking_data", metadata,
    Column("id",        Integer, primary_key=True, index=True),
    Column("latitude",  Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)

traffic_light_data = Table(
    "traffic_light_data", metadata,
    Column("id",             Integer, primary_key=True, index=True),
    Column("state",          String),
    Column("time_remaining", Integer),
    Column("latitude",       Float),
    Column("longitude",      Float),
    Column("timestamp",      DateTime),
)