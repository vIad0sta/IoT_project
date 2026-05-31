from schema.gps_schema import GpsSchema
from marshmallow import Schema, fields

class TrafficLightSchema(Schema):
    sensor_id = fields.String(required=True)
    state = fields.String(required=True)
    time_remaining = fields.Integer(required=True)
    timestamp = fields.DateTime(required=True)
    gps = fields.Nested(GpsSchema, required=True)