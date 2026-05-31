from domain.gps import Gps
from datetime import datetime

class Parking:
    def __init__(self, timestamp: datetime, gps: Gps):
        self.timestamp = timestamp
        self.gps = gps