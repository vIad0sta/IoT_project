from csv import reader
from datetime import datetime
from domain.parking import Parking
from domain.traffic_light import TrafficLight
from domain.aggregated_data import AggregatedData, Accelerometer, Gps


class FileDatasource:
    def __init__(
        self,
        accelerometer_filename: str,
        gps_filename: str,
        parking_filename: str,
        traffic_light_filename: str,
    ) -> None:
        self.accelerometer_filename  = accelerometer_filename
        self.gps_filename            = gps_filename
        self.parking_filename        = parking_filename
        self.traffic_light_filename  = traffic_light_filename

        self._accel_file         = None
        self._gps_file           = None
        self._parking_file       = None
        self._traffic_light_file = None

        self._accel_reader         = None
        self._gps_reader           = None
        self._parking_reader       = None
        self._traffic_light_reader = None

    def _reopen(self, filename: str, file_attr: str, reader_attr: str):
        old_file = getattr(self, file_attr)
        if old_file:
            old_file.close()

        new_file   = open(filename, 'r')
        new_reader = reader(new_file)
        next(new_reader) 

        setattr(self, file_attr,   new_file)
        setattr(self, reader_attr, new_reader)

    
    def _next_row(self, reader_attr: str, filename: str, file_attr: str) -> list:
        try:
            return next(getattr(self, reader_attr))
        except StopIteration:
            self._reopen(filename, file_attr, reader_attr)
            return next(getattr(self, reader_attr))

    def startReading(self, *args, **kwargs):
        self._accel_file = open(self.accelerometer_filename,  'r')
        self._gps_file = open(self.gps_filename,            'r')
        self._parking_file = open(self.parking_filename,        'r')
        self._traffic_light_file = open(self.traffic_light_filename,  'r')

        self._accel_reader = reader(self._accel_file)
        self._gps_reader = reader(self._gps_file)
        self._parking_reader = reader(self._parking_file)
        self._traffic_light_reader = reader(self._traffic_light_file)

        next(self._accel_reader)
        next(self._gps_reader)
        next(self._parking_reader)
        next(self._traffic_light_reader)

    def read(self) -> AggregatedData:
        accel_row = self._next_row(
            '_accel_reader', self.accelerometer_filename, '_accel_file'
        )
        gps_row = self._next_row(
            '_gps_reader', self.gps_filename, '_gps_file'
        )
        parking_row = self._next_row(
            '_parking_reader', self.parking_filename, '_parking_file'
        )
        traffic_light_row = self._next_row(
            '_traffic_light_reader', self.traffic_light_filename, '_traffic_light_file'
        )

        accel_data = Accelerometer(
            x=int(accel_row[0]),
            y=int(accel_row[1]),
            z=int(accel_row[2]),
        )

        gps_data = Gps(
            latitude=float(gps_row[0]),
            longitude=float(gps_row[1]),
        )

        parking_data = Parking(
            timestamp=datetime.now(),
            gps=Gps(
                latitude=float(parking_row[2]),
                longitude=float(parking_row[3]),
            )
        )

        traffic_light_data = TrafficLight(
            timestamp=datetime.now(),
            gps=Gps(
                latitude=float(traffic_light_row[2]),
                longitude=float(traffic_light_row[3]),
            ),
            state=str(traffic_light_row[4]),
            time_remaining=int(traffic_light_row[5]),
        )

        return AggregatedData(
            accelerometer=accel_data,
            gps=gps_data,
            parking=parking_data,
            traffic_light=traffic_light_data,
            timestamp=datetime.now(),
        )

    def stopReading(self, *args, **kwargs):
        for f in (
            self._accel_file,
            self._gps_file,
            self._parking_file,
            self._traffic_light_file,
        ):
            if f:
                f.close()