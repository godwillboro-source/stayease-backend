from marshmallow import Schema, fields, validate

from models import PROPERTY_STATUSES


class AdminUserUpdateSchema(Schema):
    """Approve a manager, or block / unblock a user."""
    is_approved = fields.Bool()
    is_active = fields.Bool()


class PropertyStatusSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(PROPERTY_STATUSES))


admin_user_schema = AdminUserUpdateSchema()
property_status_schema = PropertyStatusSchema()