from typing import List, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import SQLAlchemyError

from database import engine, parking_data, road_state_data, traffic_light_data
from models import (
    ParkingDataInDB,
    ProcessedAgentData,
    ProcessedAgentDataWithSensorsInDB,
    RoadStateInDB,
    TrafficLightDataInDB,
)
from websocket_manager import send_data_to_subscribers

router = APIRouter(prefix="/processed_agent_data", tags=["processed_agent_data"])


def _find_exact_parking(conn, lat: float, lon: float) -> Optional[ParkingDataInDB]:
    """Повертає запис парковки, координати якої точно дорівнюють (lat, lon)."""
    stmt = (
        select(parking_data)
        .where(
            (parking_data.c.latitude == lat) &
            (parking_data.c.longitude == lon)
        )
        .limit(1)
    )
    result = conn.execute(stmt).mappings().first()
    return ParkingDataInDB(**result) if result else None


def _find_exact_traffic_light(conn, lat: float, lon: float) -> Optional[TrafficLightDataInDB]:
    """Повертає найновіший запис світлофора за координатами (lat, lon)."""
    stmt = (
        select(traffic_light_data)
        .where(
            (traffic_light_data.c.latitude == lat) &
            (traffic_light_data.c.longitude == lon)
        )
        .order_by(traffic_light_data.c.id.desc())
        .limit(1)
    )
    result = conn.execute(stmt).mappings().first()
    return TrafficLightDataInDB(**result) if result else None


def _enrich_with_sensors(conn, row: dict) -> ProcessedAgentDataWithSensorsInDB:
    """Доповнює рядок road_state даними парковки та світлофора за координатами."""
    lat = row["latitude"]
    lon = row["longitude"]
    return ProcessedAgentDataWithSensorsInDB(
        **row,
        parking=_find_exact_parking(conn, lat, lon),
        traffic_light=_find_exact_traffic_light(conn, lat, lon),
    )

@router.post("/", response_model=List[RoadStateInDB])
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    processed_values     = []
    parking_values       = []
    traffic_light_values = []

    for item in data:
        processed_values.append({
            "road_state": item.road_state,
            "x":          item.agent_data.accelerometer.x,
            "y":          item.agent_data.accelerometer.y,
            "z":          item.agent_data.accelerometer.z,
            "latitude":   item.agent_data.gps.latitude,
            "longitude":  item.agent_data.gps.longitude,
            "timestamp":  item.agent_data.timestamp,
        })

        if item.agent_data.parking:
            parking_values.append({
                "latitude":  item.agent_data.parking.gps.latitude,
                "longitude": item.agent_data.parking.gps.longitude,
                "timestamp": item.agent_data.parking.timestamp,
            })

        if item.agent_data.traffic_light:
            traffic_light_values.append({
                "state":          item.agent_data.traffic_light.state,
                "time_remaining": item.agent_data.traffic_light.time_remaining,
                "latitude":       item.agent_data.traffic_light.gps.latitude,
                "longitude":      item.agent_data.traffic_light.gps.longitude,
                "timestamp":      item.agent_data.traffic_light.timestamp,
            })

    if not processed_values:
        return []

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                insert(road_state_data).values(processed_values).returning(road_state_data)
            ).mappings().all()

            if parking_values:
                conn.execute(insert(parking_data).values(parking_values))
            if traffic_light_values:
                conn.execute(insert(traffic_light_data).values(traffic_light_values))

            conn.commit()

            response_data = [RoadStateInDB(**r) for r in rows]
            await send_data_to_subscribers([r.model_dump() for r in response_data])
            return response_data

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{processed_agent_data_id}", response_model=ProcessedAgentDataWithSensorsInDB)
def read_processed_agent_data(processed_agent_data_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            select(road_state_data).where(road_state_data.c.id == processed_agent_data_id)
        ).mappings().first()

        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")

        return _enrich_with_sensors(conn, dict(result))


@router.get("/", response_model=List[ProcessedAgentDataWithSensorsInDB])
def list_processed_agent_data(offset: int = 0, limit: int = 10):
    with engine.connect() as conn:
        results = conn.execute(
            select(road_state_data).offset(offset).limit(limit)
        ).mappings().all()
        return [_enrich_with_sensors(conn, dict(r)) for r in results]


@router.put("/{processed_agent_data_id}", response_model=ProcessedAgentDataWithSensorsInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData):
    with engine.connect() as conn:
        if not conn.execute(
            select(road_state_data).where(road_state_data.c.id == processed_agent_data_id)
        ).first():
            raise HTTPException(status_code=404, detail="Data not found")

        result = conn.execute(
            update(road_state_data)
            .where(road_state_data.c.id == processed_agent_data_id)
            .values(
                road_state=data.road_state,
                x=data.agent_data.accelerometer.x,
                y=data.agent_data.accelerometer.y,
                z=data.agent_data.accelerometer.z,
                latitude=data.agent_data.gps.latitude,
                longitude=data.agent_data.gps.longitude,
                timestamp=data.agent_data.timestamp,
            )
            .returning(road_state_data)
        ).mappings().first()

        if data.agent_data.parking is not None:
            p = data.agent_data.parking
            existing = conn.execute(
                select(parking_data).where(parking_data.c.id == p.id)
            ).mappings().first()

            if existing:
                conn.execute(
                    update(parking_data)
                    .where(parking_data.c.id == p.id)
                    .values(latitude=p.gps.latitude, longitude=p.gps.longitude, timestamp=p.timestamp)
                )
            else:
                conn.execute(
                    insert(parking_data)
                    .values(latitude=p.gps.latitude, longitude=p.gps.longitude, timestamp=p.timestamp)
                )

        if data.agent_data.traffic_light is not None:
            tl = data.agent_data.traffic_light
            existing = conn.execute(
                select(traffic_light_data).where(traffic_light_data.c.id == tl.id)
            ).mappings().first()

            if existing:
                conn.execute(
                    update(traffic_light_data)
                    .where(traffic_light_data.c.id == tl.id)
                    .values(
                        state=tl.state,
                        time_remaining=tl.time_remaining,
                        latitude=tl.gps.latitude,
                        longitude=tl.gps.longitude,
                        timestamp=tl.timestamp,
                    )
                )
            else:
                conn.execute(
                    insert(traffic_light_data)
                    .values(
                        state=tl.state,
                        time_remaining=tl.time_remaining,
                        latitude=tl.gps.latitude,
                        longitude=tl.gps.longitude,
                        timestamp=tl.timestamp,
                    )
                )

        conn.commit()
        return _enrich_with_sensors(conn, dict(result))


@router.delete("/{processed_agent_data_id}", response_model=RoadStateInDB)
def delete_processed_agent_data(processed_agent_data_id: int):
    with engine.connect() as conn:
        existing = conn.execute(
            select(road_state_data).where(road_state_data.c.id == processed_agent_data_id)
        ).mappings().first()
        if not existing:
            raise HTTPException(status_code=404, detail="Data not found")

        conn.execute(
            delete(road_state_data).where(road_state_data.c.id == processed_agent_data_id)
        )
        conn.commit()
        return RoadStateInDB(**existing)