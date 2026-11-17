from flask import jsonify, request

from app import app
from config import db
from helpers import error, load_or_400, roles_required
from models import City
from schemas import CitySchema

city_schema = CitySchema()


@app.get("/api/cities")
def list_cities():
    """List cities.
    ---
    tags:
      - Cities
    responses:
      200:
        description: Cities ordered by name.
    """
    cities = City.query.order_by(City.name).all()
    return jsonify(city_schema.dump(cities, many=True))


@app.post("/api/cities")
@roles_required("admin")
def create_city():
    """Create a city.
    ---
    tags:
      - Cities
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name]
          properties:
            name: {type: string}
    responses:
      201:
        description: City created.
      400:
        description: Invalid city data.
      409:
        description: City already exists.
    """
    data = load_or_400(city_schema, request.get_json(silent=True))
    name = data["name"].strip().title()
    if City.query.filter(db.func.lower(City.name) == name.lower()).first():
        return error("City already exists", 409)
    city = City(name=name)
    db.session.add(city)
    db.session.commit()
    return jsonify(city_schema.dump(city)), 201


@app.put("/api/cities/<int:city_id>")
@roles_required("admin")
def update_city(city_id):
    """Update a city.
    ---
    tags:
      - Cities
    parameters:
      - in: path
        name: city_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name]
          properties:
            name: {type: string}
    responses:
      200:
        description: Updated city.
      400:
        description: Invalid city data.
      404:
        description: City not found.
      409:
        description: Another city already uses that name.
    """
    city = db.get_or_404(City, city_id)
    data = load_or_400(city_schema, request.get_json(silent=True))
    name = data["name"].strip().title()
    clash = City.query.filter(db.func.lower(City.name) == name.lower(), City.id != city_id).first()
    if clash:
        return error("Another city already has that name", 409)
    city.name = name
    db.session.commit()
    return jsonify(city_schema.dump(city))


@app.delete("/api/cities/<int:city_id>")
@roles_required("admin")
def delete_city(city_id):
    """Delete a city with no properties.
    ---
    tags:
      - Cities
    parameters:
      - in: path
        name: city_id
        required: true
        type: integer
    responses:
      204:
        description: City deleted.
      404:
        description: City not found.
      409:
        description: City still has properties.
    """
    city = db.get_or_404(City, city_id)
    if city.properties:
        return error("Cannot delete a city that still has properties", 409)
    db.session.delete(city)
    db.session.commit()
    return "", 204