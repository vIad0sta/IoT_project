from domain.gps import Gps
from datetime import datetime

class TrafficLight:
    def __init__(self, state: str, time_remaining: int, timestamp: datetime, gps: Gps):
        self.state = state              
        self.time_remaining = time_remaining 
        self.timestamp = timestamp     
        self.gps = gps