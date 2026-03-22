import json
from datetime import datetime
from typing import Set, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, Float, Integer, String, DateTime, MetaData, Table, create_engine, delete, insert, select, update
from sqlalchemy.exc import SQLAlchemyError

from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB

# SQLAlchemy setup
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)

# FastAPI models
class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float

class GpsData(BaseModel):
    latitude: float
    longitude: float

class AgentData(BaseModel):
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

@classmethod
@field_validator('timestamp', mode='before')
def check_timestamp(cls, value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("Invalid timestamp format. Expected ISO 8601 format(YYYY-MM-DDTHH:MM:SSZ).")

class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData

# Database model
class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime

# FastAPI app setup
app = FastAPI()

# WebSocket subscriptions
subscriptions: Set[WebSocket] = set()

# FastAPI WebSocket endpoint
@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    subscriptions.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions.remove(websocket)

# Function to send data to subscribed users
async def send_data_to_subscribers(data):
    for websocket in subscriptions:
        await websocket.send_json(json.dumps(data))


# FastAPI CRUDL endpoints
@app.post("/processed_agent_data/", response_model=List[ProcessedAgentDataInDB])
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    """
    Приймає список вкладених об'єктів, розгортає їх у плоску структуру,
    зберігає в БД та повідомляє WebSocket клієнтів.
    """
    values_to_insert = []
    
    # Мапінг вкладеної структури Pydantic у плоску структуру БД
    for item in data:
        row = {
            "road_state": item.road_state,
            "x": item.agent_data.accelerometer.x,
            "y": item.agent_data.accelerometer.y,
            "z": item.agent_data.accelerometer.z,
            "latitude": item.agent_data.gps.latitude,
            "longitude": item.agent_data.gps.longitude,
            "timestamp": item.agent_data.timestamp,
        }
        values_to_insert.append(row)

    if not values_to_insert:
        return []

    try:
        with engine.connect() as connection:
            # Використовуємо returning, щоб отримати ID створених записів
            stmt = insert(processed_agent_data).values(values_to_insert).returning(processed_agent_data)
            result = connection.execute(stmt)
            inserted_rows = result.mappings().all()
            connection.commit()
            
            # Перетворення результату SQLAlchemy RowMapping у Pydantic моделі
            response_data = [ProcessedAgentDataInDB(**row) for row in inserted_rows]
            
            # Відправка даних у WebSocket (асинхронно конвертуємо у dict для JSON)
            await send_data_to_subscribers([row.model_dump() for row in response_data])
            
            return response_data
            
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int):
    """Отримання одного запису за ID"""
    with engine.connect() as connection:
        stmt = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        result = connection.execute(stmt).mappings().first()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")
            
        return ProcessedAgentDataInDB(**result)


@app.get("/processed_agent_data/", response_model=List[ProcessedAgentDataInDB])
def list_processed_agent_data(offset: int = 0, limit: int = 10):
    """Отримання списку записів з пагінацією"""
    with engine.connect() as connection:
        stmt = select(processed_agent_data).offset(offset).limit(limit)
        results = connection.execute(stmt).mappings().all()
        
        return [ProcessedAgentDataInDB(**row) for row in results]


@app.put("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData):
    """Оновлення запису. Також вимагає мапінгу з вкладеної структури."""
    with engine.connect() as connection:
        # Перевірка існування
        stmt_check = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        if not connection.execute(stmt_check).first():
            raise HTTPException(status_code=404, detail="Data not found")

        # Підготовка даних для оновлення
        update_values = {
            "road_state": data.road_state,
            "x": data.agent_data.accelerometer.x,
            "y": data.agent_data.accelerometer.y,
            "z": data.agent_data.accelerometer.z,
            "latitude": data.agent_data.gps.latitude,
            "longitude": data.agent_data.gps.longitude,
            "timestamp": data.agent_data.timestamp,
        }

        stmt = (
            update(processed_agent_data)
            .where(processed_agent_data.c.id == processed_agent_data_id)
            .values(**update_values)
            .returning(processed_agent_data)
        )
        
        result = connection.execute(stmt).mappings().first()
        connection.commit()
        
        return ProcessedAgentDataInDB(**result)


@app.delete("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def delete_processed_agent_data(processed_agent_data_id: int):
    """Видалення запису"""
    with engine.connect() as connection:
        # Спочатку отримуємо дані, щоб повернути їх після видалення (як це прийнято в REST іноді, або просто підтвердження)
        stmt_get = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        existing_data = connection.execute(stmt_get).mappings().first()
        
        if not existing_data:
            raise HTTPException(status_code=404, detail="Data not found")
            
        stmt_delete = delete(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        connection.execute(stmt_delete)
        connection.commit()
        
        return ProcessedAgentDataInDB(**existing_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)