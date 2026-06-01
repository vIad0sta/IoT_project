from typing import List

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import SQLAlchemyError

from database import engine, parking_data
from models import AgentData, ParkingDataInDB

router = APIRouter(prefix="/parking_data", tags=["parking"])


@router.post("/", response_model=List[ParkingDataInDB])
async def create_parking_data(data: List[AgentData]):
    values_to_insert = [
        {
            "latitude":  item.parking.gps.latitude,
            "longitude": item.parking.gps.longitude,
            "timestamp": item.parking.timestamp,
        }
        for item in data
    ]
    if not values_to_insert:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                insert(parking_data).values(values_to_insert).returning(parking_data)
            ).mappings().all()
            conn.commit()
            return [ParkingDataInDB(**r) for r in rows]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/latest/", response_model=List[ParkingDataInDB])
def latest_parking_data():
    with engine.connect() as conn:
        stmt = (
            select(parking_data)
            .distinct(parking_data.c.sensor_id)
            .order_by(parking_data.c.sensor_id, parking_data.c.id.desc())
        )
        results = conn.execute(stmt).mappings().all()
        return [ParkingDataInDB(**r) for r in results]


@router.get("/{parking_data_id}", response_model=ParkingDataInDB)
def read_parking_data(parking_data_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(parking_data).where(parking_data.c.id == parking_data_id)
        ).mappings().first()
        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")
        return ParkingDataInDB(**result)


@router.get("/", response_model=List[ParkingDataInDB])
def list_parking_data(offset: int = 0, limit: int = 10):
    with engine.connect() as conn:
        results = conn.execute(
            select(parking_data).offset(offset).limit(limit)
        ).mappings().all()
        return [ParkingDataInDB(**r) for r in results]


@router.put("/{parking_data_id}", response_model=ParkingDataInDB)
def update_parking_data(parking_data_id: int, data: AgentData):
    with engine.connect() as conn:
        if not conn.execute(
            select(parking_data).where(parking_data.c.id == parking_data_id)
        ).first():
            raise HTTPException(status_code=404, detail="Data not found")

        result = conn.execute(
            update(parking_data)
            .where(parking_data.c.id == parking_data_id)
            .values(
                latitude=data.parking.gps.latitude,
                longitude=data.parking.gps.longitude,
                timestamp=data.parking.timestamp,
            )
            .returning(parking_data)
        ).mappings().first()
        conn.commit()
        return ParkingDataInDB(**result)


@router.delete("/{parking_data_id}", response_model=ParkingDataInDB)
def delete_parking_data(parking_data_id: int):
    with engine.connect() as conn:
        existing = conn.execute(
            select(parking_data).where(parking_data.c.id == parking_data_id)
        ).mappings().first()
        if not existing:
            raise HTTPException(status_code=404, detail="Data not found")

        conn.execute(delete(parking_data).where(parking_data.c.id == parking_data_id))
        conn.commit()
        return ParkingDataInDB(**existing)