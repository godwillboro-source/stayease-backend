
from flask import g, jsonify, request, session

from app import app
from config import db
from helpers import error, load_or_400, paginate, roles_required
from models import City, Property, Unit, User
from schemas import BrowseQuerySchema, PageSchema, PropertySchema

property_schema = PropertySchema()


def apply_property_filters(query, f):
    """Shared filters for browsing properties (city, area, unit type, price range)."""
    if f.get("city_id"):
        query = query.filter(Property.city_id == f["city_id"])
    if f.get("city"):
        query = query.join(City).filter(City.name.ilike(f"%{f['city']}%"))
    if f.get("area"):
        query = query.filter(Property.area.ilike(f"%{f['area']}%"))

    unit_conditions = []
    if f.get("unit_type"):
        unit_conditions.append(Unit.unit_type == f["unit_type"])
    if f.get("min_price") is not None:
        unit_conditions.append(Unit.price_per_month >= f["min_price"])
    if f.get("max_price") is not None:
        unit_conditions.append(Unit.price_per_month <= f["max_price"])
    if unit_conditions:
        query = query.filter(Property.units.any(db.and_(*unit_conditions)))
    return query


@app.get("/api/properties")
def browse_properties():
    """Browse approved properties.
    ---
    tags:
      - Properties
    parameters:
      - in: query
        name: city_id
        type: integer
      - in: query
        name: city
        type: string
      - in: query
        name: area
        type: string
      - in: query
        name: unit_type
        type: string
      - in: query
        name: min_price
        type: number
        format: decimal
      - in: query
        name: max_price
        type: number
        format: decimal
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
        description: Paginated properties with their units.
      400:
        description: Invalid filter.
    """
    f = load_or_400(BrowseQuerySchema(), request.args.to_dict())
    query = Property.query.filter(Property.status == "approved")
    query = apply_property_filters(query, f).order_by(Property.created_at.desc())
    return jsonify(paginate(query, property_schema, f["page"], f["per_page"]))


@app.get("/api/properties/mine")
@roles_required("manager")
def my_properties():
    """List the current manager's properties.
    ---
    tags:
      - Properties
    parameters:
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
    f = load_or_400(PageSchema(), request.args.to_dict())
    query = Property.query.filter_by(manager_id=g.current_user.id).order_by(Property.created_at.desc())
    return jsonify(paginate(query, property_schema, f["page"], f["per_page"]))


@app.get("/api/properties/<int:property_id>")
def get_property(property_id):
    """Get an approved property or one visible to its manager or an admin.
    ---
    tags:
      - Properties
    parameters:
      - in: path
        name: property_id
        required: true
        type: integer
    responses:
      200:
        description: Property details.
      404:
        description: Property not found.
    """
    prop = db.get_or_404(Property, property_id)
    if prop.status != "approved":
        # unapproved listings are only visible to their manager or an admin
        user_id = session.get("user_id")
        viewer = db.session.get(User, user_id) if user_id is not None else None
        allowed = viewer and viewer.is_active and (
            viewer.role == "admin" or viewer.id == prop.manager_id
        )
        if not allowed:
            return error("Property not found", 404)
    return jsonify(property_schema.dump(prop))


@app.post("/api/properties")
@roles_required("manager", approved_only=True)
def create_property():
    """Create a property listing.
    ---
    tags:
      - Properties
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [city_id, name]
          properties:
            city_id: {type: integer}
            name: {type: string}
            description: {type: string}
            area: {type: string}
            address: {type: string}
            image_url: {type: string, format: url}
    responses:
      201:
        description: Property created with pending status.
      400:
        description: Invalid property data.
      404:
        description: City not found.
    """
    data = load_or_400(property_schema, request.get_json(silent=True))
    if not db.session.get(City, data["city_id"]):
        return error("City does not exist", 404)
    prop = Property(manager_id=g.current_user.id, status="pending", **data)
    db.session.add(prop)
    db.session.commit()
    return jsonify(property_schema.dump(prop)), 201


@app.patch("/api/properties/<int:property_id>")
@roles_required("manager", approved_only=True)
def update_property(property_id):
    """Update a property owned by the current manager.
    ---
    tags:
      - Properties
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
          properties:
            city_id: {type: integer}
            name: {type: string}
            description: {type: string}
            area: {type: string}
            address: {type: string}
            image_url: {type: string, format: url}
    responses:
      200:
        description: Updated property.
      400:
        description: Invalid property data.
      403:
        description: Property is owned by another manager.
      404:
        description: Property or city not found.
    """
    prop = db.get_or_404(Property, property_id)
    if prop.manager_id != g.current_user.id:
        return error("You can only edit your own properties", 403)
    data = load_or_400(property_schema, request.get_json(silent=True), partial=True)
    if "city_id" in data and not db.session.get(City, data["city_id"]):
        return error("City does not exist", 404)
    for key, value in data.items():
        setattr(prop, key, value)
    db.session.commit()
    return jsonify(property_schema.dump(prop))


@app.delete("/api/properties/<int:property_id>")
@roles_required("manager", "admin")
def delete_property(property_id):
    """Delete a property.
    ---
    tags:
      - Properties
    parameters:
      - in: path
        name: property_id
        required: true
        type: integer
    responses:
      204:
        description: Property deleted.
      403:
        description: Property is owned by another manager.
      404:
        description: Property not found.
    """
    prop = db.get_or_404(Property, property_id)
    user = g.current_user
    if user.role == "manager" and prop.manager_id != user.id:
        return error("You can only delete your own properties", 403)
    db.session.delete(prop)
    db.session.commit()
    return "", 204