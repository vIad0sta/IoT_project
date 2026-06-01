from datetime import datetime
from typing import Optional

from pydantic import BaseModel



class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    latitude: float
    longitude: float

class ParkingData(BaseModel):
    timestamp: datetime
    gps: GpsData


class TrafficLightData(BaseModel):
    state:          str
    time_remaining: int
    timestamp:      datetime
    gps:            GpsData


class AgentData(BaseModel):
    accelerometer: AccelerometerData
    gps: GpsData
    parking: Optional[ParkingData]      = None
    traffic_light: Optional[TrafficLightData] = None
    timestamp: datetime


class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData



class RoadStateInDB(BaseModel):
    id: int
    road_state: str
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime


class ParkingDataInDB(BaseModel):
    timestamp: datetime
    latitude: float
    longitude: float


class TrafficLightDataInDB(BaseModel):
    state: str
    time_remaining: int
    timestamp: datetime
    latitude: float
    longitude: float


class ProcessedAgentDataWithSensorsInDB(BaseModel):
    id: int
    road_state: str
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime
    parking: Optional[ParkingDataInDB] = None
    traffic_light: Optional[TrafficLightDataInDB] = None