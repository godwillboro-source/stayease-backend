from marshmallow import Schema, ValidationError, fields, validate, validates_schema
from models import BOOKING_STATUSES
from schemas.auth import OwnerSchema
from schemas.units import UnitListSchema

class BookingSchema(Schema):
    id = fields.Int(dump_only=True)
    unit_id = fields.Int(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    total_price = fields.Float(dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    unit = fields.Nested(UnitListSchema, dump_only=True)
    customer = fields.Nested(OwnerSchema, dump_only=True)
    @validates_schema
    def check_dates(self, data, **kwargs):
        if data["end_date"] <= data["start_date"]:
            raise ValidationError("end_date must be after start_date.", "end_date")


class BookingStatusSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(BOOKING_STATUSES))


booking_schema = BookingSchema()
status_schema = BookingStatusSchema()