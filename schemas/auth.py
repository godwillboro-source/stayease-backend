from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    email = fields.Email()
    phone = fields.Str()
    role = fields.Str()
    is_approved = fields.Bool()
    is_active = fields.Bool()
    created_at = fields.DateTime()


class OwnerSchema(Schema):
    """Small public view of a user (shown on properties and bookings)."""
    id = fields.Int()
    username = fields.Str()
    phone = fields.Str()


class SignupSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    phone = fields.Str(validate=validate.Length(max=20))
    # load_only: accepted on input, never returned.
    password = fields.Str(
        required=True, load_only=True, validate=validate.Length(min=8, max=128)
    )
    # Admins can't sign up through the API; the first admin comes from seed.py.
    role = fields.Str(required=True, validate=validate.OneOf(["manager", "customer"]))


user_schema = UserSchema()
signup_schema = SignupSchema()