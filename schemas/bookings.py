from marshmallow import Schema, ValidationError, fields, validate, validates_schema
from models import BOOKING_STATUSES
from schemas.auth import OwnerSchema
from schemas.units import UnitListSchema