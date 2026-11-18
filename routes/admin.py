from decimal import Decimal

from flask import g, jsonify, request
from sqlalchemy import func

from app import app
from config import db
from helpers import error, load_or_400, paginate, roles_required
from models import Booking, City, Property, Unit, User
from schemas import (
    AdminUserUpdateSchema,
    PropertySchema,
    PropertyStatusSchema,
    StatusFilterSchema,
    UserFilterSchema,
    UserSchema,
)

user_schema = UserSchema()
property_schema = PropertySchema()


@app.get("/api/admin/users")
@roles_required("admin")
def list_users():
    """List users with optional filters.
    ---
    tags:
      - Admin
    parameters:
      - in: query
        name: role
        type: string
        enum: [manager, customer, admin]
      - in: query
        name: is_approved
        type: boolean
      - in: query
        name: is_active
        type: boolean
      - in: query
        name: page
        type: integer
        minimum: 1
      - in: query
        name: per_page
        type: integer
        minimum: 1
        maximum: 50
    responses:
      200:
        description: Paginated users.
      401:
        description: Authentication required.
      403:
        description: Admin access required.
    """
    f = load_or_400(UserFilterSchema(), request.args.to_dict())
    query = User.query
    for field in ("role", "is_approved", "is_active"):
        if field in f:
            query = query.filter(getattr(User, field) == f[field])
    query = query.order_by(User.created_at.desc())
    return jsonify(paginate(query, user_schema, f["page"], f["per_page"]))


@app.patch("/api/admin/users/<int:user_id>")
@roles_required("admin")
def update_user(user_id):
    """Approve or block a user.
    ---
    tags:
      - Admin
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
      - in: body
        name: body
        schema:
          type: object
          properties:
            is_approved: {type: boolean}
            is_active: {type: boolean}
    responses:
      200:
        description: Updated user.
      400:
        description: Invalid update.
      404:
        description: User not found.
    """
    user = db.get_or_404(User, user_id)
    data = load_or_400(AdminUserUpdateSchema(), request.get_json(silent=True))
    if user.id == g.current_user.id and data.get("is_active") is False:
        return error("You cannot block your own account", 400)
    for key, value in data.items():
        setattr(user, key, value)
    db.session.commit()
    return jsonify(user_schema.dump(user))


@app.delete("/api/admin/users/<int:user_id>")
@roles_required("admin")
def delete_user(user_id):
    """Permanently delete a manager or customer and their related records.
    ---
    tags:
      - Admin
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
    responses:
      204:
        description: User and related records deleted.
      400:
        description: Admin accounts cannot be deleted with this endpoint.
      403:
        description: Admin access required.
      404:
        description: User not found.
    """
    user = db.get_or_404(User, user_id)
    if user.role not in ("manager", "customer"):
        return error("Only manager and customer accounts can be deleted", 400)
    db.session.delete(user)
    db.session.commit()
    return "", 204


@app.get("/api/admin/properties")
@roles_required("admin")
def list_all_properties():
    """List properties in every status.
    ---
    tags:
      - Admin
    parameters:
      - in: query
        name: status
        type: string
        enum: [pending, approved, rejected]
      - in: query
        name: page
        type: integer
        minimum: 1
      - in: query
        name: per_page
        type: integer
        minimum: 1
        maximum: 50
    responses:
      200:
        description: Paginated properties.
    """
    f = load_or_400(StatusFilterSchema(), request.args.to_dict())
    query = Property.query
    if f.get("status"):
        query = query.filter(Property.status == f["status"])
    query = query.order_by(Property.created_at.desc())
    return jsonify(paginate(query, property_schema, f["page"], f["per_page"]))


@app.patch("/api/admin/properties/<int:property_id>/status")
@roles_required("admin")
def set_property_status(property_id):
    """Approve or reject a property.
    ---
    tags:
      - Admin
    parameters:
      - in: path
        name: property_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [status]
          properties:
            status: {type: string, enum: [pending, approved, rejected]}
    responses:
      200:
        description: Updated property.
      400:
        description: Invalid status.
      404:
        description: Property not found.
    """
    prop = db.get_or_404(Property, property_id)
    prop.status = load_or_400(PropertyStatusSchema(), request.get_json(silent=True))["status"]
    db.session.commit()
    return jsonify(property_schema.dump(prop))


@app.get("/api/admin/stats")
@roles_required("admin")
def stats():
    """Return administrative platform statistics.
    ---
    tags:
      - Admin
    responses:
      200:
        description: User, listing, booking, and revenue statistics.
    """
    revenue = (
        db.session.query(func.coalesce(func.sum(Booking.total_price), 0))
        .filter(Booking.status.in_(("confirmed", "completed")))
        .scalar()
    )
    return jsonify(
        {
            "users": {
                "managers": User.query.filter_by(role="manager").count(),
                "pending_managers": User.query.filter_by(role="manager", is_approved=False).count(),
                "customers": User.query.filter_by(role="customer").count(),
            },
            "cities": City.query.count(),
            "properties": {
                "total": Property.query.count(),
                "pending": Property.query.filter_by(status="pending").count(),
                "approved": Property.query.filter_by(status="approved").count(),
                "rejected": Property.query.filter_by(status="rejected").count(),
            },
            "units": Unit.query.count(),
            "bookings": {
                "total": Booking.query.count(),
                "pending": Booking.query.filter_by(status="pending").count(),
                "confirmed": Booking.query.filter_by(status="confirmed").count(),
                "cancelled": Booking.query.filter_by(status="cancelled").count(),
                "completed": Booking.query.filter_by(status="completed").count(),
            },
            "revenue": str(Decimal(revenue).quantize(Decimal("0.01"))),
        }
    )