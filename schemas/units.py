from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates_schema

from models import UNIT_TYPES
from schemas.auth import OwnerSchema
from schemas.cities import CitySchema


class UnitSchema(Schema):
    id = fields.Int(dump_only=True)
    property_id = fields.Int(dump_only=True)
    unit_type = fields.Str(required=True, validate=validate.OneOf(UNIT_TYPES))
    price_per_month = fields.Float(required=True, validate=validate.Range(min=0))
    bathrooms = fields.Int(validate=validate.Range(min=0))
    amenities = fields.Str(validate=validate.Length(max=500))
    image_url = fields.Url()
    total_units = fields.Int(validate=validate.Range(min=1))
    available_units = fields.Int(validate=validate.Range(min=0))

    @validates_schema
    def check_availability(self, data, **kwargs):
        total, available = data.get("total_units"), data.get("available_units")
        if total is not None and available is not None and available > total:
            raise ValidationError(
                "available_units cannot exceed total_units.", "available_units"
            )


class PropertySummarySchema(Schema):
    id = fields.Int()
    name = fields.Str()
    area = fields.Str()
    city = fields.Nested(CitySchema)
    manager = fields.Nested(OwnerSchema)


class UnitListSchema(UnitSchema):
    """A unit plus a short summary of its property (used when comparing prices)."""
    property = fields.Nested(PropertySummarySchema, dump_only=True)


class UnitBrowseSchema(Schema):
    """Query-string filters for GET /units."""
    class Meta:
        unknown = EXCLUDE  # ignore page / per_page

    city_id = fields.Int()
    city = fields.Str()
    area = fields.Str()
    unit_type = fields.Str(validate=validate.OneOf(UNIT_TYPES))
    min_price = fields.Float(validate=validate.Range(min=0))
    max_price = fields.Float(validate=validate.Range(min=0))
    sort = fields.Str(
        load_default="newest", validate=validate.OneOf(["newest", "price_asc", "price_desc"])
    )


unit_schema = UnitSchema()
unit_list_schema = UnitListSchema()
unit_browse_schema = UnitBrowseSchema()