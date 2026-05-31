from marshmallow import Schema, fields
from schema.accelerometer_schema import AccelerometerSchema
from schema.gps_schema import GpsSchema
from schema.parking_schema        import ParkingSchema
from schema.traffic_light_schema  import TrafficLightSchema

class AggregatedDataSchema(Schema):
    accelerometer = fields.Nested(AccelerometerSchema)
    gps = fields.Nested(GpsSchema)
    parking = fields.Nested(ParkingSchema)
    traffic_light = fields.Nested(TrafficLightSchema)
    timestamp = fields.DateTime('iso')