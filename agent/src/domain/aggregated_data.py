from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.parking import Parking
from domain.traffic_light import TrafficLight

class AggregatedData:
    def __init__(
        self,
        accelerometer: Accelerometer,
        gps: Gps,
        parking: Parking,
        traffic_light: TrafficLight,
        timestamp: datetime,
    ):
        self.accelerometer = accelerometer
        self.gps           = gps
        self.parking       = parking
        self.traffic_light = traffic_light
        self.timestamp     = timestamp
