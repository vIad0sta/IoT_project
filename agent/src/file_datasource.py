from csv import reader
from datetime import datetime
from domain.aggregated_data import AggregatedData, Accelerometer, Gps

class FileDatasource:
    def __init__(self, accelerometer_filename: str, gps_filename: str) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        
        self._accel_file = None
        self._gps_file = None
        self._accel_reader = None
        self._gps_reader = None

    def startReading(self, *args, **kwargs):
        self._accel_file = open(self.accelerometer_filename, 'r')
        self._gps_file = open(self.gps_filename, 'r')
        
        self._accel_reader = reader(self._accel_file)
        self._gps_reader = reader(self._gps_file)
        
        next(self._accel_reader)
        next(self._gps_reader)

    def read(self) -> AggregatedData:
        try:
            accel_row = next(self._accel_reader)
            gps_row = next(self._gps_reader)
        except StopIteration:
            self.stopReading()
            self.startReading()
            
            accel_row = next(self._accel_reader)
            gps_row = next(self._gps_reader)

        accel_data = Accelerometer(
            x=int(accel_row[0]),
            y=int(accel_row[1]),
            z=int(accel_row[2])
        )

        gps_data = Gps(
            latitude=float(gps_row[0]),
            longitude=float(gps_row[1])
        )

        return AggregatedData(
            accelerometer=accel_data,
            gps=gps_data,
            timestamp=datetime.now()
        )

    def stopReading(self, *args, **kwargs):
        if self._accel_file:
            self._accel_file.close()
        if self._gps_file:
            self._gps_file.close()