from schema.gps_schema import GpsSchema
from marshmallow import Schema, fields

class ParkingSchema(Schema):
    sensor_id = fields.String(required=True)
    timestamp = fields.DateTime(required=True)
    gps = fields.Nested(GpsSchema, required=True)