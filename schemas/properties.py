from marshmallow import EXCLUDE, Schema, fields, validate

from models import UNIT_TYPES
from schemas.auth import OwnerSchema
from schemas.cities import CitySchema
from schemas.units import UnitSchema


class PropertySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    description = fields.Str()
    area = fields.Str(validate=validate.Length(max=100))
    address = fields.Str(validate=validate.Length(max=255))
    image_url = fields.Url()
    # load_only: sent when creating/editing, the full city object is returned instead.
    city_id = fields.Int(required=True, load_only=True)
    status = fields.Str(dump_only=True) # only an admin changes this
    created_at = fields.DateTime(dump_only=True)

    city = fields.Nested(CitySchema, dump_only=True)
    manager = fields.Nested(OwnerSchema, dump_only=True)
    units = fields.List(fields.Nested(UnitSchema), dump_only=True)


class PropertyBrowseSchema(Schema):
    """Query-string filters for GET /properties."""
    class Meta:
        unknown = EXCLUDE # ignore page / per_page

    city_id = fields.Int()
    city = fields.Str()
    area = fields.Str()
    unit_type = fields.Str(validate=validate.OneOf(UNIT_TYPES))
    min_price = fields.Float(validate=validate.Range(min=0))
    max_price = fields.Float(validate=validate.Range(min=0))


property_schema = PropertySchema()
property_browse_schema = PropertyBrowseSchema()