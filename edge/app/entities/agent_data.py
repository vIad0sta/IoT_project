from datetime import datetime
from pydantic import BaseModel, field_validator


class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    latitude: float
    longitude: float


class ParkingData(BaseModel):
    timestamp:   datetime
    gps:         GpsData

class TrafficLightData(BaseModel):
    state:          str    
    time_remaining: int
    timestamp:      datetime
    gps:            GpsData


class AgentData(BaseModel):
    accelerometer: AccelerometerData
    gps: GpsData
    parking: ParkingData
    traffic_light: TrafficLightData
    timestamp: datetime

    @classmethod
    @field_validator('timestamp', mode='before')
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."
            )