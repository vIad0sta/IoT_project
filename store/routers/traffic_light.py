from typing import List

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import SQLAlchemyError

from database import engine, traffic_light_data
from models import AgentData, TrafficLightDataInDB

router = APIRouter(prefix="/traffic_light_data", tags=["traffic_light"])


@router.post("/", response_model=List[TrafficLightDataInDB])
async def create_traffic_light_data(data: List[AgentData]):
    values_to_insert = [
        {
            "state":          item.traffic_light.state,
            "time_remaining": item.traffic_light.time_remaining,
            "latitude":       item.traffic_light.gps.latitude,
            "longitude":      item.traffic_light.gps.longitude,
            "timestamp":      item.traffic_light.timestamp,
        }
        for item in data
    ]
    if not values_to_insert:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                insert(traffic_light_data).values(values_to_insert).returning(traffic_light_data)
            ).mappings().all()
            conn.commit()
            return [TrafficLightDataInDB(**r) for r in rows]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/latest/", response_model=List[TrafficLightDataInDB])
def latest_traffic_light_data():
    with engine.connect() as conn:
        stmt = (
            select(traffic_light_data)
            .distinct(traffic_light_data.c.sensor_id)
            .order_by(traffic_light_data.c.sensor_id, traffic_light_data.c.id.desc())
        )
        results = conn.execute(stmt).mappings().all()
        return [TrafficLightDataInDB(**r) for r in results]


@router.get("/{traffic_light_data_id}", response_model=TrafficLightDataInDB)
def read_traffic_light_data(traffic_light_data_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(traffic_light_data).where(traffic_light_data.c.id == traffic_light_data_id)
        ).mappings().first()
        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")
        return TrafficLightDataInDB(**result)


@router.get("/", response_model=List[TrafficLightDataInDB])
def list_traffic_light_data(offset: int = 0, limit: int = 10):
    with engine.connect() as conn:
        results = conn.execute(
            select(traffic_light_data).offset(offset).limit(limit)
        ).mappings().all()
        return [TrafficLightDataInDB(**r) for r in results]


@router.put("/{traffic_light_data_id}", response_model=TrafficLightDataInDB)
def update_traffic_light_data(traffic_light_data_id: int, data: AgentData):
    with engine.connect() as conn:
        if not conn.execute(
            select(traffic_light_data).where(traffic_light_data.c.id == traffic_light_data_id)
        ).first():
            raise HTTPException(status_code=404, detail="Data not found")

        result = conn.execute(
            update(traffic_light_data)
            .where(traffic_light_data.c.id == traffic_light_data_id)
            .values(
                state=data.traffic_light.state,
                time_remaining=data.traffic_light.time_remaining,
                latitude=data.traffic_light.gps.latitude,
                longitude=data.traffic_light.gps.longitude,
                timestamp=data.traffic_light.timestamp,
            )
            .returning(traffic_light_data)
        ).mappings().first()
        conn.commit()
        return TrafficLightDataInDB(**result)


@router.delete("/{traffic_light_data_id}", response_model=TrafficLightDataInDB)
def delete_traffic_light_data(traffic_light_data_id: int):
    with engine.connect() as conn:
        existing = conn.execute(
            select(traffic_light_data).where(traffic_light_data.c.id == traffic_light_data_id)
        ).mappings().first()
        if not existing:
            raise HTTPException(status_code=404, detail="Data not found")

        conn.execute(
            delete(traffic_light_data).where(traffic_light_data.c.id == traffic_light_data_id)
        )
        conn.commit()
        return TrafficLightDataInDB(**existing)